"""Reader end-of-stream integrity: a decode failure mid-read must surface
as an exception, not as a silently shorter video (the writer got this
guarantee in issue #111; these tests pin the reader side). Also covers
vread() of inputs whose frame count cannot be probed."""
import numpy as np
import pytest

import skvideo
import skvideo.datasets
import skvideo.io

pytestmark = pytest.mark.skipif(
    not skvideo._HAS_FFMPEG, reason="FFmpeg required for these tests.")


def test_reader_raises_when_ffmpeg_dies_midstream():
    """If the ffmpeg process dies partway through (decode error, OOM-kill,
    dropped network source), iteration must raise instead of ending the
    generator early -- the caller cannot distinguish a truncated result
    from a legitimately shorter video."""
    reader = skvideo.io.FFmpegReader(skvideo.datasets.bigbuckbunny())
    try:
        gen = reader.nextFrame()
        frame = next(gen)
        assert frame.shape[2] == 3
        reader._proc.kill()  # simulate mid-stream death
        with pytest.raises(RuntimeError, match="[Ff][Ff]mpeg"):
            for _ in gen:
                pass
    finally:
        reader.close()


def test_reader_clean_eof_still_silent():
    """A normal full read must NOT raise from the new exit-status check."""
    videodata = skvideo.io.vread(skvideo.datasets.bigbuckbunny(), num_frames=3)
    assert videodata.shape[0] == 3


def test_vread_with_unknown_frame_count_collects_frames(monkeypatch):
    """When the frame count cannot be probed (URL/stream inputs),
    getShape() reports T=0. vread previously allocated np.empty((0,...))
    and crashed with IndexError on the first frame; it must instead
    collect the frames it reads."""
    import skvideo.io.io as io_mod
    RealReader = io_mod.FFmpegReader

    class UnknownCountReader(RealReader):
        def getShape(self):
            T, M, N, C = RealReader.getShape(self)
            return 0, M, N, C

    monkeypatch.setattr(io_mod, "FFmpegReader", UnknownCountReader)
    videodata = skvideo.io.vread(skvideo.datasets.bigbuckbunny(), num_frames=3)
    assert videodata.shape[0] == 3
    assert videodata.shape[3] == 3
    assert np.any(videodata)  # actual decoded content, not zeros
