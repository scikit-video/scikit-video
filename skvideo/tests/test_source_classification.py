"""Tests for the input/output source classifier (issues #117, #113, #81)."""
import io
from pathlib import Path

import pytest

from skvideo.io.abstract import _classify_source


# --- "file" category ---------------------------------------------------------

def test_plain_string_filename_is_file():
    assert _classify_source("video.mp4") == "file"


def test_string_with_directory_is_file():
    assert _classify_source("/tmp/clip.mov") == "file"


def test_pathlib_path_is_file():
    assert _classify_source(Path("/tmp/clip.mov")) == "file"


def test_windows_drive_letter_is_file():
    # Strict URL regex requires `<scheme>://`. `C:\foo.mp4` has no slashes,
    # so it must not be mistaken for a URL.
    assert _classify_source(r"C:\videos\clip.mp4") == "file"


def test_relative_filename_is_file():
    assert _classify_source("clip.mp4") == "file"


# --- "url" category ----------------------------------------------------------

@pytest.mark.parametrize("url", [
    "http://example.com/video.mp4",
    "https://example.com/video.mp4",
    "rtsp://camera.local:554/stream",
    "rtmp://server/live/key",
    "rtmps://server/live/key",
    "udp://127.0.0.1:1234",
    "tcp://127.0.0.1:1234",
    "ftp://example.com/clip.mp4",
    "sftp://example.com/clip.mp4",
    "srt://server:9000",
    "hls://example.com/stream.m3u8",
])
def test_known_url_schemes_classify_as_url(url):
    assert _classify_source(url) == "url"


# --- "memory" category -------------------------------------------------------

def test_bytesio_is_memory():
    assert _classify_source(io.BytesIO(b"some bytes")) == "memory"


def test_open_file_handle_is_memory():
    """An already-open file handle (has read()) classifies as memory."""
    with open(__file__, "rb") as fh:
        assert _classify_source(fh) == "memory"


def test_bytesio_for_writing_is_memory():
    """A BytesIO opened for writing also classifies as memory (has write())."""
    buf = io.BytesIO()
    assert _classify_source(buf) == "memory"


# --- edge cases --------------------------------------------------------------

def test_empty_string_is_file():
    """Defer to existing error handling; don't mis-classify."""
    assert _classify_source("") == "file"
