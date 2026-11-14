from canal.probe import probe


def test_probe_reads_dimensions(sample_video):
    info = probe(sample_video())
    assert (info.width, info.height) == (1280, 720)
    assert abs(info.fps - 30) < 0.01
    assert abs(info.duration - 20) < 0.5
    assert info.has_audio and not info.is_hdr and not info.is_vfr


def test_probe_flags_hdr(sample_video):
    assert probe(sample_video(seconds=3, hdr=True)).is_hdr


def test_probe_flags_vfr(sample_video):
    assert probe(sample_video(seconds=3, vfr=True)).is_vfr


def test_probe_no_audio(sample_video):
    assert not probe(sample_video(seconds=3, audio=False)).has_audio
