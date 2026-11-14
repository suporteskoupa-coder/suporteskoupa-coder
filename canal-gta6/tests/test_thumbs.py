import numpy as np
from PIL import Image, ImageFilter

from canal.config import Config
from canal.thumbs import best_frames, make_thumb, sharpness


def _checker(path, blur=0):
    a = (np.indices((360, 640)).sum(axis=0) // 20 % 2 * 255).astype("uint8")
    img = Image.fromarray(a).convert("RGB")
    if blur:
        img = img.filter(ImageFilter.GaussianBlur(blur))
    img.save(path)
    return path


def test_sharpness_orders(tmp_path):
    assert sharpness(_checker(tmp_path / "a.jpg")) > sharpness(_checker(tmp_path / "b.jpg", blur=6))


def test_best_frames_prefers_sharp(tmp_path):
    frames = [_checker(tmp_path / f"{i}.jpg", blur=0 if i == 5 else 6) for i in range(10)]
    assert best_frames(frames, k=1)[0].name == "5.jpg"


def test_best_frames_spacing(tmp_path):
    frames = [_checker(tmp_path / f"{i}.jpg", blur=i % 3) for i in range(12)]
    picked = [frames.index(f) for f in best_frames(frames, k=3, min_gap=3)]
    assert len(picked) == 3
    assert all(abs(a - b) >= 3 for i, a in enumerate(picked) for b in picked[i + 1:])


def test_make_thumb_size(tmp_path):
    out = make_thumb(_checker(tmp_path / "a.jpg"), tmp_path / "t.png", Config(), text="Vice City à noite")
    assert Image.open(out).size == (1280, 720)
