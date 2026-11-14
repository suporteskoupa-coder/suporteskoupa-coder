import json
import subprocess
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

HDR_TRANSFERS = {"smpte2084", "arib-std-b67"}


@dataclass(frozen=True)
class MediaInfo:
    width: int
    height: int
    fps: float
    duration: float
    is_hdr: bool
    is_vfr: bool
    has_audio: bool


def _rate(s: str) -> Fraction:
    try:
        return Fraction(s)
    except (ValueError, ZeroDivisionError):
        return Fraction(0)


def probe(path: Path) -> MediaInfo:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        capture_output=True, text=True, encoding="utf-8", check=True,
    ).stdout
    data = json.loads(out)
    streams = data.get("streams", [])
    video = next(s for s in streams if s.get("codec_type") == "video")
    r = _rate(video.get("r_frame_rate", "0/1"))
    avg = _rate(video.get("avg_frame_rate", "0/1"))
    fps = float(avg or r)
    return MediaInfo(
        width=int(video["width"]),
        height=int(video["height"]),
        fps=fps,
        duration=float(data["format"].get("duration") or video.get("duration") or 0),
        is_hdr=video.get("color_transfer") in HDR_TRANSFERS,
        is_vfr=bool(r and avg and abs(float(r) - float(avg)) > 0.01),
        has_audio=any(s.get("codec_type") == "audio" for s in streams),
    )
