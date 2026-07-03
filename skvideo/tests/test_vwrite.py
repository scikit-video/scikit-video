import skvideo.io
import sys
import numpy as np
import os

def _vwrite(backend):
    outputfile = sys._getframe().f_code.co_name + ".mp4"

    np.random.seed(0)

    # generate random data for 5 frames
    outputdata = np.random.random(size=(5, 480, 640, 3)) * 255
    outputdata = outputdata.astype(np.uint8)

    # save it out
    skvideo.io.vwrite(outputfile, outputdata, backend=backend)

    # encoded bytes are ffmpeg-version-dependent, so no content hash;
    # a non-empty output is the invariant
    assert os.path.getsize(outputfile) > 0

    # remove test file
    os.remove(outputfile)

def test_vreader_ffmpeg():
    if not skvideo._HAS_FFMPEG:
        return
    _vwrite("ffmpeg")

def test_vreader_libav():
    if not skvideo._HAS_AVCONV:
        return
    try:
        if int(skvideo._LIBAV_MAJOR_VERSION) < 12:
            return
    except:
        return

    _vwrite("libav")

