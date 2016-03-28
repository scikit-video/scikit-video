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
