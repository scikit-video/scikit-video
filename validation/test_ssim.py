"""Accuracy validation for SSIM (vs scikit-image) and MS-SSIM (sanity).

SSIM is cross-checked against scikit-image's structural_similarity,
configured IDENTICALLY to skvideo's implementation:

  - Gaussian 11-tap window, sigma=1.5 (truncate=3.5 -> radius 5)
  - K_1=0.01, K_2=0.03, data_range=255 (L = 2**8 - 1)
  - population covariance (use_sample_covariance=False)
  - both trim a 5px border before averaging

Two skvideo-specific differences are neutralised so we test the CORE
algorithm, not incidental config:
  - scaleFix=False: skvideo's default downsamples images whose min
    dimension > 256 (its own viewing-distance enhancement, off-spec vs
    Wang et al.); we disable it here.
  - skvideo computes in float32, skimage in float64, so agreement is
    expected at ~float32 precision (~1e-5), not exact.

MS-SSIM is cross-checked against `sewar.full_ref.msssim` (a pure
numpy/scipy/opencv reference - no torch/tf needed). MS-SSIM cascades 5
scales with inter-scale downsampling whose exact filter/crop is an
implementation choice, so cross-implementation agreement is looser than
single-scale SSIM (~4e-3 observed vs ~3e-5 for SSIM); a structural bug
would be 0.01-0.1. A sanity test (identity, monotonicity) also runs even
when sewar is absent. See the validation plan.

    pytest validation/test_ssim.py -q
"""
import numpy as np
import pytest

import skvideo.measure as M

skimage_metrics = pytest.importorskip("skimage.metrics")
import scipy.ndimage as ndi


def _content_image(seed=0, size=256):
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:size, 0:size]
    img = (127 + 60 * np.sin(xx / 12.0) + 40 * np.cos(yy / 20.0)
           + ndi.gaussian_filter(rng.uniform(0, 255, (size, size)), 3) * 0.5)
    return np.clip(img, 0, 255)


def _skvideo_ssim(ref, dis):
    # scaleFix=False -> compare the core algorithm, not skvideo's downsampling
    return float(M.ssim(ref[None, :, :, None], dis[None, :, :, None], scaleFix=False)[0])


def _skimage_ssim(ref, dis):
    return float(skimage_metrics.structural_similarity(
        ref, dis, data_range=255, gaussian_weights=True, sigma=1.5,
        use_sample_covariance=False, truncate=3.5))


def _distortions(base, rng):
    yield "identical", base.copy()
    for s in (5, 15, 30):
        yield f"noise{s}", np.clip(base + rng.normal(0, s, base.shape), 0, 255)
    for sg in (1.0, 2.5):
        yield f"blur{sg}", ndi.gaussian_filter(base, sg)
    yield "quantize40", (base // 40) * 40.0


def test_ssim_matches_skimage():
    """skvideo SSIM must match scikit-image (config-matched) to float32 precision."""
    base = _content_image(seed=0)
    rng = np.random.default_rng(0)
    worst = 0.0
    for name, dis in _distortions(base, rng):
        diff = abs(_skvideo_ssim(base, dis) - _skimage_ssim(base, dis))
        worst = max(worst, diff)
        assert diff < 1e-3, f"{name}: skvideo vs skimage SSIM diff {diff:.2e} exceeds 1e-3"
    # Observed worst case ~3e-5; 1e-3 leaves headroom while still catching a real bug.
    assert worst < 1e-3


def test_msssim_sanity():
    """Runs even without a reference: identity == 1 and monotonic degradation."""
    base = _content_image(seed=1)
    rng = np.random.default_rng(1)

    def ms(dis):
        return float(M.msssim(base[None, :, :, None], dis[None, :, :, None])[0])

    assert ms(base) == pytest.approx(1.0, abs=1e-4)
    prev = 1.0
    for s in (5, 15, 30, 60):
        v = ms(np.clip(base + rng.normal(0, s, base.shape), 0, 255))
        assert v < prev, f"MS-SSIM not monotonic at noise sigma={s}"
        prev = v


def test_msssim_matches_sewar():
    """skvideo MS-SSIM must match sewar's independent implementation. Looser
    tolerance than SSIM (1e-2) because 5-scale cascades differ legitimately
    in inter-scale downsampling; a structural bug would still exceed it."""
    sewar_fr = pytest.importorskip("sewar.full_ref")
    base = _content_image(seed=2)  # 256x256 -> skvideo scaleFix is a no-op throughout
    rng = np.random.default_rng(2)

    def sv(dis):
        return float(M.msssim(base[None, :, :, None], dis[None, :, :, None])[0])

    def sw(dis):
        return float(np.real(sewar_fr.msssim(base.astype(np.uint8), dis.astype(np.uint8), MAX=255)))

    cases = [("identical", base.copy())]
    for s in (5, 15, 30):
        cases.append((f"noise{s}", np.clip(base + rng.normal(0, s, base.shape), 0, 255)))
    for sg in (1.0, 2.5):
        cases.append((f"blur{sg}", ndi.gaussian_filter(base, sg)))

    for name, dis in cases:
        diff = abs(sv(dis) - sw(dis))
        assert diff < 1e-2, f"{name}: skvideo vs sewar MS-SSIM diff {diff:.2e} exceeds 1e-2"
