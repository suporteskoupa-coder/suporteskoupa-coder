import argparse
import json
import shutil
import sys
import time
from dataclasses import asdict
from datetime import date
from pathlib import Path

from .analyze import audio_peaks, dead_segments, detect_scenes, sample_frames
from .config import Config
from .cut import chapters, keep_segments, render_long
from .encode import normalize, pick_encoder
from .metadata import write_metadata
from .probe import probe
from .shorts import pick_short_windows, render_short
from .thumbs import best_frames, make_thumb


def _frame_t(f: Path) -> int:
    return int(f.stem.lstrip("t"))


class EspacoInsuficiente(RuntimeError):
    pass


def check_free_space(src: Path, out_root: Path) -> None:
    alvo = out_root.resolve()
    while not alvo.exists():
        alvo = alvo.parent
    precisa = 2 * src.stat().st_size
    livre = shutil.disk_usage(alvo).free
    if livre < precisa:
        gb = 1024 ** 3
        raise EspacoInsuficiente(
            f"Espaço insuficiente: precisa de ~{precisa / gb:.1f} GB, tem {livre / gb:.1f} GB")


class _Etapa:
    def __init__(self, nome: str):
        self.nome = nome

    def __enter__(self):
        self.t0 = time.monotonic()
        print(f"- {self.nome}...", flush=True)

    def __exit__(self, *exc):
        if exc[0] is None:
            print(f"  ok ({time.monotonic() - self.t0:.0f} s)", flush=True)


def processar(src: Path, slug: str, notas: str = "", out_root: Path = Path("saida"),
              cfg: Config = Config(), short_len_s: float = 30.0) -> Path:
    src = Path(src)
    check_free_space(src, out_root)
    out = out_root / f"{date.today():%Y-%m-%d}-{slug}"
    (out / "shorts").mkdir(parents=True, exist_ok=True)
    print(f"Encoder: {pick_encoder()}")

    with _Etapa("Lendo o arquivo"):
        info = probe(src)
    trabalho, temp = src, None
    if info.is_hdr or info.is_vfr or round(info.fps) != cfg.fps:
        with _Etapa("Normalizando (HDR/fps)"):
            temp = out / "_normalizado.mp4"
            trabalho = normalize(src, temp, info, cfg)
            info = probe(trabalho)
    try:
        with _Etapa("Analisando"):
            scenes = detect_scenes(trabalho)
            peaks = audio_peaks(trabalho)
            dead = dead_segments(trabalho, cfg.dead_min_s)
            segments = keep_segments(info.duration, dead)
            frames = sample_frames(trabalho, max(1.0, info.duration / 60), out / "frames")
        with _Etapa("Vídeo longo"):
            render_long(trabalho, segments, out / "video.mp4", cfg)
            caps = chapters(segments, scenes)
        with _Etapa("Shorts"):
            vivos = [p for p in peaks if any(s <= p.t < e for s, e in segments)]
            janelas = pick_short_windows(vivos, info.duration, cfg.shorts_per_video, short_len_s)
            shorts = [render_short(trabalho, w, out / "shorts" / f"{i:02d}.mp4", cfg)
                      for i, w in enumerate(janelas, 1)]
        with _Etapa("Thumbnails"):
            # frames de loading/menu têm muito texto e "parecem" nítidos: fora
            candidatos = [f for f in frames
                          if not any(s <= _frame_t(f) < e for s, e in dead)] or frames
            escolhidos = best_frames(candidatos, cfg.thumb_options)
            if len(escolhidos) < cfg.thumb_options:
                escolhidos = best_frames(candidatos, cfg.thumb_options, min_gap=1)
            thumbs = [make_thumb(f, out / "thumbs" / f"opcao-{i}.png", cfg)
                      for i, f in enumerate(escolhidos, 1)]
        rel = lambda ps: [p.relative_to(out) for p in ps]
        write_metadata(out / "metadata.md", slug=slug, notas=notas, chapters=caps,
                       shorts=rel(shorts), thumbs=rel(thumbs))
        analise = {
            "fonte": str(src), "info": asdict(info), "scenes": scenes,
            "peaks": [asdict(p) for p in peaks], "dead": dead, "segments": segments,
            "chapters": caps, "shorts": [{"arquivo": str(p.relative_to(out)), "janela": w}
                                         for p, w in zip(shorts, janelas)],
            "frames": [str(f.relative_to(out)) for f in frames],
            "thumbs_frames": [str(f.relative_to(out)) for f in escolhidos],
        }
        (out / "analise.json").write_text(json.dumps(analise, ensure_ascii=False, indent=2),
                                          encoding="utf-8")
    finally:
        if temp:
            temp.unlink(missing_ok=True)
    print(f"Pronto: {out}")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="canal")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("processar", help="gera o pacote completo de um arquivo")
    p.add_argument("arquivo", type=Path)
    p.add_argument("--slug", required=True)
    p.add_argument("--notas", default="")
    p.add_argument("--saida", type=Path, default=Path("saida"))
    p.add_argument("--duracao-short", type=float, default=30.0)
    p.add_argument("--cinematic", action="store_true",
                   help="cor + barras de cinema + fades (bom para passeios)")
    s = sub.add_parser("short", help="gera um Short de um trecho específico")
    s.add_argument("arquivo", type=Path)
    s.add_argument("--inicio", type=float, required=True)
    s.add_argument("--fim", type=float, required=True)
    s.add_argument("--texto")
    s.add_argument("--saida", type=Path, required=True)
    a = ap.parse_args(argv)
    try:
        if a.cmd == "processar":
            processar(a.arquivo, a.slug, a.notas, a.saida, cfg=Config(cinematic=a.cinematic),
                      short_len_s=a.duracao_short)
        else:
            a.saida.parent.mkdir(parents=True, exist_ok=True)
            render_short(a.arquivo, (a.inicio, a.fim), a.saida, Config(), text=a.texto)
    except EspacoInsuficiente as e:
        print(e, file=sys.stderr)
        return 2
    return 0
