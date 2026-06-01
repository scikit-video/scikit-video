"""Tests for start_frame / windowed reading (issue #166)."""
import numpy as np
import pytest

import skvideo.io
import skvideo.datasets


# bigbuckbunny is 132 frames at 25 fps (~5.28s); test assertions use that.


def test_start_frame_with_num_frames_returns_exact_count():
    """start_frame + num_frames gives a deterministic window size."""
    videodata = skvideo.io.vread(
        skvideo.datasets.bigbuckbunny(),
        start_frame=50,
        num_frames=20,
    )
    assert videodata.shape == (20, 720, 1280, 3)


def test_start_frame_alone_skips_frames():
    """start_frame alone reduces the total frame count (~total - start_frame).

    The actual count may differ by a few frames due to keyframe-based seek;
    we assert a loose bound rather than equality.
    """
    full = skvideo.io.vread(skvideo.datasets.bigbuckbunny())
    windowed = skvideo.io.vread(skvideo.datasets.bigbuckbunny(), start_frame=50)
    # Full bunny is 132 frames; seek at 50 should leave ~82, allow ±10 slack
    # for keyframe seek imprecision.
    assert windowed.shape[0] < full.shape[0]
    assert 70 <= windowed.shape[0] <= 95, (
        "expected ~82 frames after start_frame=50, got %d" % windowed.shape[0]
    )


def test_start_frame_actually_seeks():
    """The first frame returned after start_frame=50 should NOT equal frame 0
    of the full read — otherwise the seek did nothing.
    """
    first_frame_full = skvideo.io.vread(skvideo.datasets.bigbuckbunny(), num_frames=1)[0]
    first_frame_after_seek = skvideo.io.vread(
        skvideo.datasets.bigbuckbunny(), start_frame=50, num_frames=1
    )[0]
    # Use a large pixel-level MSE threshold so this catches "seek did nothing"
    # without being sensitive to FFmpeg version differences in the seek target.
    mse = float(np.mean((first_frame_full.astype(np.float32) -
                          first_frame_after_seek.astype(np.float32)) ** 2))
    assert mse > 50.0, (
        "Seek appears to have returned the same frame as full-read (MSE=%f). "
        "start_frame should have advanced past frame 0." % mse
    )


def test_start_frame_rejects_double_ss():
    """If the caller supplies BOTH start_frame and inputdict['-ss'], we
    refuse rather than silently letting one shadow the other.
    """
    with pytest.raises(ValueError, match="start_frame"):
        skvideo.io.vread(
            skvideo.datasets.bigbuckbunny(),
            start_frame=50,
            inputdict={"-ss": "1.5"},
        )


def test_vreader_supports_start_frame():
    """The generator API mirrors vread()."""
    reader = skvideo.io.vreader(
        skvideo.datasets.bigbuckbunny(),
        start_frame=50,
        num_frames=10,
    )
    frames = list(reader)
    assert len(frames) == 10
    assert frames[0].shape == (720, 1280, 3)
