import subprocess
import tempfile
from pathlib import Path

from .config import Config
from .encode import (LOUDNORM, cinematic_audio, cinematic_video, pick_encoder,
                     target_height, video_args)
from .probe import probe

Seg = tuple[float, float]

# Acima disso o grafo vai para um arquivo (-/filter_complex, ffmpeg >= 7.1): o Windows limita
# a linha de comando a 32767 caracteres (~230 cortes). Abaixo, fica na linha para funcionar
# também com ffmpeg antigo.
GRAPH_FILE_MIN_CHARS = 8000


def keep_segments(duration: float, dead: list[Seg], min_keep_s: float = 1.0) -> list[Seg]:
    keep, cur = [], 0
    for s, e in sorted(dead):
        if s - cur >= min_keep_s:
            keep.append((cur, s))
        cur = max(cur, e)
    if duration - cur >= min_keep_s:
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
    total = sum(e - s for s, e in segments)
    vchain = f"scale=-2:{h},fps={cfg.fps}"
    achain = LOUDNORM
    if cfg.cinematic:
        vchain += "," + cinematic_video(info.width, info.height, total)
        achain += "," + cinematic_audio(total)
    graph += f";[cv]{vchain}[outv]"
    if a:
        graph += f";[ca]{achain}[outa]"
    graph_file = None
    if len(graph) >= GRAPH_FILE_MIN_CHARS:
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write(graph)
        graph_file = Path(f.name)
        graph_args = ["-/filter_complex", str(graph_file)]
    else:
        graph_args = ["-filter_complex", graph]
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(src), *graph_args, "-map", "[outv]"]
    if a:
        cmd += ["-map", "[outa]"]
    cmd += video_args(pick_encoder(), h, cfg.fps) + [str(dst)]
    try:
        subprocess.run(cmd, check=True)
    finally:
        if graph_file:
            graph_file.unlink(missing_ok=True)
    return dst
