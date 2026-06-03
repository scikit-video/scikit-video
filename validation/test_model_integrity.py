"""Phase 0.5: trained-model file integrity.

NIQE and Video-BLIINDS ship MATLAB .mat parameter files (pristine
multivariate-Gaussian models). This guards against those files being
corrupted or failing to load (a botched port, a truncated file, or a
git-LFS pointer stub committed by mistake): it checks they load with the
expected keys / shapes / finite values, and that the metrics consuming
them produce finite output that moves the right direction.

This is INTEGRITY (loads + runs + behaves sanely), not ACCURACY (matches
published dataset correlations) - accuracy is Phase 3/4.

Video-BLIINDS end-to-end was verified manually (46-dim finite features on
a 12-frame 256x256 clip) but is left out of this fast regression: it needs
>10 frames and >192px and is comparatively slow.

    pytest validation/test_model_integrity.py -q
"""
import os

import numpy as np
import pytest
import scipy.io
import scipy.ndimage as ndi

import skvideo.measure as M

DATA = os.path.join(os.path.dirname(M.__file__), "data")


def _content_image(seed=0, size=224):
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:size, 0:size]
    img = (127 + 60 * np.sin(xx / 12.0) + 40 * np.cos(yy / 20.0)
           + ndi.gaussian_filter(rng.uniform(0, 255, (size, size)), 3) * 0.5)
    return np.clip(img, 0, 255)


@pytest.mark.parametrize("fname,mu_key,cov_key", [
    ("niqe_image_params.mat", "pop_mu", "pop_cov"),
    ("frames_modelparameters.mat", "mu_prisparam", "cov_prisparam"),
])
def test_model_file_loads_and_is_sane(fname, mu_key, cov_key):
    p = scipy.io.loadmat(os.path.join(DATA, fname))
    for k in (mu_key, cov_key):
        assert k in p, f"{fname} missing key {k}"
        v = np.asarray(p[k], dtype=float)
        assert np.isfinite(v).all(), f"{fname}:{k} has non-finite values"
        assert not np.all(v == 0), f"{fname}:{k} is all zeros"
    assert np.ravel(p[mu_key]).size == 36
    assert np.asarray(p[cov_key]).shape == (36, 36)


def test_niqe_runs_and_direction_correct():
    clean = _content_image(0)[None, :, :, None]
    noised = np.clip(clean + np.random.default_rng(0).normal(0, 25, clean.shape), 0, 255)
    nc, nn = float(M.niqe(clean)[0]), float(M.niqe(noised)[0])
    assert np.isfinite(nc) and np.isfinite(nn)
    assert nn > nc, "NIQE should increase with added noise"


def test_brisque_features_finite():
    img = _content_image(1)[None, :, :, None]
    bf = np.ravel(M.brisque_features(img))
    assert bf.size == 36
    assert np.isfinite(bf).all()
