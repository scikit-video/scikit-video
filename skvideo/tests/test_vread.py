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

def make_raw_videos():
    videodata = skvideo.io.vread(skvideo.datasets.bigbuckbunny())
    print videodata.shape
    skvideo.io.vwrite("bunnytest.yuv", videodata)

def delete_raw_videos():
    os.remove("bunnytest.yuv")

def test_vread_raw():
    make_raw_videos()
    videodata = skvideo.io.vread("bunnytest.yuv", width=1280, height=720)
    t, h, w, c = videodata.shape

    # check the dimensions of the video

    assert_equal(t, 132)
    assert_equal(h, 720)
    assert_equal(w, 1280)
    assert_equal(c, 3)

    # check the numbers

    assert_equal(109.28332841215979, np.mean(videodata))
   
    delete_raw_videos()
