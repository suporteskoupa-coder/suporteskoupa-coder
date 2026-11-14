import subprocess
from functools import lru_cache
from pathlib import Path

from .config import Config
from .probe import MediaInfo

TONEMAP = ("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,"
           "tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p")


def _try_encoder(name: str) -> bool:
    """Tenta codificar 1 frame: só listar em `ffmpeg -encoders` não garante GPU."""
    r = subprocess.run(
        ["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=black:s=256x256:d=0.1",
         "-frames:v", "1", "-c:v", name, "-f", "null", "-"],
        capture_output=True,
    )
    return r.returncode == 0


@lru_cache(maxsize=1)
def pick_encoder() -> str:
    return "hevc_nvenc" if _try_encoder("hevc_nvenc") else "libx264"


def video_args(encoder: str, height: int, fps: int) -> list[str]:
    if encoder == "hevc_nvenc":
        v = ["-c:v", "hevc_nvenc", "-preset", "p5", "-rc", "vbr", "-cq", "19",
             "-b:v", "0", "-tag:v", "hvc1"]
    else:
        v = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18"]
    return v + ["-pix_fmt", "yuv420p", "-r", str(fps),
                "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart"]


def target_height(info: MediaInfo, cfg: Config) -> int:
    return min(info.height, cfg.long_max_height)


def normalize(src: Path, dst: Path, info: MediaInfo, cfg: Config) -> Path:
    vf = []
    if info.is_hdr:
        vf.append(TONEMAP)
    h = target_height(info, cfg)
    if h != info.height:
        vf.append(f"scale=-2:{h}")
    vf.append(f"fps={cfg.fps}")
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(src), "-vf", ",".join(vf)]
    if info.has_audio:
        cmd += ["-af", "aresample=async=1"]
    cmd += video_args(pick_encoder(), h, cfg.fps) + [str(dst)]
    subprocess.run(cmd, check=True)
    return dst
