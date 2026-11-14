from canal.analyze import Peak
from canal.config import Config
from canal.probe import probe
from canal.shorts import pick_short_windows, render_short


def P(t, db=-10.0):
    return Peak(t=t, rms_db=db)


def test_windows_do_not_overlap():
    peaks = [P(50, -1), P(60, -2), P(120, -3), P(200, -4)]
    w = pick_short_windows(peaks, duration=300, n=5, length_s=30)
    ws = sorted(w)
    assert all(a[1] <= b[0] for a, b in zip(ws, ws[1:]))
    assert w[0] == (47, 77)  # o pico mais forte vem primeiro


def test_windows_clamped_to_duration():
    w = pick_short_windows([P(1), P(98)], duration=100, n=2, length_s=30)
    assert (0, 30) in w and (70, 100) in w


def test_short_video_yields_fewer_windows():
    assert pick_short_windows([P(4)], duration=8, n=3, length_s=30) == []


def test_respects_n():
    peaks = [P(t, -t / 100) for t in range(10, 1000, 40)]
    assert len(pick_short_windows(peaks, duration=1000, n=3, length_s=30)) == 3


def test_render_short_is_vertical(sample_video, tmp_path):
    out = render_short(sample_video(seconds=8), (1, 7), tmp_path / "s.mp4", Config())
    info = probe(out)
    assert (info.width, info.height) == (1080, 1920)
    assert info.duration <= 59 and abs(info.duration - 6) < 0.5


def test_render_short_caps_length(sample_video, tmp_path):
    out = render_short(sample_video(seconds=70), (0, 70), tmp_path / "s.mp4", Config())
    assert probe(out).duration <= 59.1


def test_render_short_with_accented_text(sample_video, tmp_path):
    out = render_short(sample_video(seconds=4), (0, 3), tmp_path / "s.mp4", Config(),
                       text="Ação na praia! 100% \"insano\": 'sério'")
    assert out.exists()


def test_fit_text_shrinks_or_wraps_long_text():
    from canal.shorts import fit_text
    font = Config().resolve_font()
    lines, size = fit_text("Sniper no topo da torre — visão incrível", font, max_w=972)
    from PIL import ImageFont
    f = ImageFont.truetype(str(font), size)
    assert all(f.getlength(l) <= 972 for l in lines) and size >= 44 and len(lines) <= 2
    assert fit_text("Curto", font, max_w=972) == (["Curto"], 72)


def test_render_short_long_text_stays_inside_frame(sample_video, tmp_path):
    import subprocess
    import numpy as np
    from PIL import Image
    src = sample_video(seconds=6)
    cfg = Config()

    def faixa(out):
        png = tmp_path / (out.stem + ".png")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "1", "-i", str(out), "-frames:v", "1",
                        str(png)], check=True)
        g = np.asarray(Image.open(png).convert("L"), dtype=np.float32)
        return g[int(1920 * 0.08):int(1920 * 0.30)]  # faixa onde o texto mora

    sem = faixa(render_short(src, (0, 3), tmp_path / "sem.mp4", cfg))
    com = faixa(render_short(src, (0, 3), tmp_path / "com.mp4", cfg,
                             text="Sniper no topo da torre — visão incrível"))
    borda = 20
    assert np.abs(com[:, :borda] - sem[:, :borda]).max() < 40      # nada de texto na borda esquerda
    assert np.abs(com[:, -borda:] - sem[:, -borda:]).max() < 40    # nem na direita
