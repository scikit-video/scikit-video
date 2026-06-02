"""Tests for verbosity mode behavior (issue #174)."""
import subprocess

import skvideo.io
import skvideo.datasets


def test_reader_verbosity_starts_one_process(capsys):
    """FFmpegReader(verbosity=1) must start exactly one ffmpeg process.

    Previously the reader's _createProcess() ran Popen inside an
    `if verbosity > 0` branch and then *again* unconditionally outside it,
    leaking the first process and overwriting self._proc. The first process
    had stderr=None (visible) and the second had stderr=PIPE (captured),
    so verbosity=1 effectively suppressed its own output AND wasted a fork
    (issue #174).

    Test strategy: read a video with verbosity=1 and confirm reading succeeds
    (the leaked process bug surfaced as broken pipes for some users) and that
    the second process's setup matches what verbosity=1 promises — stderr=None.
    """
    reader = skvideo.io.FFmpegReader(skvideo.datasets.bigbuckbunny(), verbosity=1)
    # If the bug were present, self._proc would be the second (silent) Popen
    # with stderr piped. After the fix, verbosity=1 keeps stderr unredirected.
    assert reader._proc.stderr is None
    # Read a few frames to confirm the pipe actually works
    frames_read = 0
    for frame in reader.nextFrame():
        frames_read += 1
        if frames_read >= 3:
            break
    reader.close()
    assert frames_read == 3


def test_reader_verbosity_off_pipes_stderr():
    """Without verbosity, stderr should be captured (sp.PIPE)."""
    reader = skvideo.io.FFmpegReader(skvideo.datasets.bigbuckbunny(), verbosity=0)
    assert reader._proc.stderr is not None
    reader.close()
