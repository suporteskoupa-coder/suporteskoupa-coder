import subprocess
import tempfile
from pathlib import Path

from .analyze import Peak
from .config import Config
from .encode import pick_encoder, video_args
from .probe import probe


def pick_short_windows(peaks: list[Peak], duration: float, n: int, length_s: float,
                       lead_s: float = 3.0) -> list[tuple[float, float]]:
    windows: list[tuple[float, float]] = []
    if duration < length_s:
        return windows
    for p in sorted(peaks, key=lambda p: p.rms_db, reverse=True):
        start = max(0.0, p.t - lead_s)
        end = start + length_s
        if end > duration:
            end, start = duration, duration - length_s
        if all(end <= s or start >= e for s, e in windows):
            windows.append((start, end))
            if len(windows) == n:
                break
    return windows


def _filter_path(p: Path) -> str:
    """Caminho seguro dentro de um filtro do ffmpeg (Windows: C\\:/...)."""
    return p.resolve().as_posix().replace(":", r"\:").replace("'", r"\'")


def render_short(src: Path, window: tuple[float, float], dst: Path, cfg: Config,
                 text: str | None = None) -> Path:
    w, h = cfg.short_size
    start = window[0]
    dur = min(window[1] - window[0], cfg.short_max_s)
    graph = (f"[0:v]split[a][b];"
             f"[a]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},boxblur=20[bg];"
             f"[b]scale={w}:-2[fg];"
             f"[bg][fg]overlay=(W-w)/2:(H-h)/2,fps={cfg.fps}")
    tmp = None
    if text:
        tmp = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8")
        tmp.write(text)
        tmp.close()
        graph += (f",drawtext=fontfile='{_filter_path(cfg.resolve_font())}'"
                  f":textfile='{_filter_path(Path(tmp.name))}':expansion=none"
                  f":fontsize=72:fontcolor=white:borderw=6:bordercolor=black"
                  f":x=(w-text_w)/2:y=h*0.12")
    graph += "[outv]"
    cmd = ["ffmpeg", "-y", "-v", "error", "-ss", f"{start}", "-t", f"{dur}", "-i", str(src),
           "-filter_complex", graph, "-map", "[outv]"]
    if probe(src).has_audio:
        cmd += ["-map", "0:a"]
    cmd += video_args(pick_encoder(), h, cfg.fps) + [str(dst)]
    try:
        subprocess.run(cmd, check=True)
    finally:
        if tmp:
            Path(tmp.name).unlink(missing_ok=True)
    return dst
