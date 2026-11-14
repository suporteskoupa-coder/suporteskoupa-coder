import subprocess
from pathlib import Path

from .config import Config
from .encode import pick_encoder, target_height, video_args
from .probe import probe

Seg = tuple[float, float]


def keep_segments(duration: float, dead: list[Seg]) -> list[Seg]:
    keep, cur = [], 0
    for s, e in sorted(dead):
        if s > cur:
            keep.append((cur, s))
        cur = max(cur, e)
    if cur < duration:
        keep.append((cur, duration))
    return keep


def _to_cut_time(t: float, segments: list[Seg]) -> float | None:
    """Converte um tempo da fonte para o tempo no vídeo cortado (None se caiu num corte)."""
    offset = 0.0
    for s, e in segments:
        if s <= t < e:
            return offset + (t - s)
        offset += e - s
    return None


def chapters(segments: list[Seg], scenes: list[Seg], min_gap_s: float = 60.0) -> list[tuple[float, str]]:
    total = sum(e - s for s, e in segments)
    marks = [0.0]
    for start, _ in scenes:
        t = _to_cut_time(start, segments)
        if t is not None and t - marks[-1] >= min_gap_s and total - t >= 10:
            marks.append(t)
    return [(0.0, "Início")] + [(t, f"Parte {i}") for i, t in enumerate(marks[1:], 1)]


def render_long(src: Path, segments: list[Seg], dst: Path, cfg: Config) -> Path:
    info = probe(src)
    parts, labels = [], []
    for i, (s, e) in enumerate(segments):
        parts.append(f"[0:v]trim=start={s}:end={e},setpts=PTS-STARTPTS[v{i}]")
        labels.append(f"[v{i}]")
        if info.has_audio:
            parts.append(f"[0:a]atrim=start={s}:end={e},asetpts=PTS-STARTPTS[a{i}]")
            labels.append(f"[a{i}]")
    h = target_height(info, cfg)
    a = 1 if info.has_audio else 0
    graph = ";".join(parts) + f";{''.join(labels)}concat=n={len(segments)}:v=1:a={a}[cv]" + ("[ca]" if a else "")
    graph += f";[cv]scale=-2:{h},fps={cfg.fps}[outv]"
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(src), "-filter_complex", graph, "-map", "[outv]"]
    if a:
        cmd += ["-map", "[ca]"]
    cmd += video_args(pick_encoder(), h, cfg.fps) + [str(dst)]
    subprocess.run(cmd, check=True)
    return dst
