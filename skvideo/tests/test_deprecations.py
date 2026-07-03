"""1.3.0-line deprecations and behavior fixes:

- libav/avconv backend and mediainfo/mprobe are deprecated (dead upstream,
  never CI-tested) -- one release of DeprecationWarning before removal.
- The hardcoded container-extension allowlist (a frozen snapshot of a
  2016-era ffmpeg's formats) now warns and defers to ffmpeg instead of
  rejecting extensions ffmpeg may well support (URL and BytesIO inputs
  always bypassed it anyway).
- Binaries are no longer resolved from the current working directory.
"""
import os
import shutil

import numpy as np
import pytest

import skvideo
import skvideo.datasets
import skvideo.io
import skvideo.utils


# --- libav / mediainfo deprecation -------------------------------------

def test_libav_reader_warns_deprecated():
    with pytest.warns(DeprecationWarning, match="libav"):
        try:
            skvideo.io.LibAVReader(skvideo.datasets.bigbuckbunny())
        except RuntimeError:
            pass  # avconv not installed; the warning must fire first


def test_libav_writer_warns_deprecated(tmp_path):
    with pytest.warns(DeprecationWarning, match="libav"):
        try:
            skvideo.io.LibAVWriter(str(tmp_path / "out.mp4"))
        except RuntimeError:
            pass


def test_setLibAVPath_warns_deprecated():
    import warnings
    with pytest.warns(DeprecationWarning, match="libav"):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            warnings.simplefilter("always", DeprecationWarning)
            skvideo.setLibAVPath("/nonexistent")


def test_mprobe_warns_deprecated():
    with pytest.warns(DeprecationWarning, match="mediainfo"):
        try:
            skvideo.io.mprobe(skvideo.datasets.bigbuckbunny())
        except RuntimeError:
            pass  # mediainfo not installed; the warning must fire first


# --- extension allowlist ------------------------------------------------

@pytest.mark.skipif(not skvideo._HAS_FFMPEG, reason="FFmpeg required")
def test_reader_unknown_extension_warns_and_reads(tmp_path):
    """ffmpeg detects container format from content, not extension. An
    extension missing from the frozen allowlist must warn and defer to
    ffmpeg, not hard-fail -- .avif etc. postdate the snapshot."""
    weird = str(tmp_path / "video.weirdext")
    shutil.copy(skvideo.datasets.bigbuckbunny(), weird)
    with pytest.warns(UserWarning, match="[Ee]xtension"):
        videodata = skvideo.io.vread(weird, num_frames=2)
    assert videodata.shape[0] == 2


@pytest.mark.skipif(not skvideo._HAS_FFMPEG, reason="FFmpeg required")
def test_writer_unknown_extension_warns_not_raises(tmp_path):
    """Writer construction with an unknown extension warns instead of
    raising; if ffmpeg really cannot infer a muxer, its own error now
    surfaces loudly at write/close time."""
    with pytest.warns(UserWarning, match="[Ee]xtension"):
        writer = skvideo.io.FFmpegWriter(str(tmp_path / "out.weirdext"))
    writer.close()


# --- no CWD binary resolution -------------------------------------------

def test_binaries_not_resolved_from_cwd(tmp_path, monkeypatch):
    """`import skvideo` must not execute an ffprobe found in the current
    working directory (hijack vector; no modern library resolves
    executables from CWD)."""
    fake = tmp_path / "fakebinary_skvideo_test"
    fake.write_text("#!/bin/sh\necho fake\n")
    fake.chmod(0o755)
    monkeypatch.chdir(tmp_path)
    matches = list(skvideo.utils.where("fakebinary_skvideo_test"))
    assert matches == [], (
        "binary resolved from CWD: %r" % matches)
