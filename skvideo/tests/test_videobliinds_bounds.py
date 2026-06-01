"""Tests for videobliinds out-of-bounds motion vector handling (issue #97)."""
import numpy as np
import pytest

import skvideo.measure.videobliinds as vb


def _make_frames(T=3, H=64, W=64):
    """A tiny synthetic video sized so blockMotion produces a 4x4 grid of vectors
    (with mblock=16). Real content doesn't matter — we just need shapes to work."""
    rng = np.random.RandomState(0)
    return (rng.random_sample((T, H, W, 1)) * 255).astype(np.uint8)


def test_default_n3ss_path_returns_finite():
    """Default method (N3SS) must still produce a finite output — sanity check
    that the new bounds-check + nanstd/nanmean didn't change the success path."""
    frames = _make_frames()
    result = vb.temporal_dc_variation_feature_extraction(frames)
    assert result.shape == (1,)
    assert np.isfinite(result[0]), "Expected finite output for N3SS path, got %r" % result[0]


def test_handles_out_of_bounds_vectors(monkeypatch):
    """Out-of-bounds motion vectors must not raise; they get NaN'd and the
    remaining blocks aggregate normally. Previously this raised
    `ValueError: operands could not be broadcast together with shapes (16,16) (0,16)`
    (issue #97)."""
    frames = _make_frames(T=3, H=64, W=64)
    # 64/16 = 4 blocks per dim, 2 frame-pairs (T-1)
    # Patch blockMotion to return vectors where SOME point way outside the frame
    fake_vectors = np.zeros((2, 4, 4, 2), dtype=np.int8)
    # Make the top-left block in each pair point to (-32, -32) — far out of bounds
    fake_vectors[:, 0, 0, :] = -32
    # And the bottom-right block point past the frame edge
    fake_vectors[:, 3, 3, :] = 32

    def fake_block_motion(frames, **kwargs):
        return fake_vectors

    monkeypatch.setattr(vb, "blockMotion", fake_block_motion)

    result = vb.temporal_dc_variation_feature_extraction(frames)
    assert result.shape == (1,)
    assert np.isfinite(result[0]), (
        "Out-of-bounds vectors should be NaN'd and ignored, not propagated. "
        "Got %r" % result[0]
    )
