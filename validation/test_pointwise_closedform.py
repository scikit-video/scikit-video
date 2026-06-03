"""Accuracy validation for the point-wise metrics (mse / mae / psnr).

These metrics have closed-form ground truth, so no external reference
implementation is needed: the mathematical definition IS the reference.

  mse(x, x + c)  == c**2          (constant offset)
  mae(x, x + c)  == |c|
  psnr(x, x + c) == 10*log10(MAX**2 / c**2),  MAX = 2**bitdepth - 1

This is the cheapest, highest-confidence tier of the metric-accuracy plan:
zero setup, no dataset, no tolerance ambiguity. Run with:

    pytest validation/test_pointwise_closedform.py -q
"""
import numpy as np
import pytest

import skvideo.measure as M

ATOL = 1e-7


def _ref(shape, low=0.0, high=200.0, seed=0):
    return np.random.default_rng(seed).uniform(low, high, size=shape)


def test_identity():
    x = _ref((1, 64, 64, 1))
    assert np.allclose(M.mse(x, x), [0.0], atol=ATOL)
    assert np.allclose(M.mae(x, x), [0.0], atol=ATOL)
    assert np.isinf(M.psnr(x, x)[0])


@pytest.mark.parametrize("c", [1.0, 5.0, 15.0, 40.0])
def test_constant_offset(c):
    x = _ref((1, 48, 72, 1), seed=int(c))
    y = x + c
    assert np.allclose(M.mse(x, y), [c ** 2], atol=ATOL)
    assert np.allclose(M.mae(x, y), [abs(c)], atol=ATOL)
    assert np.allclose(M.psnr(x, y), [10 * np.log10(255.0 ** 2 / c ** 2)], atol=ATOL)


def test_multiframe_per_frame_correctness():
    cs = np.array([2.0, 10.0, 25.0])
    x = _ref((3, 40, 40, 1), seed=7)
    y = x + cs[:, None, None, None]
    assert np.allclose(M.mse(x, y), cs ** 2, atol=ATOL)
    assert np.allclose(M.mae(x, y), np.abs(cs), atol=ATOL)
    assert np.allclose(M.psnr(x, y), 10 * np.log10(255.0 ** 2 / cs ** 2), atol=ATOL)


def test_fractional_coverage():
    c = 20.0
    rng = np.random.default_rng(11)
    x = rng.uniform(0, 200, size=(1, 50, 50, 1))
    y = x.copy()
    mask = rng.random(x.shape) < 0.5
    frac = mask.mean()
    y[mask] += c
    assert np.allclose(M.mse(x, y), [frac * c ** 2], atol=ATOL)
    assert np.allclose(M.mae(x, y), [frac * abs(c)], atol=ATOL)
