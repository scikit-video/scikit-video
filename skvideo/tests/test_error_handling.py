"""Library code must raise exceptions, not return non-exception singletons
or call exit() (which would kill the host process)."""
import importlib

import numpy as np
import pytest

import skvideo.utils

# The function `niqe` shadows the `niqe` submodule in skvideo.measure's
# namespace, so import the modules explicitly to reach their helpers.
_niqe_mod = importlib.import_module("skvideo.measure.niqe")
_vbliinds_mod = importlib.import_module("skvideo.measure.videobliinds")


def test_rgb2gray_rejects_alpha_with_real_exception():
    # Previously `raise NotImplemented` (the singleton), which itself
    # raises "TypeError: exceptions must derive from BaseException".
    rgba = np.zeros((1, 16, 16, 4), dtype=np.uint8)
    with pytest.raises(NotImplementedError):
        skvideo.utils.rgb2gray(rgba)


def test_niqe_patches_raises_on_small_image_instead_of_exit():
    # _get_patches_generic used exit(0) on an undersized image, terminating
    # the caller's process. It must raise instead.
    tiny = np.zeros((4, 4), dtype=np.float32)
    with pytest.raises(ValueError):
        _niqe_mod._get_patches_generic(tiny, 96, 0, 1)


def test_videobliinds_computequality_raises_on_small_frame_instead_of_exit():
    tiny = np.zeros((4, 4, 1), dtype=np.float32)
    with pytest.raises(ValueError):
        _vbliinds_mod.computequality(tiny, 96, 96, None, None)


def test_input_validation_survives_O_optimization():
    """Public input validation must use real exceptions, not `assert`, so it
    is not stripped under `python -O`. Previously `mse` asserted on the
    channel count; under -O that vanished and mse returned [0.] for RGB."""
    import subprocess
    import sys

    code = (
        "import numpy as np, skvideo.measure as m\n"
        "rgb = np.zeros((2, 16, 16, 3))\n"
        "try:\n"
        "    m.mse(rgb, rgb)\n"
        "    print('NORAISE')\n"
        "except ValueError:\n"
        "    print('VALUEERROR')\n"
    )
    out = subprocess.run(
        [sys.executable, "-O", "-c", code],
        capture_output=True, text=True,
    )
    assert "VALUEERROR" in out.stdout, (
        "mse did not raise under -O; stdout=%r stderr=%r"
        % (out.stdout, out.stderr[-200:])
    )


def test_ffprobe_warns_on_unparseable_file(tmp_path):
    """ffprobe returning {} is load-bearing for raw video, but it must no
    longer do so silently: an unparseable file should emit a UserWarning
    explaining why, rather than vanishing behind a later generic error."""
    import skvideo.io
    bogus = tmp_path / "not_a_video.mp4"
    bogus.write_bytes(b"this is plainly not a media file")
    with pytest.warns(UserWarning):
        info = skvideo.io.ffprobe(str(bogus))
    assert info == {}


def test_fullref_metric_rejects_shape_mismatch():
    """Full-reference metrics must reject mismatched ref/dis shapes with a
    real exception (was a bare `assert`, stripped under -O where mismatched
    arrays broadcast to a plausible-but-wrong score)."""
    import skvideo.measure as M
    a = np.zeros((2, 16, 16, 1))
    b = np.zeros((3, 16, 16, 1))
    for fn in (M.mse, M.mae, M.psnr):
        with pytest.raises(ValueError):
            fn(a, b)


def test_fullref_shape_mismatch_survives_O():
    import subprocess, sys
    code = (
        "import numpy as np, skvideo.measure as m\n"
        "try:\n"
        "    m.mse(np.zeros((2,16,16,1)), np.zeros((3,16,16,1)))\n"
        "    print('NORAISE')\n"
        "except ValueError:\n"
        "    print('VALUEERROR')\n"
    )
    out = subprocess.run([sys.executable, "-O", "-c", code], capture_output=True, text=True)
    assert "VALUEERROR" in out.stdout, (out.stdout, out.stderr[-200:])


def test_blockcomp_nondivisible_dims_pass_through_remainder():
    """A frame whose dimensions aren't a multiple of mbSize (e.g. 1080/16)
    must not have its uncovered border silently zeroed; the remainder passes
    through instead."""
    import skvideo.motion as MO
    frame = np.ones((17, 17, 1)) * 7.0
    vid = np.stack([frame, frame])
    mv = np.zeros((1, 17 // 8, 17 // 8, 2), dtype=np.int64)
    comp = MO.blockComp(vid, mv, mbSize=8)
    # bottom row (index 16) is outside any whole 8x8 block -> must be 7, not 0
    assert comp[1, 16, :, 0].min() == 7.0


def test_blockcomp_single_frame_does_not_crash():
    import skvideo.motion as MO
    out = MO.blockComp(np.ones((16, 16, 1)), np.zeros((2, 2, 2), dtype=np.int64), mbSize=8)
    # single-frame result is (1, M, N, C), consistent with the multi-frame path
    assert out.shape == (1, 16, 16, 1)


def test_blockcomp_rejects_mismatched_motion_grid():
    """A motion-vector grid that doesn't match the macroblock grid must raise
    a clear ValueError, not a cryptic IndexError (too small) or silently
    ignore extra vectors (too large)."""
    import skvideo.motion as MO
    frame = np.ones((16, 16, 1))  # 2x2 macroblock grid at mbSize=8
    vid = np.stack([frame, frame])
    with pytest.raises(ValueError):
        MO.blockComp(vid, np.zeros((1, 1, 1, 2), dtype=np.int64), mbSize=8)
    with pytest.raises(ValueError):
        MO.blockComp(vid, np.zeros((1, 3, 3, 2), dtype=np.int64), mbSize=8)


def test_globalEdgeMotion_blank_frames_report_no_motion():
    import skvideo.motion as MO
    z = np.zeros((40, 40), np.float32)
    assert list(MO.globalEdgeMotion(z, z, method="hamming")) == [0, 0]
    assert list(MO.globalEdgeMotion(z, z, method="hausdorff")) == [0, 0]


def test_vwrite_rejects_zero_frames(tmp_path):
    import skvideo.io
    with pytest.raises(ValueError):
        skvideo.io.vwrite(str(tmp_path / "empty.mp4"), np.empty((0, 16, 16, 3)))


def test_blockcomp_rejects_malformed_vector_rank():
    """blockComp must reject motion vectors whose last dimension isn't 2
    (or that are rank-2) with a clear ValueError, not a cryptic IndexError
    / silent ignore of extra components."""
    import skvideo.motion as MO
    frame = np.ones((16, 16, 1))  # single frame -> _subcomp gets motionVect directly
    for bad in [(2, 2), (2, 2, 1), (2, 2, 3)]:
        with pytest.raises(ValueError):
            MO.blockComp(frame, np.zeros(bad, dtype=np.int64), mbSize=8)
    # the correct shape still works
    ok = MO.blockComp(frame, np.zeros((2, 2, 2), dtype=np.int64), mbSize=8)
    assert ok.shape == (1, 16, 16, 1)


def test_bytesio_writer_close_emits_no_resourcewarning():
    """Closing a BytesIO writer must not leak ffmpeg pipe file objects
    (previously emitted ResourceWarning: unclosed file per writer)."""
    import io as _io
    import warnings
    import skvideo.io
    with warnings.catch_warnings():
        warnings.simplefilter("error", ResourceWarning)
        buf = _io.BytesIO()
        w = skvideo.io.FFmpegWriter(buf, inputdict={"-r": "5"}, outputdict={"-f": "mp4"})
        for _ in range(3):
            w.writeFrame(np.zeros((16, 16, 3), dtype=np.uint8))
        w.close()  # must not raise ResourceWarning


def test_setffmpegpath_bad_path_clears_codec_caches():
    """A bad setFFmpegPath must not leave stale decoder/encoder lists from a
    previously valid binary (half-configured state)."""
    import skvideo
    orig = skvideo._FFMPEG_PATH
    try:
        skvideo.setFFmpegPath("/nonexistent/skvideo/path")
        assert skvideo._HAS_FFMPEG == 0
        assert skvideo._FFMPEG_SUPPORTED_DECODERS == []
        assert skvideo._FFMPEG_SUPPORTED_ENCODERS == []
    finally:
        skvideo.setFFmpegPath(orig)  # restore for the rest of the session
    assert skvideo._HAS_FFMPEG == 1


def test_backend_missing_raises_runtimeerror_under_O():
    """Backend-availability checks must be real exceptions, not asserts, so a
    missing ffmpeg is reported even under `python -O` (where asserts vanish)."""
    import subprocess
    import sys
    code = (
        "import importlib\n"
        "m = importlib.import_module('skvideo.io.ffprobe')\n"
        "m._HAS_FFMPEG = 0\n"   # simulate ffmpeg not installed
        "try:\n"
        "    m.ffprobe('whatever.mp4')\n"
        "    print('NORAISE')\n"
        "except RuntimeError:\n"
        "    print('RUNTIMEERROR')\n"
    )
    out = subprocess.run([sys.executable, "-O", "-c", code], capture_output=True, text=True)
    assert "RUNTIMEERROR" in out.stdout, (out.stdout, out.stderr[-200:])


def test_ssim_rejects_too_small_frames():
    """ssim / ssim_full on frames smaller than the 11x11 window silently
    returned NaN (the map trims to empty); both must raise ValueError."""
    import skvideo.measure as M
    tiny = np.zeros((2, 8, 8, 1), dtype=np.uint8)
    with pytest.raises(ValueError):
        M.ssim(tiny, tiny)
    with pytest.raises(ValueError):
        M.ssim_full(tiny, tiny)
