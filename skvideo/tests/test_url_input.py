"""Tests for URL input support (issues #117, #81).

Uses a local Range-aware HTTP server fixture so we don't depend on external
network. Python's stdlib SimpleHTTPRequestHandler does NOT implement the
Range header, which ffmpeg's HTTP reader requires to seek the mp4 moov atom —
without proper Range support ffmpeg gets "partial file" errors and silently
returns empty frames.
"""
import http.server
import os
import socketserver
import threading

import pytest

import skvideo.io
import skvideo.datasets


class _RangeHandler(http.server.SimpleHTTPRequestHandler):
    """SimpleHTTPRequestHandler + minimal RFC 7233 Range support.

    Enough to satisfy ffmpeg's HTTP demuxer (single byte-range form
    `Range: bytes=START-END` or `Range: bytes=START-`). Returns 206
    Partial Content for valid ranges, falls back to the parent's 200
    response when no Range header is present.
    """

    def log_message(self, format, *args):  # silence per-request logs
        pass

    def send_head(self):
        rng = self.headers.get("Range")
        if not rng or not rng.startswith("bytes="):
            return super().send_head()
        # Parse "bytes=START-END" (END optional)
        try:
            start_s, end_s = rng[len("bytes="):].split("-", 1)
            start = int(start_s)
            path = self.translate_path(self.path)
            size = os.path.getsize(path)
            end = int(end_s) if end_s else size - 1
            if start >= size or end >= size or start > end:
                self.send_error(416, "Requested Range Not Satisfiable")
                return None
            length = end - start + 1
            f = open(path, "rb")
            f.seek(start)
            self.send_response(206)
            self.send_header("Content-Type", self.guess_type(path))
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Range", "bytes %d-%d/%d" % (start, end, size))
            self.send_header("Content-Length", str(length))
            self.end_headers()
            # Stream just the requested slice. Parent's copyfile reads until EOF;
            # we cap at `length` bytes manually.
            try:
                remaining = length
                while remaining > 0:
                    chunk = f.read(min(64 * 1024, remaining))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    remaining -= len(chunk)
            finally:
                f.close()
            return None  # we already wrote the body
        except (ValueError, OSError):
            self.send_error(400, "Bad Range header")
            return None


@pytest.fixture(scope="module")
def local_http_server():
    """Serve skvideo's datasets directory on a free port with Range support.

    Yields the base URL (e.g. http://127.0.0.1:38123/). Skips if no port can
    be bound (rare; happens on locked-down CI).
    """
    datasets_dir = os.path.dirname(skvideo.datasets.bigbuckbunny())

    class _Handler(_RangeHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=datasets_dir, **kwargs)

    try:
        # ThreadingTCPServer: ffmpeg may issue multiple concurrent Range
        # requests; a single-threaded server stalls them.
        server = socketserver.ThreadingTCPServer(("127.0.0.1", 0), _Handler)
        server.daemon_threads = True
    except OSError as exc:
        pytest.skip("Could not bind local HTTP server: %s" % exc)

    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield "http://127.0.0.1:%d/" % port
    finally:
        server.shutdown()
        server.server_close()


def test_vread_accepts_http_url(local_http_server):
    """vread() with an http:// URL should download via ffmpeg and decode."""
    url = local_http_server + "bigbuckbunny.mp4"
    videodata = skvideo.io.vread(url, num_frames=3)
    assert videodata.shape == (3, 720, 1280, 3)


def test_ffmpegreader_accepts_http_url(local_http_server):
    """FFmpegReader directly should also work; previously crashed on
    os.path.getsize() at abstract.py:79.
    """
    url = local_http_server + "bigbuckbunny.mp4"
    reader = skvideo.io.FFmpegReader(url)
    try:
        shape = reader.getShape()
        assert shape[1:] == (720, 1280, 3)  # H, W, C — frame count may vary
        # Read up to a few frames to confirm the pipe works. Use for-break
        # rather than next() to avoid PEP 479 StopIteration RuntimeError if
        # the URL is treated as a webcam-style stream (inputframenum=0).
        first_frame = None
        for frame in reader.nextFrame():
            first_frame = frame
            break
        assert first_frame is not None, "Reader yielded no frames"
        assert first_frame.shape == (720, 1280, 3)
    finally:
        reader.close()


def test_ffprobe_accepts_http_url(local_http_server):
    """ffprobe natively supports http; verify our wrapper doesn't break that."""
    url = local_http_server + "bigbuckbunny.mp4"
    info = skvideo.io.ffprobe(url)
    assert info != {}, "ffprobe returned empty for valid http URL"
    assert "video" in info
