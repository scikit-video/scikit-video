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

    assert_equal(109.28332841215979, np.mean(videodata))
