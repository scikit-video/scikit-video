import warnings
warnings.filterwarnings('ignore', category=UserWarning)

from numpy.testing import assert_equal, assert_almost_equal
import os
import sys
import numpy as np
import skvideo.io
import skvideo.datasets
import skvideo.measure

def test_measure_Viideo():
    vidpaths = skvideo.datasets.bigbuckbunny()
    dis = skvideo.io.vread(vidpaths, as_grey=True)
    dis = dis[:80, :200, :200]
    score = skvideo.measure.viideo_score(dis)
    assert_almost_equal(score, 0.71836352, decimal=8)

def test_measure_VideoBliinds():
    vidpaths = skvideo.datasets.bigbuckbunny()
    dis = skvideo.io.vread(vidpaths, as_grey=True)
    dis = dis[:20, :200, :200]
    features = skvideo.measure.videobliinds_features(dis)

    output = np.array([
      2.5088000000000021, 0.724275327323045, 0.8861500000000007, 0.094900842693629056,
      0.075270971555494642, 0.15325861073888791, 0.8329500000000006, 0.14585321322841788,
      0.047469422063737839, 0.15615215568504523, 0.8581500000000007, 0.043909016247040515,
      0.093810913769758003, 0.12884708807173553, 0.8573750000000006, 0.070210824862759855,
      0.08386625014618812, 0.13807367734350467, 3.1720250000000023, 0.97015263176310695,
      1.0041750000000007, 0.040410365123259274, 0.21275511045068587, 0.25307286632545678,
      0.9610000000000009, 0.18644517954657436, 0.1247713077966655, 0.3004221947501538,
      0.8754000000000005, -0.018816728814343462, 0.20691846471380232, 0.19199153588274515,
      0.9019250000000006, 0.030521913142025053, 0.1923558865107291, 0.2152507149491516,
      9.4895315992836764, 1.0096157789230347, 0.25037492252785809, 0.71355452219476423,
      0.67227717825038635, 0.66991249849828205, 0.69206157746299479, 0.62188467521925039,
      0.44126443934583309, 0.14251929738151306 
    ])

    for i in range(features.shape[0]):
      assert_almost_equal(features[i], output[i], decimal=10)

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
