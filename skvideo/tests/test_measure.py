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

    assert_almost_equal(np.mean(scores), 0.909682154655457, decimal=2)


def test_measure_BRISQUE():
    vidpaths = skvideo.datasets.bigbuckbunny()
    dis = skvideo.io.vread(vidpaths, as_grey=True)
    dis = dis[0, :200, :200]
    features = skvideo.measure.brisque_features(dis)

    # Reference regenerated 2026-05 against numpy 2.4, scipy 1.17, opencv 4.13,
    # ffmpeg 8.1. The first half (indices 0-17, "first subband") is essentially
    # unchanged from the 2018 baseline; the second half (indices 18-35, "second
    # subband") drifted by up to ~0.4 because the second-subband MSCN goes
    # through cv2.resize whose default interpolation behavior has changed.
    output = np.array([
        2.2890000343, 0.2322352976, 0.8130000234, 0.0714223012,
        0.0303128175, 0.0790385231, 0.7820000052, 0.1253915578,
        0.0196698494, 0.1092294082, 0.8009999990, 0.0333176553,
        0.0419099517, 0.0649650022, 0.8009999990, 0.0416956730,
        0.0396165289, 0.0685476810, 2.8050000668, 0.3836214840,
        0.9129999876, -0.0166532192, 0.1542353481, 0.1358711720,
        0.8759999871, 0.1370459199, 0.0800065324, 0.2339500189,
        0.8019999862, -0.0352361463, 0.1921713501, 0.1484891176,
        0.8050000072, 0.0092620207, 0.1591690481, 0.1704723388,
    ])

    for i in range(features.shape[1]):
      assert_almost_equal(features[0, i], output[i], decimal=2)

def test_measure_Viideo():
    vidpaths = skvideo.datasets.bigbuckbunny()
    dis = skvideo.io.vread(vidpaths, as_grey=True)
    dis = dis[:80, :200, :200]
    score = skvideo.measure.viideo_score(dis)
    # Value changed 2026-06 by the VIIDEO accuracy fix: viideo_score is now a
    # faithful port of the LIVE reference computeVIIDEOscore.m (verified to
    # ~1e-5 against Octave on the release demo clips). The prior 0.72179317 was
    # the old broken port (NIQE gamma grid + truncated edge patches). This pin
    # is self-referential, not external ground truth.
    assert_almost_equal(score, 0.69935427, decimal=2)

def test_measure_VideoBliinds():
    vidpaths = skvideo.datasets.bigbuckbunny()
    dis = skvideo.io.vread(vidpaths, as_grey=True)
    dis = dis[:20, :200, :200]
    features = skvideo.measure.videobliinds_features(dis)

    # Values changed 2026-06 by two Video-BLIINDS faithfulness fixes, bringing
    # the features into agreement with the original Video-BLIINDS MATLAB:
    #   (1) resize: computequality now downsamples with antialiased
    #       imresize(...,'bicubic') (was cv2.resize INTER_CUBIC) -> changed the
    #       scale-2 NIQE features [18:35] and the NIQE score [36].
    #   (2) motion tie-break: blockMotion(...,tiebreak='reference') matches the
    #       reference minCost.m (top-left wins equal-cost ties) -> slightly
    #       changed the motion features [44:45].
    # Scale-1 NIQE [0:17] and DCT/spectral [37:43] are unchanged. Self-pinned.
    output = np.array([
        2.5088000000, 0.7242788489, 0.8861750000, 0.0949017145,
        0.0752771542, 0.1532683975, 0.8329750000, 0.1458550347,
        0.0474738216, 0.1561622395, 0.8581500000, 0.0439089416,
        0.0938119084, 0.1288480221, 0.8574000000, 0.0702115546,
        0.0838724282, 0.1380829532, 3.1720250000, 0.9701545832,
        1.0041750000, 0.0404103531, 0.2127559627, 0.2530737028,
        0.9610000000, 0.1864457556, 0.1247718168, 0.3004232500,
        0.8754000000, -0.0188169924, 0.2069193063, 0.1919921613,
        0.9019250000, 0.0305220692, 0.1923565446, 0.2152514981,
        9.4891487887, 1.0096157789, 0.2503749225, 0.7135545222,
        0.6722771783, 0.6699124985, 0.6920615775, 0.6218846752,
        0.4408835769, 0.1416096091,
    ])


    for i in range(features.shape[0]):
      assert_almost_equal(features[i], output[i], decimal=2)

def test_measure_Li3DDCT_smoke():
    # Smoke test only: the exported Li3DDCT_features previously raised
    # NameError ('int32' not defined) on every Python-3 call, so there is
    # no historical reference output to pin. Verify it runs and returns a
    # finite (5*63,) feature vector. Also exercises the T==4 minimum.
    vidpath = skvideo.datasets.bigbuckbunny()
    dis = skvideo.io.vread(vidpath, as_grey=True)[:8, :64, :64]
    features = skvideo.measure.Li3DDCT_features(dis)
    assert features.shape == (5 * 63,)
    assert np.all(np.isfinite(features))

    # T == 4 is the documented minimum and must yield one group of frames,
    # not an empty slice.
    features4 = skvideo.measure.Li3DDCT_features(dis[:4])
    assert features4.shape == (5 * 63,)
    assert np.all(np.isfinite(features4))

def test_measure_SSIM():
    vidpaths = skvideo.datasets.fullreferencepair()
    ref = skvideo.io.vread(vidpaths[0], as_grey=True)
    dis = skvideo.io.vread(vidpaths[1], as_grey=True)

    scores = skvideo.measure.ssim(ref, dis)

    avg_score = np.mean(scores)

    assert_almost_equal(avg_score, 0.722089111804962, decimal=2)

    # beef up ref/dis forcing larger size
    im1 = np.zeros((512, 512))
    im2 = np.ones((512, 512))
    im1[::2] = im2[::2]
    im2 = im1.T
    scores = skvideo.measure.ssim(im1, im2, scaleFix=False)

    avg_score = np.mean(scores)

    assert_almost_equal(avg_score, 0.991528987884521, decimal=2)

    scores = skvideo.measure.ssim(im1, im2, scaleFix=True)

    avg_score = np.mean(scores)

    assert_almost_equal(avg_score, 1.0, decimal=2)

def test_measure_NIQE():
    vidpaths = skvideo.datasets.bigbuckbunny()

    ref = skvideo.io.vread(vidpaths, as_grey=True)

    # only first 2 frames
    ref = ref[:2]

    scores = skvideo.measure.niqe(ref)

    # NIQE uses the reference LIVE pristine model as of 1.1.16; values shifted
    # from the old inaccurate model (~11.5) to ~4.1 (clean content scores low,
    # as expected for a naturalness metric). decimal=0 keeps a generous
    # tolerance for BLAS/resize differences across platforms (OpenBLAS on Linux
    # vs Accelerate on macOS).
    assert_almost_equal(scores[0], 4.13, decimal=0)
    assert_almost_equal(scores[1], 4.10, decimal=0)

def test_measure_MAE():
    vidpaths = skvideo.datasets.fullreferencepair()
    ref = skvideo.io.vread(vidpaths[0], as_grey=True)
    dis = skvideo.io.vread(vidpaths[1], as_grey=True)

    scores = skvideo.measure.mae(ref, dis)

    avg_score = np.mean(scores)

    assert_almost_equal(avg_score, 11.515880584716797, decimal=2)

def test_measure_MSE():
    vidpaths = skvideo.datasets.fullreferencepair()
    ref = skvideo.io.vread(vidpaths[0], as_grey=True)
    dis = skvideo.io.vread(vidpaths[1], as_grey=True)

    scores = skvideo.measure.mse(ref, dis)

    avg_score = np.mean(scores)

    assert_almost_equal(avg_score, 290.730133056640625, decimal=2)

def test_measure_PSNR():
    vidpaths = skvideo.datasets.fullreferencepair()
    ref = skvideo.io.vread(vidpaths[0], as_grey=True)
    dis = skvideo.io.vread(vidpaths[1], as_grey=True)

    scores = skvideo.measure.psnr(ref, dis)

    avg_score = np.mean(scores)

    assert_equal(avg_score, 23.506116528477801)
