import warnings
warnings.filterwarnings('ignore', category=UserWarning)

from numpy.testing import assert_equal
import os
import sys
import numpy as np
import skvideo.io
import skvideo.datasets

if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest


@unittest.skipIf(not skvideo._HAS_FFMPEG, "FFmpeg required for this test.")
def test_FFmpeg_paths():
    current_path = skvideo.getFFmpegPath()
    current_version = skvideo.getFFmpegVersion()

    # check that version is not the default 0.0.0
    assert current_version != "0.0.0", "FFmpeg version not parsed."


    skvideo.setFFmpegPath("/")
    assert skvideo.getFFmpegVersion() == "0.0.0", "FFmpeg version is not zeroed out properly."
    assert current_path != skvideo.getFFmpegPath(), "FFmpeg path did not update correctly"


    # change path back
    skvideo.setFFmpegPath(current_path)

    # check that it worked
    assert current_path == skvideo.getFFmpegPath(), "FFmpeg path did not update correctly"
    assert skvideo.getFFmpegVersion() == current_version, "FFmpeg version is not loaded properly from valid FFmpeg."


@unittest.skipIf(not skvideo._HAS_FFMPEG, "FFmpeg required for this test.")
def test_getFFmpegVersion_is_clean_string():
    """getFFmpegVersion must return a real dotted version string (or an
    N-prefixed git-build string), never a repr of bytes like "b'8'.b'1'"."""
    version = skvideo.getFFmpegVersion()
    assert "b'" not in version, "bytes leaked into version string: %r" % version
    if not version.startswith("N"):
        for part in version.split("."):
            assert part.isdigit(), "non-numeric version component in %r" % version


def test_HAS_MEDIAINFO_matches_actual_binary():
    """_HAS_MEDIAINFO must be set only when the mediainfo binary actually
    exists. which() returns '' (not None) on a miss, so an `is not None`
    check marks mediainfo present on every system."""
    from skvideo.utils import where
    actually_present = len(where("mediainfo")) > 0
    assert bool(skvideo._HAS_MEDIAINFO) == actually_present, (
        "_HAS_MEDIAINFO=%r but mediainfo present=%r"
        % (skvideo._HAS_MEDIAINFO, actually_present))


@unittest.skipIf(not skvideo._HAS_AVCONV, "LibAV required for this test.")
def test_LibAV_paths():
    current_path = skvideo.getLibAVPath()
    current_version = skvideo.getLibAVVersion()

    # check that version is not the default 0.0
    assert current_version != "0.0", "LibAV version not parsed."

    skvideo.setLibAVPath("/")
    assert skvideo.getLibAVVersion() == "0.0", "LibAV version is not zeroed out properly."
    assert current_path != skvideo.getLibAVPath(), "LibAV path did not update correctly"

    # change path back
    skvideo.setLibAVPath(current_path)

    # check that it worked
    assert current_path == skvideo.getLibAVPath(), "LibAV path did not update correctly"
    assert skvideo.getLibAVVersion() == current_version, "LibAV version is not loaded properly from valid FFmpeg."


@unittest.skipIf(not skvideo._HAS_FFMPEG, "FFmpeg required for this test.")
def test_setFFmpegPath_takes_effect_after_io_import():
    """The io modules previously copied _HAS_FFMPEG/_FFMPEG_PATH via
    from-imports at import time, so setFFmpegPath() called after
    `import skvideo.io` silently did nothing -- the documented call
    order dependency this test pins down."""
    import skvideo.io  # noqa: F401 -- the import order IS the test

    original_path = skvideo.getFFmpegPath()
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            skvideo.setFFmpegPath("/nonexistent/skvideo/path")
        # vread checks the module-level flag; with the stale copy it
        # proceeded and failed much later inside a subprocess call.
        try:
            skvideo.io.vread(skvideo.datasets.bigbuckbunny(), num_frames=1)
            assert False, "vread must refuse to run without FFmpeg"
        except RuntimeError as e:
            assert "FFmpeg" in str(e) or "ffmpeg" in str(e)
    finally:
        skvideo.setFFmpegPath(original_path)

    # and the restore must also take effect
    videodata = skvideo.io.vread(skvideo.datasets.bigbuckbunny(), num_frames=1)
    assert videodata.shape[0] == 1
