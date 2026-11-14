"""--inicio: descarta a abertura (ex.: corpo/sangue nos primeiros segundos) do longo, Shorts e thumbs."""
import json

from canal import cli
from canal.analyze import Peak
from canal.cli import processar
from canal.config import Config
from canal.probe import probe
from canal.shorts import pick_short_windows


def test_windows_never_start_before_min_start():
    # pico em 6 s com lead de 3 s começaria em 3 s, dentro da abertura descartada
    w = pick_short_windows([Peak(6, -1), Peak(40, -2)], duration=100, n=2, length_s=10,
                           min_start=5)
    assert w and all(s >= 5 for s, _ in w)
    assert w[0] == (5, 15)


def test_processar_inicio_corta_abertura(sample_video, tmp_path):
    out = processar(sample_video(seconds=20), "inicio", out_root=tmp_path / "saida",
                    cfg=Config(shorts_per_video=2), short_len_s=5, inicio=6)
    assert abs(probe(out / "video.mp4").duration - 14) < 0.5
    data = json.loads((out / "analise.json").read_text(encoding="utf-8"))
    assert data["inicio"] == 6
    assert data["segments"][0][0] >= 6
    assert data["shorts"] and all(s["janela"][0] >= 6 for s in data["shorts"])
    assert all(int(f.split("t")[-1].split(".")[0]) >= 6 for f in data["thumbs_frames"])


def test_main_aceita_inicio(sample_video, tmp_path):
    src = sample_video(seconds=12)
    rc = cli.main(["processar", str(src), "--slug", "x", "--saida", str(tmp_path / "s"),
                   "--duracao-short", "4", "--inicio", "3"])
    assert rc == 0
    (pasta,) = (tmp_path / "s").iterdir()
    assert abs(probe(pasta / "video.mp4").duration - 9) < 0.5


def test_inicio_invalido_nao_cria_pasta(sample_video, tmp_path):
    rc = cli.main(["processar", str(sample_video(seconds=4)), "--slug", "x",
                   "--saida", str(tmp_path / "s"), "--inicio", "99"])
    assert rc == 2 and not (tmp_path / "s").exists()
