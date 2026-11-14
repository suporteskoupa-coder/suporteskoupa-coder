import subprocess
from pathlib import Path

import pytest


def make_video(path: Path, *, seconds=20, width=1280, height=720, fps=30,
               freeze_at=None, hdr=False, vfr=False, audio=True) -> Path:
    """Vídeo sintético: testsrc2 + seno com um estrondo (ruído) a cada 5 s."""
    vf = []
    if freeze_at:
        s, e = freeze_at
        # congela usando o frame em s durante [s, e]
        vf.append(f"loop=loop={int((e - s) * fps)}:size=1:start={int(s * fps)},trim=duration={seconds}")
    if vfr:
        # primeiro segundo cheio, depois metade dos frames: timestamps irregulares
        vf.append("select='lt(t\\,1)+not(mod(n\\,2))'")
    if hdr:
        # ffmpeg 9 ignora -color_trc/-color_primaries de saída: marcar no próprio frame
        vf.append("setparams=color_primaries=bt2020:color_trc=smpte2084:colorspace=bt2020nc")
    cmd = ["ffmpeg", "-y", "-v", "error",
           "-f", "lavfi", "-i", f"testsrc2=size={width}x{height}:rate={fps}:duration={seconds}"]
    if audio:
        bursts = "+".join(f"between(t,{t},{t + 0.4})" for t in range(5, int(seconds), 5)) or "0"
        expr = f"0.05*sin(2*PI*220*t)+0.9*({bursts})*(random(0)*2-1)"
        cmd += ["-f", "lavfi", "-i", f"aevalsrc='{expr}':s=48000:d={seconds}"]
    if vf:
        cmd += ["-vf", ",".join(vf)]
    if vfr:
        cmd += ["-fps_mode", "vfr"]
    cmd += ["-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p"]
    if hdr:
        cmd += ["-color_primaries", "bt2020", "-color_trc", "smpte2084", "-colorspace", "bt2020nc"]
    if audio:
        cmd += ["-c:a", "aac", "-shortest"]
    cmd.append(str(path))
    subprocess.run(cmd, check=True)
    return path


@pytest.fixture
def sample_video(tmp_path):
    counter = {"n": 0}

    def _make(**kw):
        counter["n"] += 1
        name = kw.pop("name", f"amostra{counter['n']}.mp4")
        return make_video(tmp_path / name, **kw)

    return _make
