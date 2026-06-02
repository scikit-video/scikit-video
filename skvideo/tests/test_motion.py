from numpy.testing import assert_equal, assert_almost_equal
import os
import sys
import numpy as np
import skvideo.io
import skvideo.motion
import skvideo.datasets

# gaussian ball
def gauss(cx, cy, sigma, sz):
    data = np.zeros((sz, sz, 3), dtype=np.float32)
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
    mvec = mvec.astype(np.float32)
    xmean = np.mean(mvec[:, :, :, 0])
    ymean = np.mean(mvec[:, :, :, 1])

    assert_almost_equal(ymean, -0.347222208976746, decimal=15)
    assert_almost_equal(xmean, 0.013888888992369, decimal=15)


def test_4SS():
    dat = getmockdata()
    mvec = skvideo.motion.blockMotion(dat, "4SS")
    mvec = mvec.astype(np.float32)
    xmean = np.mean(mvec[:, :, :, 0])
    ymean = np.mean(mvec[:, :, :, 1])

    assert_almost_equal(ymean, -0.770833313465118, decimal=15)
    assert_almost_equal(xmean, -0.055555555969477, decimal=15)


def test_3SS():
    dat = getmockdata()
    mvec = skvideo.motion.blockMotion(dat, "3SS")
    mvec = mvec.astype(np.float32)
    xmean = np.mean(mvec[:, :, :, 0])
    ymean = np.mean(mvec[:, :, :, 1])

    assert_almost_equal(ymean, -0.173611104488373, decimal=15)
    assert_almost_equal(xmean, 0.006944444496185, decimal=15)


def test_N3SS():
    dat = getmockdata()
    mvec = skvideo.motion.blockMotion(dat, "N3SS")
    mvec = mvec.astype(np.float32)
    xmean = np.mean(mvec[:, :, :, 0])
    ymean = np.mean(mvec[:, :, :, 1])

    assert_equal(xmean, 0.0)
    assert_equal(ymean, 0)


def test_SE3SS():
    dat = getmockdata()
    mvec = skvideo.motion.blockMotion(dat, "SE3SS")
    mvec = mvec.astype(np.float32)
    xmean = np.mean(mvec[:, :, :, 0])
    ymean = np.mean(mvec[:, :, :, 1])

    assert_almost_equal(ymean, -0.1458333283662796, decimal=5)
    assert_almost_equal(xmean, -0.0486111119389534, decimal=5)


def test_ARPS():
    dat = getmockdata()
    mvec = skvideo.motion.blockMotion(dat, "ARPS")
    mvec = mvec.astype(np.float32)
    xmean = np.mean(mvec[:, :, :, 0])
    ymean = np.mean(mvec[:, :, :, 1])

    assert_almost_equal(ymean, 0.013888888992369, decimal=15)
    assert_almost_equal(xmean, -0.333333343267441, decimal=15)


def test_DS():
    dat = getmockdata()
    mvec = skvideo.motion.blockMotion(dat, "DS")
    mvec = mvec.astype(np.float32)
    xmean = np.mean(mvec[:, :, :, 0])
    ymean = np.mean(mvec[:, :, :, 1])

    assert_almost_equal(ymean, 0.013888888992369, decimal=15)
    assert_almost_equal(xmean, -0.347222208976746, decimal=15)


def test_blockComp_zero_motion_covers_full_frame():
    # Regression: _checkBounded used >= and rejected blocks ending exactly
    # at the frame edge, so blockComp dropped every bottom/right macroblock.
    # With zero motion vectors, compensation must reproduce the frame
    # exactly, including the bottom-right block.
    mbSize = 8
    frame = np.arange(16 * 16, dtype=np.float64).reshape(16, 16, 1) + 1.0  # all nonzero
    vid = np.stack([frame, frame], axis=0)
    mv = np.zeros((1, 16 // mbSize, 16 // mbSize, 2), dtype=np.int64)

    comp = skvideo.motion.blockComp(vid, mv, mbSize=mbSize)

    # Frame 0 is passed through; frame 1 is compensated and, under zero
    # motion, must equal the original frame everywhere.
    assert_equal(comp[1], vid[1])
    # The previously-dropped bottom-right block must now be filled.
    assert comp[1, 8:16, 8:16, 0].min() > 0


def test_globalEdgeMotion_recovers_known_shift():
    # globalEdgeMotion was fully broken on Python 3: canny() hit a bare
    # `int32` NameError (image input), and the hausdorff branch compared
    # the shifted frame against itself and misspelled the raise. Verify
    # both methods recover a known translation.
    f1 = np.zeros((40, 40), np.float32)
    f1[10:30, 10:30] = 255.0  # a square with detectable edges
    f2 = np.roll(np.roll(f1, 3, axis=0), 2, axis=1)
    # Motion that moves f2 back onto f1 is (-3, -2).
    assert list(skvideo.motion.globalEdgeMotion(f1, f2, r=6, method="hamming")) == [-3, -2]
    assert list(skvideo.motion.globalEdgeMotion(f1, f2, r=6, method="hausdorff")) == [-3, -2]


def test_globalEdgeMotion_rejects_unknown_method():
    f1 = np.zeros((20, 20), np.float32)
    f1[5:15, 5:15] = 255.0
    with __import__("pytest").raises(NotImplementedError):
        skvideo.motion.globalEdgeMotion(f1, f1, method="bogus")


def test_canny_runs_on_image():
    # Regression: canny() used a bare `int32` (NameError on py3).
    import skvideo.utils
    img = np.zeros((32, 32), np.float32)
    img[8:24, 8:24] = 255.0
    edges = skvideo.utils.canny(img)
    assert edges.shape == (32, 32)
    assert edges.dtype == bool or edges.sum() >= 0  # ran without crashing
