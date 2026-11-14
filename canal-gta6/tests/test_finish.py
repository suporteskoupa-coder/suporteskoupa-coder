import re
import subprocess

import numpy as np
from PIL import Image

from canal.config import Config
from canal.cut import render_long
from canal.shorts import render_short


def loudness(path) -> float:
    err = subprocess.run(["ffmpeg", "-nostats", "-i", str(path), "-af", "ebur128", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", err)[-1])


def frame(path, t, dst):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", str(path), "-frames:v", "1", str(dst)],
                   check=True)
    return np.asarray(Image.open(dst).convert("L"), dtype=np.float32)


def test_long_audio_normalized_to_youtube_level(sample_video, tmp_path):
    out = render_long(sample_video(seconds=12), [(0, 12)], tmp_path / "l.mp4", Config())
    assert abs(loudness(out) - (-14)) <= 2


def test_short_audio_normalized(sample_video, tmp_path):
    out = render_short(sample_video(seconds=12), (0, 12), tmp_path / "s.mp4", Config())
    assert abs(loudness(out) - (-14)) <= 2


def test_long_without_audio_still_renders(sample_video, tmp_path):
    out = render_long(sample_video(seconds=4, audio=False), [(0, 4)], tmp_path / "l.mp4", Config())
    assert out.exists()


def test_cinematic_letterbox_and_fades(sample_video, tmp_path):
    out = render_long(sample_video(seconds=8), [(0, 8)], tmp_path / "c.mp4", Config(cinematic=True))
    mid = frame(out, 4, tmp_path / "m.png")
    h = mid.shape[0]
    bar = int(h * (1 - (16 / 9) / 2.39) / 2)
    assert mid[: bar - 2].mean() < 5 and mid[h - bar + 2:].mean() < 5   # barras pretas
    assert mid[h // 2].mean() > 40                                        # imagem no meio
    assert frame(out, 0, tmp_path / "f.png").mean() < mid.mean() / 3      # fade-in


def test_default_has_no_letterbox(sample_video, tmp_path):
    out = render_long(sample_video(seconds=4), [(0, 4)], tmp_path / "n.mp4", Config())
    assert frame(out, 2, tmp_path / "m.png")[:5].mean() > 20
