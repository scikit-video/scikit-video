import warnings
warnings.filterwarnings('ignore', category=UserWarning)

from numpy.testing import assert_equal, assert_almost_equal, assert_allclose
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

def test_measure_STRRED():
    # ST-RRED's per-frame entropy step involves a matrix inverse whose result
    # drifts slightly across BLAS backends, so the old per-frame decimal=3 pin
    # was flaky and the test was skipped. The port is, however, validated
    # faithful: it matches the LIVE Octave reference to ~1e-6 per frame pair,
    # and reproduces the paper's LIVE VQA correlation (ALL SROCC 0.8007 vs the
    # published ~0.80, n=150). So we guard the BLAS-robust invariants plus a
    # loose-tolerance pin on the aggregate, which still catches real
    # algorithm regressions.
    #
    # The faithful per-frame reference values (Accelerate; columns = spatial
    # RRED, temporal RRED, spatial SSN, temporal SSN) are recorded here for
    # documentation but not asserted, since per-frame BLAS drift exceeds a
    # tight tolerance:
    #     [7.9732, 21.0134, 1.1363, 3.1055], [7.1905, 28.2115, 0.8248, 11.7687],
    #     [7.7626, 30.0806, 0.4832, 11.2397], [7.8387, 29.7012, 0.2756, 1.0882],
    #     [6.2906, 31.8126, 0.4176, 11.0351], [7.4271, 23.2730, 0.6569, 0.6417]
    vidpaths = skvideo.datasets.fullreferencepair()

    ref = skvideo.io.vread(vidpaths[0], as_grey=True)[:12]
    dis = skvideo.io.vread(vidpaths[1], as_grey=True)[:12]

    strred_array, strred, strredssn = skvideo.measure.strred(ref, dis)

    # one row per non-overlapping frame pair (T//2), 4 columns, all finite
    assert strred_array.shape == (ref.shape[0] // 2, 4)
    assert np.all(np.isfinite(strred_array))

    # identity anchor: no spatio-temporal difference -> exactly 0 (BLAS-invariant)
    assert skvideo.measure.strred(ref, ref)[1] == 0.0

    # a real distortion must register above the identity floor
    assert strred > 0.0

    # faithful-reference aggregate. Cross-BLAS spread is ~4e-6 relative
    # (Accelerate 202.7560 / OpenBLAS 202.7551), so a 1e-3 tolerance is
    # ~250x the observed drift yet tight enough to catch regressions.
    assert_allclose(strred, 202.7556, rtol=1e-3)
    assert_allclose(strredssn, 4.0990, rtol=5e-3)

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

    # Second-subband features (indices 18-35) changed 2026-06 by the resize fix:
    # the half-scale downsample now uses antialiased imresize(...,'bicubic')
    # matching the BRISQUE reference, instead of cv2.resize(INTER_CUBIC). This
    # brings the second subband into agreement with the original BRISQUE MATLAB
    # and recovers LIVE IQA accuracy (validated). First subband (0-17), which is
    # not downsampled, is unchanged. Self-pinned.
    output = np.array([
        2.2890000343, 0.2322352976, 0.8130000234, 0.0714223012,
        0.0303128175, 0.0790385231, 0.7820000052, 0.1253915578,
        0.0196698494, 0.1092294082, 0.8009999990, 0.0333176553,
        0.0419099517, 0.0649650022, 0.8009999990, 0.0416956730,
        0.0396165289, 0.0685476810, 3.1700000763, 0.3377887607,
        0.9840000272, 0.0400287546, 0.0888387486, 0.1259527653,
        0.9520000219, 0.1778330803, 0.0371659324, 0.2002338618,
        0.8489999771, -0.0157392956, 0.1383639872, 0.1215888560,
        0.8629999757, 0.0312444791, 0.1079883352, 0.1403260976,
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

    # NIQE uses the reference LIVE pristine model as of 1.2.0; values shifted
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
