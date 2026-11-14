from canal.config import Config


def test_defaults_match_spec():
    cfg = Config()
    assert cfg.short_size == (1080, 1920)
    assert cfg.short_max_s == 59.0
    assert cfg.thumb_size == (1280, 720)
    assert cfg.fps == 60
    assert cfg.long_max_height == 2160
