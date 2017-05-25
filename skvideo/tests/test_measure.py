import warnings
warnings.filterwarnings('ignore', category=UserWarning)

from numpy.testing import assert_equal, assert_almost_equal
import os
import sys
import numpy as np
import skvideo.io
import skvideo.datasets
import skvideo.measure

if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest

#TODO: Check blas implementation, then check numerical accuracy.
#      The required inverse operation in ST-RRED differs across
#      blas implementations

@unittest.skip("Disabled pending BLAS check")
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
        assert_almost_equal(strred_array[j, i], expected_array[j,i], decimal=3)

    assert_almost_equal(strred, 202.757949829101562, decimal=3)
    assert_almost_equal(strredssn, 4.097815036773682, decimal=3)

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
    assert_almost_equal(score, 0.72179317, decimal=8)

def test_measure_VideoBliinds():
    vidpaths = skvideo.datasets.bigbuckbunny()
    dis = skvideo.io.vread(vidpaths, as_grey=True)
    dis = dis[:20, :200, :200]
    features = skvideo.measure.videobliinds_features(dis)

    output = np.array([
      2.508800000000,0.724275349118,0.886150000000,0.094900845105,
      0.075270971672,0.153258614032,0.832950000000,0.145853236056,
      0.047469409576,0.156152160875,0.858150000000,0.043908992567,
      0.093810932519,0.128847087445,0.857375000000,0.070210827430,
      0.083866251922,0.138073680721,3.172000000000,0.970150022342,
      1.004175000000,0.040410359225,0.212755111969,0.253072861341,
      0.961000000000,0.186445182929,0.124771296044,0.300422186113,
      0.875400000000,-0.018816730259,0.206918460682,0.191991528548,
      0.901925000000,0.030521899481,0.192355885179,0.215250702742,
      9.489535449185,1.009615778923,0.250374922528,0.713554522195,
      0.672277178250,0.669912498498,0.692061577463,0.621884675219,
      0.441264439346,0.142519297382
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

    # beef up ref/dis forcing larger size
    im1 = np.zeros((512, 512))
    im2 = np.ones((512, 512))
    im1[::2] = im2[::2]
    im2 = im1.T
    scores = skvideo.measure.ssim(im1, im2, scaleFix=False)

    avg_score = np.mean(scores)

    assert_almost_equal(avg_score, 0.991528987884521, decimal=15)

    scores = skvideo.measure.ssim(im1, im2, scaleFix=True)

    avg_score = np.mean(scores)

    assert_almost_equal(avg_score, 1.0, decimal=15)

def test_measure_NIQE():
    vidpaths = skvideo.datasets.bigbuckbunny()

    ref = skvideo.io.vread(vidpaths, as_grey=True)

    # only first 2 frames
    ref = ref[:2]

    scores = skvideo.measure.niqe(ref)

    assert_almost_equal(scores[0], 11.197661399841, decimal=10)
    assert_almost_equal(scores[1], 11.055174827576, decimal=10)


def test_measure_MAD():
    vidpaths = skvideo.datasets.fullreferencepair()
    ref = skvideo.io.vread(vidpaths[0], as_grey=True)
    dis = skvideo.io.vread(vidpaths[1], as_grey=True)

    scores = skvideo.measure.mad(ref, dis)

    avg_score = np.mean(scores)

    assert_almost_equal(avg_score, 11.515880584716797, decimal=15)

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
