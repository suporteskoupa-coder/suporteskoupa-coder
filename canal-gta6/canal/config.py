from dataclasses import dataclass
from pathlib import Path

_SYSTEM_FONTS = [
    Path("C:/Windows/Fonts/arialbd.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
]


@dataclass(frozen=True)
class Config:
    long_max_height: int = 2160
    fps: int = 60
    short_size: tuple[int, int] = (1080, 1920)
    short_max_s: float = 59.0
    shorts_per_video: int = 5
    thumb_size: tuple[int, int] = (1280, 720)
    thumb_options: int = 3
    dead_min_s: float = 4.0
    font_path: Path = Path("marca/fonte.ttf")

    def resolve_font(self) -> Path:
        """Fonte da marca se existir; senão uma fonte do sistema."""
        if self.font_path.is_file():
            return self.font_path
        for f in _SYSTEM_FONTS:
            if f.is_file():
                return f
        raise FileNotFoundError("Nenhuma fonte encontrada; coloque uma em marca/fonte.ttf")
