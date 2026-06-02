"""Tests for BytesIO / file-like output support (issue #113 write-side)."""
import io

import numpy as np
import pytest

import skvideo.io


def test_vwrite_to_bytesio_writes_bytes():
    """The basic guarantee: vwrite(BytesIO, data) actually fills the buffer.
    Previously crashed at os.path.abspath(BytesIO) before commit 5."""
    buf = io.BytesIO()
    data = np.zeros((10, 64, 64, 3), dtype=np.uint8)
    skvideo.io.vwrite(buf, data)
    assert buf.tell() > 0, "BytesIO is empty after vwrite — drain thread didn't run?"


def test_bytesio_output_round_trips():
    """Write frames to BytesIO, then read them back via the BytesIO reader.
    End-to-end proof that the memory writer produces a valid container."""
    out = io.BytesIO()
    written = np.zeros((5, 64, 64, 3), dtype=np.uint8)
    # Make each frame distinguishable so a silent corruption (all zeros)
    # gets caught.
    for i in range(5):
        written[i] = (i + 1) * 30  # 30, 60, 90, 120, 150
    skvideo.io.vwrite(out, written)
    out.seek(0)

    read_back = skvideo.io.vread(out)
    assert read_back.shape == (5, 64, 64, 3)
    # We won't get bit-exact pixels back (h264 is lossy at default settings),
    # but mean per frame should preserve the gradient.
    means = read_back.reshape(5, -1).mean(axis=1)
    assert np.all(np.diff(means) > 10), (
        "Frame mean gradient lost in round-trip: %r" % means.tolist()
    )


def test_ffmpegwriter_directly_to_bytesio():
    """Lower-level FFmpegWriter path also accepts BytesIO."""
    buf = io.BytesIO()
    writer = skvideo.io.FFmpegWriter(buf)
    try:
        for _ in range(3):
            writer.writeFrame(np.zeros((64, 64, 3), dtype=np.uint8))
    finally:
        writer.close()
    assert buf.tell() > 0


def test_bytesio_writer_propagates_user_format_choice():
    """If the user picks a different container (e.g. webm), the wrapper
    must not override their choice with its mp4 default."""
    buf = io.BytesIO()
    writer = skvideo.io.FFmpegWriter(
        buf,
        outputdict={"-f": "webm", "-vcodec": "libvpx-vp9", "-b:v": "200k"},
    )
    try:
        for _ in range(3):
            writer.writeFrame(np.zeros((64, 64, 3), dtype=np.uint8))
    finally:
        writer.close()
    # webm files start with the EBML magic bytes 0x1A 0x45 0xDF 0xA3
    body = buf.getvalue()
    assert body[:4] == b"\x1a\x45\xdf\xa3", (
        "Expected webm EBML magic; got %r — wrapper may have overridden -f" %
        body[:8]
    )


def test_bytesio_writer_surfaces_ffmpeg_failure():
    """If ffmpeg fails (e.g. bogus codec), close() should raise with a
    useful error rather than silently producing an empty BytesIO."""
    buf = io.BytesIO()
    writer = skvideo.io.FFmpegWriter(
        buf,
        outputdict={"-vcodec": "this_codec_does_not_exist_xyz"},
    )
    with pytest.raises((RuntimeError, IOError)):
        writer.writeFrame(np.zeros((64, 64, 3), dtype=np.uint8))
        writer.close()


def test_bytesio_writer_drain_thread_cleans_up():
    """After close(), the drain thread must have finished — no zombie
    threads holding refs to the user's buffer."""
    buf = io.BytesIO()
    writer = skvideo.io.FFmpegWriter(buf)
    try:
        for _ in range(3):
            writer.writeFrame(np.zeros((64, 64, 3), dtype=np.uint8))
    finally:
        writer.close()
    # Thread reference still on the writer (for introspection); just verify
    # it's no longer alive.
    assert writer._stdout_drain_thread is not None
    assert not writer._stdout_drain_thread.is_alive(), (
        "drain thread is still alive after close()"
    )
