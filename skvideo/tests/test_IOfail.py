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


def test_failedextension():
    # 'garbage' extension is not a known encoder extension -> ValueError
    # (previously a bare assert, stripped under `python -O`).
    np.random.seed(0)
    outputdata = np.random.random(size=(5, 480, 640, 3)) * 255
    outputdata = outputdata.astype(np.uint8)
    with pytest.raises(ValueError):
        skvideo.io.vwrite("garbage.garbage", outputdata)
