from canal.analyze import audio_peaks, dead_segments, detect_scenes, sample_frames


def test_audio_peaks_finds_bursts(sample_video):
    peaks = audio_peaks(sample_video())
    top = sorted(p.t for p in peaks[:3])
    for got, want in zip(top, [5, 10, 15]):
        assert abs(got - want) <= 1


def test_audio_peaks_are_spaced(sample_video):
    peaks = audio_peaks(sample_video(seconds=40), top_n=20, min_gap_s=10)
    ts = sorted(p.t for p in peaks)
    assert all(b - a >= 10 for a, b in zip(ts, ts[1:]))
    assert peaks == sorted(peaks, key=lambda p: p.rms_db, reverse=True)


def test_dead_segments_finds_freeze(sample_video):
    segs = dead_segments(sample_video(freeze_at=(6, 12)), min_len_s=4.0)
    assert len(segs) == 1
    s, e = segs[0]
    assert 5.5 <= s <= 6.5 and 11.5 <= e <= 12.5


def test_no_audio_returns_no_peaks(sample_video):
    assert audio_peaks(sample_video(seconds=5, audio=False)) == []


def test_sample_frames_count(sample_video, tmp_path):
    frames = sample_frames(sample_video(), every_s=5, out_dir=tmp_path / "frames")
    assert len(frames) == 4 and all(f.suffix == ".jpg" and f.exists() for f in frames)


def test_detect_scenes_covers_video(sample_video):
    scenes = detect_scenes(sample_video(seconds=6))
    assert scenes and scenes[0][0] == 0.0 and abs(scenes[-1][1] - 6) < 0.5
