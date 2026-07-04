"""Tests for FFmpeg/LibAV not-found warning message clarity (issue #159)."""
import warnings


import skvideo


def test_ffmpeg_warning_mentions_binaries_not_modules():
    """When setFFmpegPath points at a directory without the ffmpeg binary,
    the warning must say 'binaries', not just 'ffmpeg/ffprobe' — issue #159
    flagged that users misread the old warning as referring to the
    skvideo/io/ffmpeg.py wrapper module.
    """
    original_path = skvideo.getFFmpegPath()
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            skvideo.setFFmpegPath("/")
        msgs = [str(w.message) for w in caught if issubclass(w.category, UserWarning)]
        assert msgs, "Expected a UserWarning for missing FFmpeg binaries"
        msg = msgs[-1]
        assert "binaries" in msg.lower(), (
            "Warning should say 'binaries' to distinguish from Python modules: %r" % msg
        )
        # Should also point users at the fix path
        assert "setFFmpegPath" in msg
    finally:
        skvideo.setFFmpegPath(original_path)


def test_libav_warning_mentions_binaries_not_modules():
    """Same as above for LibAV (issue #159 fix applied for symmetry)."""
    original_path = skvideo.getLibAVPath()
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            skvideo.setLibAVPath("/")
        msgs = [str(w.message) for w in caught if issubclass(w.category, UserWarning)]
        assert msgs, "Expected a UserWarning for missing LibAV binaries"
        msg = msgs[-1]
        assert "binaries" in msg.lower(), (
            "Warning should say 'binaries' to distinguish from Python modules: %r" % msg
        )
        assert "setLibAVPath" in msg
    finally:
        skvideo.setLibAVPath(original_path)
