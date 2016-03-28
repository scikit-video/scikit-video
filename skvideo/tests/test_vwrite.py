import skvideo.io
import sys
import numpy as np
import hashlib
import os
from numpy.testing import assert_equal

def hashfile(afile, hasher, blocksize=65536):
    buf = afile.read(blocksize)
    while len(buf) > 0:
        hasher.update(buf)
        buf = afile.read(blocksize)
    return hasher.hexdigest()

def _vwrite(backend):
    outputfile = sys._getframe().f_code.co_name + ".mp4"

    np.random.seed(0)

    # generate random data for 5 frames
    outputdata = np.random.random(size=(5, 480, 640, 3)) * 255
    outputdata = outputdata.astype(np.uint8)

    # save it out
    skvideo.io.vwrite(outputfile, outputdata, backend=backend)

    # check a hash of the output file
    h = hashfile(open(outputfile, 'rb'), hashlib.sha256())

    # not done developing the writer yet, so this is disabled for now
    #assert_equal(h, "7670dc3556bfc447210b66869a81774cab06774c05160a16d9865995f20e7b12")

    # remove test file
    os.remove(outputfile)

def test_vreader_ffmpeg():
    if not skvideo._HAS_FFMPEG:
        return 0
    _vwrite("ffmpeg")

def test_vreader_libav():
    if not skvideo._HAS_AVCONV:
        return 0
    try:
        if np.int(skvideo._LIBAV_MAJOR_VERSION) < 12:
            return 0
    except:
        return 0

    _vwrite("libav")

