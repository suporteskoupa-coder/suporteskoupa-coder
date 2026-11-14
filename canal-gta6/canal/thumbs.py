from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps

from .config import Config


def sharpness(img: Path) -> float:
    """Variância do Laplaciano em tons de cinza (maior = mais nítido)."""
    g = np.asarray(Image.open(img).convert("L"), dtype=np.float32)
    lap = (-4 * g[1:-1, 1:-1] + g[:-2, 1:-1] + g[2:, 1:-1] + g[1:-1, :-2] + g[1:-1, 2:])
    return float(lap.var())


def best_frames(frames: list[Path], k: int, min_gap: int = 3) -> list[Path]:
    order = sorted(range(len(frames)), key=lambda i: sharpness(frames[i]), reverse=True)
    picked: list[int] = []
    for i in order:
        if all(abs(i - j) >= min_gap for j in picked):
            picked.append(i)
            if len(picked) == k:
                break
    return [frames[i] for i in picked]


def make_thumb(frame: Path, dst: Path, cfg: Config, text: str | None = None) -> Path:
    img = ImageOps.fit(Image.open(frame).convert("RGB"), cfg.thumb_size, Image.LANCZOS)
    img = ImageEnhance.Contrast(img).enhance(1.15)
    if text:
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype(str(cfg.resolve_font()), size=96)
        box = draw.textbbox((0, 0), text, font=font, stroke_width=8)
        x = (img.width - (box[2] - box[0])) // 2
        draw.text((x, img.height - (box[3] - box[1]) - 60), text, font=font,
                  fill="white", stroke_width=8, stroke_fill="black")
    dst.parent.mkdir(parents=True, exist_ok=True)
    img.save(dst)
    return dst
