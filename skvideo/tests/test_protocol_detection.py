"""Tests for ffmpeg protocol detection + warning (v1.1.14).

After Codex round 1 the cache moved from two separate globals
(_FFMPEG_INPUT_PROTOCOLS, _FFMPEG_OUTPUT_PROTOCOLS) to a single atomic
tuple (_FFMPEG_PROTOCOLS = (inputs, outputs)) so concurrent readers
can't observe one half populated and the other half None.
"""
import warnings


import skvideo


# --- parser unit tests -------------------------------------------------------

def test_parser_extracts_input_and_output_protocols(monkeypatch):
    """Parse a representative `ffmpeg -protocols` payload and confirm
    both sections are extracted."""
    fake_output = (
        b"Supported file protocols:\n"
        b"Input:\n"
        b"  file\n"
        b"  http\n"
        b"  https\n"
        b"  pipe\n"
        b"  rtsp\n"
        b"Output:\n"
        b"  file\n"
        b"  http\n"
        b"  md5\n"
        b"  pipe\n"
    )
    monkeypatch.setattr(skvideo, "_FFMPEG_PROTOCOLS", None)
    monkeypatch.setattr(skvideo, "check_output", lambda *a, **k: fake_output)

    inputs, outputs = skvideo._get_ffmpeg_protocols()
    assert set(inputs) == {"file", "http", "https", "pipe", "rtsp"}
    assert set(outputs) == {"file", "http", "md5", "pipe"}


def test_parser_caches_result(monkeypatch):
    """Second call should NOT re-invoke check_output (lazy cache)."""
    call_count = {"n": 0}

    def fake_check_output(*a, **k):
        call_count["n"] += 1
        return b"Supported file protocols:\nInput:\n  file\nOutput:\n  file\n"

    monkeypatch.setattr(skvideo, "_FFMPEG_PROTOCOLS", None)
    monkeypatch.setattr(skvideo, "check_output", fake_check_output)

    skvideo._get_ffmpeg_protocols()
    skvideo._get_ffmpeg_protocols()
    skvideo._get_ffmpeg_protocols()
    assert call_count["n"] == 1, "expected one cached invocation, got %d" % call_count["n"]


def test_parser_handles_detection_failure(monkeypatch):
    """If check_output raises, return empty lists rather than propagating."""
    def boom(*a, **k):
        raise OSError("ffmpeg crashed")

    monkeypatch.setattr(skvideo, "_FFMPEG_PROTOCOLS", None)
    monkeypatch.setattr(skvideo, "check_output", boom)

    inputs, outputs = skvideo._get_ffmpeg_protocols()
    assert inputs == []
    assert outputs == []


def test_cache_is_atomic_tuple(monkeypatch):
    """Codex round 1: when the cache gets populated it must be a single
    tuple assignment, not two separate writes. Otherwise a concurrent
    reader can see inputs set and outputs still None.

    We can't easily reproduce the race in a single-threaded test, but
    we can verify the post-detection state has exactly one published
    cache object (the tuple), not two separate attributes.
    """
    monkeypatch.setattr(skvideo, "_FFMPEG_PROTOCOLS", None)
    monkeypatch.setattr(
        skvideo, "check_output",
        lambda *a, **k: b"Input:\n  file\nOutput:\n  file\n"
    )
    skvideo._get_ffmpeg_protocols()
    assert isinstance(skvideo._FFMPEG_PROTOCOLS, tuple)
    assert len(skvideo._FFMPEG_PROTOCOLS) == 2


# --- warn behavior tests -----------------------------------------------------

def test_warn_fires_for_unsupported_scheme(monkeypatch):
    """When the URL scheme isn't in the supported list, a UserWarning fires."""
    monkeypatch.setattr(skvideo, "_FFMPEG_PROTOCOLS", (["file", "http", "pipe"], ["file", "pipe"]))

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        skvideo._warn_if_unsupported_protocol("https://example.com/x.mp4", "input")

    msgs = [str(w.message) for w in caught if issubclass(w.category, UserWarning)]
    assert msgs, "Expected a UserWarning for unsupported https scheme"
    assert "https" in msgs[0]
    assert "input" in msgs[0]


def test_warn_silent_for_supported_scheme(monkeypatch):
    """No warning when the scheme is in the list."""
    monkeypatch.setattr(skvideo, "_FFMPEG_PROTOCOLS", (["file", "http", "https"], ["file"]))

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        skvideo._warn_if_unsupported_protocol("https://example.com/x.mp4", "input")

    user_warnings = [w for w in caught if issubclass(w.category, UserWarning)]
    assert not user_warnings, "Did not expect warning; got %r" % user_warnings


def test_warn_silent_when_detection_failed(monkeypatch):
    """Empty protocol list = detection failed; don't preempt ffmpeg's error."""
    monkeypatch.setattr(skvideo, "_FFMPEG_PROTOCOLS", ([], []))

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        skvideo._warn_if_unsupported_protocol("https://example.com/x.mp4", "input")

    user_warnings = [w for w in caught if issubclass(w.category, UserWarning)]
    assert not user_warnings


def test_warn_silent_for_non_url(monkeypatch):
    """Plain filenames (no `://`) don't trigger the URL warning."""
    monkeypatch.setattr(skvideo, "_FFMPEG_PROTOCOLS", (["file"], ["file"]))

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        skvideo._warn_if_unsupported_protocol("/tmp/video.mp4", "input")
        skvideo._warn_if_unsupported_protocol("video.mp4", "input")

    user_warnings = [w for w in caught if issubclass(w.category, UserWarning)]
    assert not user_warnings


def test_warn_input_vs_output_independent(monkeypatch):
    """A scheme supported as output but not input should warn for input only."""
    monkeypatch.setattr(skvideo, "_FFMPEG_PROTOCOLS", (["file"], ["file", "md5"]))

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        skvideo._warn_if_unsupported_protocol("md5://output.bin", "input")
        skvideo._warn_if_unsupported_protocol("md5://output.bin", "output")

    msgs = [str(w.message) for w in caught if issubclass(w.category, UserWarning)]
    assert len(msgs) == 1, "Expected exactly one warning (input only); got %d" % len(msgs)
    assert "input" in msgs[0]


# --- integration with setFFmpegPath ------------------------------------------

def test_setffmpegpath_invalidates_protocol_cache(monkeypatch):
    """A new ffmpeg binary may have different compiled-in protocols, so
    setFFmpegPath must clear the cache."""
    monkeypatch.setattr(skvideo, "_FFMPEG_PROTOCOLS", (["file"], ["file"]))

    original_path = skvideo.getFFmpegPath()
    try:
        skvideo.setFFmpegPath("/")  # any path; we just need the cache reset
        assert skvideo._FFMPEG_PROTOCOLS is None
    finally:
        skvideo.setFFmpegPath(original_path)
