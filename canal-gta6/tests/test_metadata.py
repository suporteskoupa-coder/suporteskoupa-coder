from pathlib import Path

from canal.metadata import write_metadata


def test_metadata_has_sections(tmp_path):
    out = write_metadata(tmp_path / "metadata.md", slug="praia", notas="passeio de noite na praia",
                         chapters=[(0.0, "Início"), (75.0, "Parte 1"), (3725.0, "Parte 2")],
                         shorts=[Path("shorts/01.mp4")], thumbs=[Path("thumbs/opcao-1.png")])
    s = out.read_text(encoding="utf-8")
    for h in ["## Título (PT)", "## Title (EN)", "## Descrição", "## Tags", "## Capítulos", "## Horário sugerido"]:
        assert h in s
    assert "0:00 Início" in s and "1:15 Parte 1" in s and "1:02:05 Parte 2" in s
    assert "passeio de noite na praia" in s
    assert "<!-- CLAUDE: preencher -->" in s
    assert "shorts/01.mp4" in s and "thumbs/opcao-1.png" in s
