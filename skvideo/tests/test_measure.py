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
    assert_almost_equal(score, 0.71836346, decimal=8)

def test_measure_VideoBliinds():
    vidpaths = skvideo.datasets.bigbuckbunny()
    dis = skvideo.io.vread(vidpaths, as_grey=True)
    dis = dis[:20, :200, :200]
    features = skvideo.measure.videobliinds_features(dis)

    output = np.array([
      2.5088000000000021, 0.7242753367272081, 0.8861500000000007, 0.094900847568062191,
      0.075270973470923444, 0.15325861685068912, 0.8329500000000006, 0.14585321461603232,
      0.047469422938636596, 0.15615215763155582, 0.8581500000000007, 0.0439090205701466,
      0.093810915548360074, 0.1288470933706874, 0.8573750000000006, 0.07021082789886289,
      0.083866251161426389, 0.13807368076106666, 3.1720250000000023, 0.9701526392729102,
      1.0041750000000007, 0.04041036782592701, 0.21275511525845162, 0.2530728742388451,
      0.9610000000000009, 0.18644518630607176, 0.1247713083903639, 0.30042220162418243,
      0.8754000000000005, -0.018816728320646806, 0.20691846874650363, 0.19199154023722637,
      0.9019250000000006, 0.030521916222252365, 0.19235588688277644, 0.21525071798715123,
      9.4895317005425905, 1.0096157789230347, 0.25037494389374315, 0.71355452359121407,
      0.67227717951355304, 0.66991249910052508, 0.69206157878950736, 0.62188467499650601,
      0.4412644295129315, 0.14251931089412367 
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
