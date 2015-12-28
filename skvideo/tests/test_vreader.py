from numpy.testing import assert_equal
import numpy as np
import skvideo.io
import skvideo.datasets


def _vreader(backend):
    reader = skvideo.io.vreader(skvideo.datasets.bigbuckbunny(), backend=backend)

    T = 0
    M = 0
    N = 0
    C = 0
    accumulation = 0
    for frame in reader:
        M, N, C = frame.shape
        accumulation += np.sum(frame)
        T += 1

    # check the dimensions of the video

    assert_equal(T, 132)
    assert_equal(M, 720)
    assert_equal(N, 1280)
    assert_equal(C, 3)

    # check the numbers

    assert_equal(109.28332841215979, accumulation / (T * M * N * C))


def test_vreader_ffmpeg():
    _vreader("ffmpeg")

def test_vreader_libav():
    _vreader("libav")

