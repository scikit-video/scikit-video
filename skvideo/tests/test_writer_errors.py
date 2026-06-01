"""Tests for FFmpegWriter error surfacing (issue #111)."""
import numpy as np
import pytest

import skvideo.io


def test_close_raises_on_invalid_codec(tmp_path):
    """A bogus codec should surface FFmpeg's error, not produce silent garbage.

    Before #111 was fixed, an invalid -vcodec value caused FFmpeg to exit
    non-zero, but close() called wait() and ignored the return code — the
    user got an empty output file with no exception.
    """
    out_path = tmp_path / "out.mp4"
    writer = skvideo.io.FFmpegWriter(
        str(out_path),
        outputdict={"-vcodec": "this_codec_does_not_exist_xyz"},
    )
    with pytest.raises((RuntimeError, IOError)) as exc_info:
        writer.writeFrame(np.zeros((64, 64, 3), dtype=np.uint8))
        writer.close()
    # The exception message should contain FFmpeg's actual complaint, not
    # just a Python-level broken-pipe.
    msg = str(exc_info.value).lower()
    assert "ffmpeg" in msg or "codec" in msg or "unknown" in msg, (
        "Expected FFmpeg's stderr in the error message, got: %r" % str(exc_info.value)
    )


def test_close_returns_normally_on_success(tmp_path):
    """close() must not raise when FFmpeg exits cleanly."""
    out_path = tmp_path / "out.mp4"
    writer = skvideo.io.FFmpegWriter(str(out_path))
    for _ in range(3):
        writer.writeFrame(np.zeros((64, 64, 3), dtype=np.uint8))
    writer.close()  # should not raise
    assert out_path.stat().st_size > 0
