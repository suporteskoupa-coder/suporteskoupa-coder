"""Pendências do ensaio: vídeo 100% parado, muitos cortes, detecção de cena por corte seco."""
import subprocess

from canal import cut
from canal.analyze import detect_scenes
from canal.cli import processar
from canal.config import Config
from canal.cut import keep_segments, render_long
from canal.probe import probe

WIN_CMDLINE_MAX = 32767  # limite do CreateProcess no Windows


def test_keep_segments_drops_slivers():
    # pedaços < 1 s entre trechos mortos viram ruído no corte
    assert keep_segments(20, [(0, 6), (6.5, 14)]) == [(14, 20)]


def test_processar_video_totalmente_parado(sample_video, tmp_path):
    src = sample_video(seconds=12, freeze_at=(0, 12))
    out = processar(src, "parado", out_root=tmp_path / "saida", cfg=Config(shorts_per_video=1),
                    short_len_s=5)
    # nada a cortar com segurança: mantém o vídeo inteiro em vez de quebrar
    assert abs(probe(out / "video.mp4").duration - 12) < 0.5


def test_render_long_muitos_cortes_cabe_na_linha_de_comando(sample_video, tmp_path, monkeypatch):
    src = sample_video(seconds=4)
    segs = [(i * 9.123457, i * 9.123457 + 4.567891) for i in range(500)]  # ~1 h com 500 cortes
    capturado = {}
    real_run = subprocess.run

    def fake_run(cmd, **kw):
        if cmd[0] != "ffmpeg":  # ffprobe segue de verdade
            return real_run(cmd, **kw)
        capturado["cmd"] = cmd
        idx = cmd.index("-/filter_complex") if "-/filter_complex" in cmd else None
        if idx is not None:
            with open(cmd[idx + 1], encoding="utf-8") as f:
                capturado["grafo"] = f.read()
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(cut.subprocess, "run", fake_run)
    render_long(src, segs, tmp_path / "l.mp4", Config())
    assert len(subprocess.list2cmdline(capturado["cmd"])) < WIN_CMDLINE_MAX
    assert "concat=n=500" in capturado.get("grafo", "")


def test_render_long_grafo_em_arquivo_funciona_de_verdade(sample_video, tmp_path, monkeypatch):
    monkeypatch.setattr(cut, "GRAPH_FILE_MIN_CHARS", 0)  # força o caminho do arquivo
    src = sample_video(seconds=10)
    out = render_long(src, [(0, 3), (5, 10)], tmp_path / "l.mp4", Config())
    assert abs(probe(out).duration - 8) < 0.5


def test_detect_scenes_acha_corte_seco(tmp_path):
    src = tmp_path / "corte.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y",
                    "-f", "lavfi", "-i", "testsrc2=size=640x360:rate=30:duration=4",
                    "-f", "lavfi", "-i", "mandelbrot=size=640x360:rate=30",
                    "-filter_complex", "[1:v]trim=duration=4,setpts=PTS-STARTPTS,format=yuv420p[b];"
                                       "[0:v]format=yuv420p[a];[a][b]concat=n=2:v=1[v]",
                    "-map", "[v]", "-c:v", "libx264", "-preset", "ultrafast", str(src)], check=True)
    scenes = detect_scenes(src)
    assert scenes[0][0] == 0.0 and abs(scenes[-1][1] - 8) < 0.5
    assert any(abs(s - 4) < 0.5 for s, _ in scenes[1:])
