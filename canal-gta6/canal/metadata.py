from pathlib import Path

FILL = "<!-- CLAUDE: preencher -->"


def fmt_ts(t: float) -> str:
    t = int(t)
    h, m, s = t // 3600, t % 3600 // 60, t % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def write_metadata(dst: Path, *, slug: str, notas: str, chapters: list[tuple[float, str]],
                   shorts: list[Path], thumbs: list[Path]) -> Path:
    caps = "\n".join(f"{fmt_ts(t)} {name}" for t, name in chapters)
    lines = [
        f"# {slug}",
        "",
        f"**Notas do dono:** {notas or '(nenhuma)'}",
        "",
        "## Título (PT)", FILL, "",
        "## Title (EN)", FILL, "",
        "## Descrição", FILL, "",
        "## Tags", FILL, "",
        "## Capítulos",
        "(renomear as partes; o YouTube exige 3+ capítulos de 10 s+ começando em 0:00)",
        "", caps, "",
        "## Thumbnails", *[f"- {p.as_posix()}" for p in thumbs], "",
        "## Shorts", *[f"- {p.as_posix()} — título: {FILL}" for p in shorts], "",
        "## Horário sugerido",
        "- Shorts: 12:00 e 19:00 (horário de Brasília)",
        "- Vídeo longo: 18:00 (horário de Brasília)",
        "",
    ]
    dst.write_text("\n".join(lines), encoding="utf-8")
    return dst
