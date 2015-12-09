from numpy.testing import assert_equal
import numpy as np
import skvideo.io
import skvideo.datasets


def test_vread():
    videodata = skvideo.io.vread(skvideo.datasets.bigbuckbunny())

    t, h, w, c = videodata.shape

    # check the dimensions of the video

    assert_equal(t, 132)
    assert_equal(h, 720)
    assert_equal(w, 1280)
    assert_equal(c, 3)

    # check the numbers

    assert_equal(np.mean(videodata), 109.28332841215979)

def test_vread_generator():
    videogen = skvideo.io.vread_generator(skvideo.datasets.bigbuckbunny())

    t = 0
    h = 0
    w = 0
    c = 0
    accumulation = 0
    for frame in videogen:
        h, w, c = frame.shape
        accumulation += np.sum(frame)
        t += 1

    # check the dimensions of the video

    assert_equal(t, 132)
    assert_equal(h, 720)
    assert_equal(w, 1280)
    assert_equal(c, 3)

    # check the numbers

    assert_equal(accumulation / (t * h * w * c), 109.28332841215979)
