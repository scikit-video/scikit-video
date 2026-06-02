"""Tests for URL output support (issue #117 write-side, related #81).

Full end-to-end URL output (e.g. rtmp publish, HTTP PUT) depends on a
cooperating server that handles ffmpeg's chunked streaming behavior — that
infrastructure is heavier than v1.1.14 needs. The wrapper's actual guarantee
is narrower: "don't block construction on the URL string." That's what these
tests verify.
"""
import io as _io

import pytest

import skvideo.io


def test_ffmpegwriter_accepts_rtmp_url_without_crashing():
    """Before commit 4, constructing a writer with rtmp:// crashed with
    `AssertionError: Cannot write to directory:` because os.path.split on
    `rtmp://host/path` returns ('rtmp:', '/host/path'), and os.access on
    'rtmp:' fails. Now URLs skip the writable-directory check entirely.
    """
    writer = skvideo.io.FFmpegWriter(
        "rtmp://example.invalid/live/stream",
        outputdict={"-f": "flv"},
    )
    # Don't call writeFrame — that would try to connect to the invalid
    # rtmp host. The wrapper-side guarantee is just "construction works".
    assert writer._dest_kind == "url"
    writer.close()


def test_ffmpegwriter_accepts_http_url_without_crashing():
    """Same guarantee for http:// destinations (PUT-style publish)."""
    writer = skvideo.io.FFmpegWriter(
        "http://example.invalid/upload.mp4",
        outputdict={"-method": "PUT", "-f": "mp4"},
    )
    assert writer._dest_kind == "url"
    writer.close()


def test_writer_url_skips_extension_assert():
    """URLs have no meaningful extension on the wrapper side; the encoder
    allowlist assertion must not fire (the URL might end in a path with
    no extension at all)."""
    # Would have failed previously: os.path.splitext on
    # 'rtmp://server/live/stream' yields extension '', which isn't in the
    # supported encoders allowlist.
    writer = skvideo.io.FFmpegWriter(
        "rtmp://server/live/stream",
        outputdict={"-f": "flv"},
    )
    assert writer.extension == ""  # documented as "" for non-file destinations
    writer.close()


def test_writer_rejects_bytesio_for_now():
    """Until commit 5 wires up BytesIO output, the wrapper should refuse
    cleanly rather than crash mid-init with a confusing error."""
    buf = _io.BytesIO()
    with pytest.raises(NotImplementedError, match="BytesIO"):
        skvideo.io.FFmpegWriter(buf)
