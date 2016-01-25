from numpy.testing import assert_equal
import os
import sys
import numpy as np
import skvideo.io
import skvideo.motion
import skvideo.datasets

# gaussian ball
def gauss(cx, cy, sigma, sz):
    data = np.zeros((sz, sz, 3), dtype=np.float)
    for y in range(-sigma*3, sigma*3+1, 1):
        for x in range(-sigma*3, sigma*3+1, 1):
            magnitude = np.exp(-0.5 * (x**2 + y**2)/(sigma**2))
            if ((x + cx < 0) or (x + cx > sz) or (y + cy < 0) or (y + cy > sz)):
                continue
            data[y + cy, x + cx, 0] = magnitude
            data[y + cy, x + cx, 1] = magnitude
            data[y + cy, x + cx, 2] = magnitude
    return data

def getmockdata():
    frame1 = gauss(50, 50, 5, 100)
    frame2 = gauss(55, 50, 5, 100)
    videodata = []
    videodata.append(frame1)
    videodata.append(frame2)
    videodata = np.array(videodata)
    return videodata

# exhaustive search
def test_ES():
    dat = getmockdata()
    mvec = skvideo.motion.blockMotion(dat, "ES")
    mvec = mvec.astype(np.float)
    xmean = np.mean(mvec[:, :, :, 0])
    ymean = np.mean(mvec[:, :, :, 1])
    assert_equal(xmean, 0.31944444444444442)
    assert_equal(ymean, -0.0069444444444444441)


def test_4SS():
    dat = getmockdata()
    mvec = skvideo.motion.blockMotion(dat, "4SS")
    mvec = mvec.astype(np.float)
    xmean = np.mean(mvec[:, :, :, 0])
    ymean = np.mean(mvec[:, :, :, 1])
    print(xmean, ymean)
    assert_equal(xmean, 0.5625)
    assert_equal(ymean, -0.125)


def test_3SS():
    dat = getmockdata()
    mvec = skvideo.motion.blockMotion(dat, "3SS")
    mvec = mvec.astype(np.float)
    xmean = np.mean(mvec[:, :, :, 0])
    ymean = np.mean(mvec[:, :, :, 1])
    assert_equal(xmean, 0.17361111111111111)
    assert_equal(ymean, 0)


def test_N3SS():
    dat = getmockdata()
    mvec = skvideo.motion.blockMotion(dat, "N3SS")
    mvec = mvec.astype(np.float)
    xmean = np.mean(mvec[:, :, :, 0])
    ymean = np.mean(mvec[:, :, :, 1])

    assert_equal(xmean, 0.17361111111111111)
    assert_equal(ymean, 0)


def test_SE3SS():
    dat = getmockdata()
    mvec = skvideo.motion.blockMotion(dat, "SE3SS")
    mvec = mvec.astype(np.float)
    xmean = np.mean(mvec[:, :, :, 0])
    ymean = np.mean(mvec[:, :, :, 1])
    assert_equal(xmean, 0.0208333333333333332)
    assert_equal(ymean, 0)


def test_ARPS():
    dat = getmockdata()
    mvec = skvideo.motion.blockMotion(dat, "ARPS")
    mvec = mvec.astype(np.float)
    xmean = np.mean(mvec[:, :, :, 0])
    ymean = np.mean(mvec[:, :, :, 1])
    assert_equal(ymean, -0.0069444444444444441)
    assert_equal(xmean, 0.31944444444444442)


def test_DS():
    dat = getmockdata()
    mvec = skvideo.motion.blockMotion(dat, "DS")
    mvec = mvec.astype(np.float)
    xmean = np.mean(mvec[:, :, :, 0])
    ymean = np.mean(mvec[:, :, :, 1])
    assert_equal(ymean, -0.0069444444444444441)
    assert_equal(xmean, 0.31944444444444442)
