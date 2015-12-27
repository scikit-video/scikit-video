from numpy.testing import assert_equal
import numpy as np
import skvideo.io
import skvideo.datasets


def test_vread():
    videodata = skvideo.io.vread(skvideo.datasets.bigbuckbunny())

    T, M, N, C = videodata.shape

    # check the dimensions of the video

    assert_equal(T, 132)
    assert_equal(M, 720)
    assert_equal(N, 1280)
    assert_equal(C, 3)

    # check the numbers

    assert_equal(np.mean(videodata), 109.28332841215979)

def make_raw_videos():
    videodata = skvideo.io.vread(skvideo.datasets.bigbuckbunny())
    skvideo.io.vwrite("bunnytest.yuv", videodata)

def delete_raw_videos():
    os.remove("bunnytest.yuv")

def test_vread_raw():
    make_raw_videos()
    videodata = skvideo.io.vread("bunnytest.yuv", width=1280, height=720)
    T, M, N, C = videodata.shape

    # check the dimensions of the video

    assert_equal(T, 132)
    assert_equal(M, 720)
    assert_equal(N, 1280)
    assert_equal(C, 3)

    # check the numbers

    assert_equal(np.mean(videodata), 109.28332841215979)
   
    delete_raw_videos()
