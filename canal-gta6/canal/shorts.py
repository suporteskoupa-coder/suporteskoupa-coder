import subprocess
import tempfile
from pathlib import Path

from PIL import ImageFont

from .analyze import Peak
from .config import Config
from .encode import LOUDNORM, pick_encoder, video_args
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


def fit_text(text: str, font: Path, max_w: int, base: int = 72,
             min_size: int = 44) -> tuple[list[str], int]:
    """Texto que cabe em max_w: uma linha no maior tamanho possível; se ficar pequeno
    demais, quebra em 2 linhas. (No ensaio, 40 caracteres em 72 px vazavam do quadro.)"""
    def width(lines, size):
        f = ImageFont.truetype(str(font), size)
        return max(f.getlength(l) for l in lines)

    def best(lines):
        size = base
        while size > min_size and width(lines, size) > max_w:
            size -= 2
        return size

    one = [text]
    if width(one, min_size) <= max_w and best(one) >= 56:
        return one, best(one)
    words = text.split()
    if len(words) > 1:
        splits = [[" ".join(words[:i]), " ".join(words[i:])] for i in range(1, len(words))]
        two = min(splits, key=lambda ls: width(ls, base))
        return two, best(two)
    return one, best(one)


def _filter_path(p: Path) -> str:
    """Caminho seguro dentro de um filtro do ffmpeg (Windows: C\\:/...)."""
    return p.resolve().as_posix().replace(":", r"\:").replace("'", r"\'")


def render_short(src: Path, window: tuple[float, float], dst: Path, cfg: Config,
                 text: str | None = None) -> Path:
    w, h = cfg.short_size
    start = window[0]
    dur = min(window[1] - window[0], cfg.short_max_s)
    # fundo desfocado em 1/4 da resolução e ampliado: mesmo visual, 3,8x mais rápido (ensaio)
    graph = (f"[0:v]split[a][b];"
             f"[a]scale={w // 4}:{h // 4}:force_original_aspect_ratio=increase,crop={w // 4}:{h // 4},"
             f"boxblur=5,scale={w}:{h}[bg];"
             f"[b]scale={w}:-2[fg];"
             f"[bg][fg]overlay=(W-w)/2:(H-h)/2,fps={cfg.fps}")
    tmps: list[Path] = []
    if text:
        font = cfg.resolve_font()
        lines, size = fit_text(text, font, max_w=int(w * 0.9) - 12)  # 12 = contorno dos 2 lados
        # um drawtext por linha, centralizada: não depende de text_align (ffmpeg recente)
        for i, line in enumerate(lines):
            with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False,
                                             encoding="utf-8") as tmp:
                tmp.write(line)
            tmps.append(Path(tmp.name))
            graph += (f",drawtext=fontfile='{_filter_path(font)}'"
                      f":textfile='{_filter_path(tmps[-1])}':expansion=none"
                      f":fontsize={size}:fontcolor=white:borderw=6:bordercolor=black"
                      f":x=(w-text_w)/2:y=h*0.12+{i * int(size * 1.25)}")
    graph += "[outv]"
    cmd = ["ffmpeg", "-y", "-v", "error", "-ss", f"{start}", "-t", f"{dur}", "-i", str(src),
           "-filter_complex", graph, "-map", "[outv]"]
    if probe(src).has_audio:
        cmd += ["-map", "0:a", "-af", LOUDNORM]
    cmd += video_args(pick_encoder(), h, cfg.fps) + [str(dst)]
    try:
        subprocess.run(cmd, check=True)
    finally:
        for t in tmps:
            t.unlink(missing_ok=True)
    return dst
