from canal.config import Config
from canal.cut import chapters, keep_segments, render_long
from canal.probe import probe


def test_keep_segments_inverts_dead():
    assert keep_segments(20, [(6, 12)]) == [(0, 6), (12, 20)]


def test_keep_segments_no_dead():
    assert keep_segments(20, []) == [(0, 20)]


def test_keep_segments_dead_at_edges():
    assert keep_segments(20, [(0, 3), (17, 20)]) == [(3, 17)]


def test_render_long_duration(sample_video, tmp_path):
    src = sample_video(freeze_at=(6, 12))
    out = render_long(src, [(0, 6), (12, 20)], tmp_path / "longo.mp4", Config())
    info = probe(out)
    assert abs(info.duration - 14) < 0.5 and info.has_audio


def test_chapters_start_at_zero():
    segs = [(0, 200), (260, 600)]
    scenes = [(0, 50), (50, 130), (130, 290), (290, 400), (400, 600)]
    ch = chapters(segs, scenes)
    assert ch[0] == (0.0, "Início")
    ts = [t for t, _ in ch]
    assert all(b - a >= 60 for a, b in zip(ts, ts[1:]))
    assert all(name == f"Parte {i + 1}" for i, (_, name) in enumerate(ch[1:]))
    assert ts[-1] <= 540  # duração cortada = 540 s
