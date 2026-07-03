import skvideo.io
import numpy as np
import pytest


def test_failedread():
    # try to read invalid path
    with pytest.raises(OSError):
        skvideo.io.vread("garbage")


def test_failedwrite():
    # 'garbage' folder does not exist -> not a writable directory.
    # Validation now raises OSError instead of a bare assert (which would
    # vanish under `python -O`).
    np.random.seed(0)
    outputdata = np.random.random(size=(5, 480, 640, 3)) * 255
    outputdata = outputdata.astype(np.uint8)
    with pytest.raises(OSError):
        skvideo.io.vwrite("garbage/garbage.mp4", outputdata)


def test_failedextension(tmp_path):
    # An unknown extension no longer trips the (deprecated) hardcoded
    # allowlist ValueError; it warns and defers to ffmpeg, which cannot
    # infer a muxer for '.garbage' and fails loudly at write time with
    # its own diagnostics (issue #111 machinery).
    np.random.seed(0)
    outputdata = np.random.random(size=(5, 480, 640, 3)) * 255
    outputdata = outputdata.astype(np.uint8)
    with pytest.warns(UserWarning, match="[Ee]xtension"):
        with pytest.raises((RuntimeError, OSError)):
            skvideo.io.vwrite(str(tmp_path / "garbage.garbage"), outputdata)
