"""Tests for FFmpegWriter lifecycle edge cases (issue #139)."""

import skvideo.io


def test_close_before_writeframe_does_not_raise(tmp_path):
    """Calling close() before any writeFrame() must not raise AttributeError.

    Previously self._proc was only assigned inside _createProcess() (lazy),
    so an early close() saw an undefined attribute (issue #139).
    """
    out_path = tmp_path / "out.mp4"
    writer = skvideo.io.FFmpegWriter(str(out_path))
    writer.close()  # must not raise


def test_with_block_no_frames(tmp_path):
    """A `with` block that writes zero frames must exit cleanly."""
    out_path = tmp_path / "out.mp4"
    with skvideo.io.FFmpegWriter(str(out_path)):
        pass  # no writeFrame call
