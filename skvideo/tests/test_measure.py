import warnings
warnings.filterwarnings('ignore', category=UserWarning)

from numpy.testing import assert_equal, assert_almost_equal
import os
import sys
import numpy as np
import skvideo.io
import skvideo.datasets
import skvideo.measure

def test_measure_STRRED():
    vidpaths = skvideo.datasets.fullreferencepair()

    ref = skvideo.io.vread(vidpaths[0], as_grey=True)[:12]
    dis = skvideo.io.vread(vidpaths[1], as_grey=True)[:12]

    strred_array, strred, strredssn = skvideo.measure.strred(ref, dis)

    expected_array = np.array([
        [7.973215579986572, 21.013387680053711, 1.136332869529724, 3.105512380599976],
        [7.190542221069336, 28.211503982543945, 0.824764370918274, 11.768671989440918],
        [7.762616157531738, 30.080577850341797, 0.483192980289459, 11.239683151245117],
        [7.838700771331787, 29.701192855834961, 0.275575548410416, 1.088217139244080],
        [6.290620326995850, 31.812648773193359, 0.417621076107025, 11.035059928894043],
        [7.427119731903076, 23.272958755493164, 0.656901776790619, 0.641671419143677]
    ])

    for j in range(6):
      for i in range(4):
        assert_almost_equal(strred_array[j, i], expected_array[j,i], decimal=15)

    assert_almost_equal(strred, 202.757949829101562, decimal=15)
    assert_almost_equal(strredssn, 4.097815036773682, decimal=15)

def test_measure_MSSSIM():
    vidpaths = skvideo.datasets.fullreferencepair()

    ref = skvideo.io.vread(vidpaths[0], as_grey=True)
    dis = skvideo.io.vread(vidpaths[1], as_grey=True)

    ref = np.pad(ref, [(0, 0), (20, 20), (20, 20), (0, 0)], mode='constant')
    dis = np.pad(dis, [(0, 0), (20, 20), (20, 20), (0, 0)], mode='constant')

    scores = skvideo.measure.msssim(ref, dis)

    assert_almost_equal(np.mean(scores), 0.909682154655457, decimal=15)


def test_measure_BRISQUE():
    vidpaths = skvideo.datasets.bigbuckbunny()
    dis = skvideo.io.vread(vidpaths, as_grey=True)
    dis = dis[0, :200, :200]
    features = skvideo.measure.brisque_features(dis)

    output = np.array([
      2.2890000343, 0.2322334051, 0.8130000234, 0.0714222640, 
      0.0303122569, 0.0790375844, 0.7820000052, 0.1253909320, 
      0.0196695272, 0.1092280298, 0.8009999990, 0.0333177634, 
      0.0419092514, 0.0649642125, 0.8009999990, 0.0416957438, 
      0.0396158583, 0.0685468540, 3.1700000763, 0.3377875388, 
      0.9840000272, 0.0400288589, 0.0888380781, 0.1259520650, 
      0.9520000219, 0.1778325588, 0.0371656679, 0.2002325803, 
      0.8489999771, -0.0157390144, 0.1383629888, 0.1215882078, 
      0.8629999757, 0.0312444586, 0.1079876497, 0.1403252929
    ])

    for i in range(features.shape[1]):
      assert_almost_equal(features[0, i], output[i], decimal=10)

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

    assert_almost_equal(avg_score, 0.722089111804962, decimal=15)


def test_measure_MSE():
    vidpaths = skvideo.datasets.fullreferencepair()
    ref = skvideo.io.vread(vidpaths[0], as_grey=True)
    dis = skvideo.io.vread(vidpaths[1], as_grey=True)

    scores = skvideo.measure.mse(ref, dis)

    avg_score = np.mean(scores)

    assert_almost_equal(avg_score, 290.730133056640625, decimal=15)

def test_measure_PSNR():
    vidpaths = skvideo.datasets.fullreferencepair()
    ref = skvideo.io.vread(vidpaths[0], as_grey=True)
    dis = skvideo.io.vread(vidpaths[1], as_grey=True)

    scores = skvideo.measure.psnr(ref, dis)

    avg_score = np.mean(scores)

    assert_equal(avg_score, 23.506116528477801)
