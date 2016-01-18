from numpy.testing import assert_equal
import os
import sys
import numpy as np
import skvideo.io
import skvideo.datasets


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
