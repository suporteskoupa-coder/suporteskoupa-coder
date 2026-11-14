import subprocess

import numpy as np
from PIL import Image

from canal import encode
from canal.config import Config
from canal.probe import probe


def test_pick_encoder_falls_back(monkeypatch):
    monkeypatch.setattr(encode, "_try_encoder", lambda name: False)
    encode.pick_encoder.cache_clear()
    assert encode.pick_encoder() == "libx264"
    encode.pick_encoder.cache_clear()


def test_pick_encoder_prefers_nvenc(monkeypatch):
    monkeypatch.setattr(encode, "_try_encoder", lambda name: name == "hevc_nvenc")
    encode.pick_encoder.cache_clear()
    assert encode.pick_encoder() == "hevc_nvenc"
    encode.pick_encoder.cache_clear()


def test_normalize_outputs_cfr_60(sample_video, tmp_path):
    src = sample_video(seconds=6, vfr=True)
    out = encode.normalize(src, tmp_path / "n.mp4", probe(src), Config())
    info = probe(out)
    assert round(info.fps) == 60 and not info.is_vfr
    a = float(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries",
                              "stream=duration", "-of", "csv=p=0", str(out)],
                             capture_output=True, text=True).stdout)
    assert abs(a - info.duration) < 0.1


def test_normalize_tonemaps_hdr(sample_video, tmp_path):
    src = sample_video(seconds=2, hdr=True)
    out = encode.normalize(src, tmp_path / "n.mp4", probe(src), Config())
    assert not probe(out).is_hdr
    frame = tmp_path / "f.png"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "1", "-i", str(out), "-frames:v", "1", str(frame)], check=True)
    mean = np.asarray(Image.open(frame).convert("L")).mean()
    assert 40 < mean < 215
