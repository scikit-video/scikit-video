import skvideo.io
import numpy as np
import pytest


def test_failedread():
    # try to read invalid path
    with pytest.raises(OSError):
        skvideo.io.vread("garbage")


def test_failedwrite():
    # 'garbage' folder does not exist
    np.random.seed(0)
    outputdata = np.random.random(size=(5, 480, 640, 3)) * 255
    outputdata = outputdata.astype(np.uint8)
    with pytest.raises(AssertionError):
        skvideo.io.vwrite("garbage/garbage.mp4", outputdata)


def test_failedextension():
    # 'garbage' extension does not exist
    np.random.seed(0)
    outputdata = np.random.random(size=(5, 480, 640, 3)) * 255
    outputdata = outputdata.astype(np.uint8)
    with pytest.raises(AssertionError):
        skvideo.io.vwrite("garbage.garbage", outputdata)
