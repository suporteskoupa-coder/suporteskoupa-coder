import subprocess
from functools import lru_cache
from pathlib import Path

from .config import Config
from .probe import MediaInfo

LOUDNORM = "loudnorm=I=-14:TP=-1.5:LRA=11"  # nível de referência do YouTube

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
        # p4: no ensaio (4K60, RTX 3060) deu SSIM igual ao p5 (0,99063 x 0,99064) e 1,55x mais rápido
        v = ["-c:v", "hevc_nvenc", "-preset", "p4", "-rc", "vbr", "-cq", "19",
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


def cinematic_video(width: int, height: int, duration: float) -> str:
    """Cor levemente mais rica, barras pretas 2.39:1 dentro do quadro e fades de 1 s."""
    bar = max(0.0, (1 - (width / height) / 2.39) / 2)
    out = max(0.0, duration - 1)
    return (f"eq=contrast=1.08:saturation=1.12,"
            f"drawbox=x=0:y=0:w=iw:h=ih*{bar:.4f}:color=black:t=fill,"
            f"drawbox=x=0:y=ih*{1 - bar:.4f}:w=iw:h=ih*{bar:.4f}+2:color=black:t=fill,"
            f"fade=t=in:st=0:d=1,fade=t=out:st={out:.3f}:d=1")


def cinematic_audio(duration: float) -> str:
    return f"afade=t=in:st=0:d=1,afade=t=out:st={max(0.0, duration - 1):.3f}:d=1"
