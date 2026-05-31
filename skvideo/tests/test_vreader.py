from numpy.testing import assert_equal
import numpy as np
import skvideo.io
import skvideo.datasets
import sys

if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest


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

    # check the numbers (allow 1% tolerance — exact value is FFmpeg-version-dependent)

    np.testing.assert_allclose(accumulation / (T * M * N * C), 109.28, rtol=0.01)


@unittest.skipIf(not skvideo._HAS_FFMPEG, "FFmpeg required for this test.")
def test_vreader_ffmpeg():
    _vreader("ffmpeg")


@unittest.skipIf(not skvideo._HAS_AVCONV, "LibAV required for this test.")
def test_vreader_libav_version12():
    try:
        if int(skvideo._LIBAV_MAJOR_VERSION) < 12:
            return
    except:
        return

    _vreader("libav")

