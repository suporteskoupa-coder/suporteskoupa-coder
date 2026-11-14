import json
import re
import shutil
from collections import namedtuple

import pytest

from canal import cli
from canal.cli import EspacoInsuficiente, processar
from canal.config import Config

FAST = Config(shorts_per_video=2)


def test_processar_creates_package(sample_video, tmp_path):
    out = processar(sample_video(seconds=40, freeze_at=(20, 26)), "teste", notas="praia",
                    out_root=tmp_path / "saida", cfg=FAST, short_len_s=8)
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}-teste", out.name)
    assert (out / "video.mp4").exists()
    assert len(list((out / "shorts").glob("*.mp4"))) >= 1
    assert len(list((out / "thumbs").glob("*.png"))) == 3
    assert "praia" in (out / "metadata.md").read_text(encoding="utf-8")
    data = json.loads((out / "analise.json").read_text(encoding="utf-8"))
    assert set(data) >= {"info", "scenes", "peaks", "dead", "segments", "chapters", "shorts", "frames"}
    assert data["dead"]


def test_processar_path_with_accents(sample_video, tmp_path):
    src = sample_video(seconds=12, name="missão da praia.mp4")
    out = processar(src, "praia", out_root=tmp_path / "saída", cfg=FAST, short_len_s=5)
    assert (out / "video.mp4").exists()


def test_free_space_check(sample_video, tmp_path, monkeypatch):
    src = sample_video(seconds=3)
    size = src.stat().st_size
    Usage = namedtuple("Usage", "total used free")
    monkeypatch.setattr(shutil, "disk_usage", lambda p: Usage(10 * size, 9 * size, size))
    with pytest.raises(EspacoInsuficiente, match="Espaço insuficiente"):
        processar(src, "x", out_root=tmp_path / "saida", cfg=FAST)
    assert not (tmp_path / "saida").exists() or not any((tmp_path / "saida").iterdir())


def test_main_short_subcommand(sample_video, tmp_path):
    src = sample_video(seconds=6)
    dst = tmp_path / "s.mp4"
    cli.main(["short", str(src), "--inicio", "1", "--fim", "4", "--texto", "Olá", "--saida", str(dst)])
    assert dst.exists()


def test_progress_output_survives_windows_codepage(capsys):
    # Claude Code no Windows lê a saída por pipe em cp1252
    with cli._Etapa("Análise do vídeo"):
        pass
    capsys.readouterr().out.encode("cp1252")
