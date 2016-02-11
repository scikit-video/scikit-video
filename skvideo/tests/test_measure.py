import warnings
warnings.filterwarnings('ignore', category=UserWarning)

from numpy.testing import assert_equal
import os
import sys
import numpy as np
import skvideo.io
import skvideo.datasets
import skvideo.measure


def test_measure_SSIM():
    vidpaths = skvideo.datasets.fullreferencepair()
    ref = skvideo.io.vread(vidpaths[0], as_grey=True)
    dis = skvideo.io.vread(vidpaths[1], as_grey=True)

    scores = skvideo.measure.ssim(ref, dis)

    avg_score = np.mean(scores)

    assert_equal(avg_score, 0.722089148702586)


def test_measure_MSE():
    vidpaths = skvideo.datasets.fullreferencepair()
    ref = skvideo.io.vread(vidpaths[0], as_grey=True)
    dis = skvideo.io.vread(vidpaths[1], as_grey=True)

    scores = skvideo.measure.mse(ref, dis)

    avg_score = np.mean(scores)

    assert_equal(avg_score, 290.7301544086701)

def test_measure_PSNR():
    vidpaths = skvideo.datasets.fullreferencepair()
    ref = skvideo.io.vread(vidpaths[0], as_grey=True)
    dis = skvideo.io.vread(vidpaths[1], as_grey=True)

    scores = skvideo.measure.psnr(ref, dis)

    avg_score = np.mean(scores)

    assert_equal(avg_score, 23.506116528477801)
