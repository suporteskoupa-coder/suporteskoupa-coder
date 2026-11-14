import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .probe import probe

SR = 8000


@dataclass(frozen=True)
class Peak:
    t: float
    rms_db: float


_SCENE = re.compile(r"lavfi\.scd\.time: ([\d.]+)")
_FREEZE = re.compile(r"lavfi\.freezedetect\.freeze_(start|end): ([\d.]+)")
SCAN_WIDTH = 480      # análise em baixa resolução: 4K decodifica uma vez só, filtros baratos
SCENE_THRESHOLD = 10  # scdet (0-100); só alimenta os capítulos, precisão fina não importa


def scan(path: Path, min_len_s: float) -> tuple[list[tuple[float, float]], list[tuple[float, float]]]:
    """Uma passada do ffmpeg: cenas (scdet) e trechos parados (freezedetect).

    Ensaio: em 4K60 o PySceneDetect levava 0,87x a duração (~52 min por 1 h);
    scdet + freezedetect juntos ficam em ~0,25x.
    """
    err = subprocess.run(
        ["ffmpeg", "-v", "info", "-i", str(path), "-an",
         "-vf", f"scale={SCAN_WIDTH}:-2,freezedetect=n=-60dB:d={min_len_s},"
                f"scdet=t={SCENE_THRESHOLD}",
         "-f", "null", "-"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    ).stderr
    duration = probe(path).duration
    cuts = sorted({float(t) for t in _SCENE.findall(err) if 0 < float(t) < duration})
    bounds = [0.0, *cuts, duration]
    scenes = list(zip(bounds, bounds[1:]))
    dead, start = [], None
    for kind, val in _FREEZE.findall(err):
        if kind == "start":
            start = float(val)
        elif start is not None:
            dead.append((start, float(val)))
            start = None
    if start is not None:
        dead.append((start, duration))
    return scenes, dead


def detect_scenes(path: Path) -> list[tuple[float, float]]:
    return scan(path, min_len_s=4.0)[0]


def audio_peaks(path: Path, window_s: float = 1.0, top_n: int = 20,
                min_gap_s: float = 3.0) -> list[Peak]:
    """Janelas de áudio mais altas, ordenadas por volume, com espaçamento mínimo."""
    if not probe(path).has_audio:
        return []
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-vn", "-ac", "1", "-ar", str(SR),
         "-f", "s16le", "-"],
        capture_output=True, check=True,
    ).stdout
    pcm = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    win = int(SR * window_s)
    n = len(pcm) // win
    if n == 0:
        return []
    rms = np.sqrt((pcm[: n * win].reshape(n, win) ** 2).mean(axis=1))
    db = 20 * np.log10(np.maximum(rms, 1e-9))
    chosen: list[Peak] = []
    for i in np.argsort(db)[::-1]:
        t = float(i * window_s)
        if all(abs(t - p.t) >= min_gap_s for p in chosen):
            chosen.append(Peak(t=t, rms_db=float(db[i])))
            if len(chosen) == top_n:
                break
    return chosen


def dead_segments(path: Path, min_len_s: float) -> list[tuple[float, float]]:
    """Trechos com imagem parada (loading, menus, pausa)."""
    return scan(path, min_len_s)[1]


def sample_frames(path: Path, every_s: float, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    duration = probe(path).duration
    frames, k = [], 0
    while k * every_s < duration:
        t = k * every_s
        dst = out_dir / f"t{int(t):05d}.jpg"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t}", "-i", str(path),
                        "-frames:v", "1", "-q:v", "3", str(dst)], check=True)
        if dst.exists():
            frames.append(dst)
        k += 1
    return frames
