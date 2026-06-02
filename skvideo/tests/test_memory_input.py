"""Tests for BytesIO / file-like input support (issue #113)."""
import io
import os
from pathlib import Path

import numpy as np
import pytest

import skvideo.io
import skvideo.datasets


@pytest.fixture(scope="module")
def bunny_bytes():
    """The bigbuckbunny mp4 loaded fully into memory as bytes."""
    with open(skvideo.datasets.bigbuckbunny(), "rb") as fh:
        return fh.read()


def test_vread_from_bytesio(bunny_bytes):
    """vread() should accept a BytesIO of mp4 bytes and decode it."""
    buf = io.BytesIO(bunny_bytes)
    videodata = skvideo.io.vread(buf, num_frames=3)
    assert videodata.shape == (3, 720, 1280, 3)


def test_ffmpegreader_from_bytesio(bunny_bytes):
    """FFmpegReader directly should also accept BytesIO; previously
    crashed at os.path.getsize() / os.fspath() on the BytesIO object."""
    buf = io.BytesIO(bunny_bytes)
    reader = skvideo.io.FFmpegReader(buf)
    try:
        shape = reader.getShape()
        # Frame count comes from probe; height/width/channels are deterministic.
        assert shape[1:] == (720, 1280, 3)
    finally:
        reader.close()


def test_vreader_from_bytesio(bunny_bytes):
    """The generator API mirrors vread()."""
    buf = io.BytesIO(bunny_bytes)
    frames = []
    for frame in skvideo.io.vreader(buf, num_frames=2):
        frames.append(frame)
    assert len(frames) == 2
    assert frames[0].shape == (720, 1280, 3)


def test_bytesio_at_nonzero_position(bunny_bytes):
    """If the caller hands us a BytesIO with the cursor already advanced,
    we should still read from the start (we seek(0) internally)."""
    buf = io.BytesIO(bunny_bytes)
    buf.seek(1024)  # caller already consumed some bytes
    videodata = skvideo.io.vread(buf, num_frames=2)
    assert videodata.shape == (2, 720, 1280, 3)


def test_open_file_handle(tmp_path, bunny_bytes):
    """An open binary file handle works just like a BytesIO; its .name
    attribute should let us preserve the extension on the temp spool."""
    p = tmp_path / "video.mp4"
    p.write_bytes(bunny_bytes)
    with open(p, "rb") as fh:
        videodata = skvideo.io.vread(fh, num_frames=2)
    assert videodata.shape == (2, 720, 1280, 3)


def test_temp_file_cleaned_up_on_close(bunny_bytes):
    """The spooled temp file must be unlinked when the reader closes,
    otherwise long-running processes leak files into /tmp."""
    buf = io.BytesIO(bunny_bytes)
    reader = skvideo.io.FFmpegReader(buf)
    spooled_path = reader._temp_input_path
    assert spooled_path is not None
    assert Path(spooled_path).exists()
    reader.close()
    assert not Path(spooled_path).exists(), (
        "Spooled temp file %s still exists after close()" % spooled_path
    )


def test_file_path_does_not_create_temp_file(tmp_path, bunny_bytes):
    """Regression guard: a regular file path must NOT trigger spooling.
    _temp_input_path stays None so close() has nothing to unlink."""
    p = tmp_path / "video.mp4"
    p.write_bytes(bunny_bytes)
    reader = skvideo.io.FFmpegReader(str(p))
    try:
        assert reader._temp_input_path is None
    finally:
        reader.close()


def test_no_temp_leak_when_constructor_fails():
    """If the constructor raises after spooling (e.g. probe can't parse the
    bytes), the spooled temp file must still be cleaned up — the caller
    never gets a reference, so they can't call close() themselves.
    """
    import glob
    import tempfile as _tempfile

    # Use the system tempdir directly: macOS uses /var/folders/... not /tmp.
    tempdir = _tempfile.gettempdir()
    pattern = os.path.join(tempdir, "skvideo_in_*")

    junk = io.BytesIO(b"this is not a video file")
    before = set(glob.glob(pattern))
    with pytest.raises(Exception):
        skvideo.io.FFmpegReader(junk)
    after = set(glob.glob(pattern))
    leaked = after - before
    # Clean up any leak the test exposed so we don't litter the temp dir
    # across CI runs.
    for path in leaked:
        try:
            os.unlink(path)
        except OSError:
            pass
    assert not leaked, (
        "Constructor failure left %d temp file(s) behind: %s" % (
            len(leaked), sorted(leaked)
        )
    )


def test_write_only_input_rejected():
    """A file-like object without read() can't be an input source. Reject it
    with a clear TypeError up front rather than failing deep inside the
    spool copy with an opaque AttributeError (and leaking a temp file)."""
    class _WriteOnly:
        def write(self, b):
            return len(b)
    with pytest.raises(TypeError, match="readable"):
        skvideo.io.FFmpegReader(_WriteOnly())


def test_write_mode_file_handle_rejected(tmp_path):
    """A real file opened in write mode ("wb") exposes a .read attribute
    that raises io.UnsupportedOperation when called, so a plain
    hasattr("read") check would pass it and then fail deep in the spool
    copy. The readable() probe must reject it up front with a TypeError."""
    p = tmp_path / "out.mp4"
    with open(p, "wb") as wb:
        with pytest.raises(TypeError, match="readable"):
            skvideo.io.FFmpegReader(wb)


def test_no_temp_leak_when_source_read_fails():
    """If source.read() raises partway through spooling, the temp file must
    be unlinked before the exception propagates."""
    import glob
    import tempfile as _tempfile

    pattern = os.path.join(_tempfile.gettempdir(), "skvideo_in_*")

    class _Boom:
        def read(self, n=-1):
            raise IOError("simulated read failure")

    before = set(glob.glob(pattern))
    with pytest.raises(Exception):
        skvideo.io.FFmpegReader(_Boom())
    after = set(glob.glob(pattern))
    leaked = after - before
    for path in leaked:
        try:
            os.unlink(path)
        except OSError:
            pass
    assert not leaked, "Spool read failure leaked: %s" % sorted(leaked)


def test_vread_cleans_spool_on_read_error(bunny_bytes, monkeypatch):
    """vread() must close the reader even if frame reading raises mid-loop,
    so a spooled BytesIO temp file is unlinked (the read path is wrapped in
    try/finally)."""
    import glob
    import tempfile as _tempfile

    pattern = os.path.join(_tempfile.gettempdir(), "skvideo_in_*")

    def boom(self):
        raise RuntimeError("simulated mid-read failure")
        yield  # pragma: no cover  (makes this a generator)

    monkeypatch.setattr(skvideo.io.FFmpegReader, "nextFrame", boom)
    before = set(glob.glob(pattern))
    with pytest.raises(RuntimeError):
        skvideo.io.vread(io.BytesIO(bunny_bytes))
    after = set(glob.glob(pattern))
    leaked = after - before
    for path in leaked:
        try:
            os.unlink(path)
        except OSError:
            pass
    assert not leaked, "vread read failure leaked spool: %s" % sorted(leaked)
