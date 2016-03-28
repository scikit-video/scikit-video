from numpy.testing import assert_equal
import os
import sys
import numpy as np
import skvideo
import skvideo.io
import skvideo.datasets

if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest


@unittest.skipIf(not skvideo._HAS_AVCONV, "LibAV required for this test.")
def test_LibAVReader_aboveversion9():
    # skip if libav not installed or of the proper version
    if not skvideo._HAS_AVCONV:
        return 0
    if np.int(skvideo._LIBAV_MAJOR_VERSION) < 9:
        return 0

    reader = skvideo.io.LibAVReader(skvideo.datasets.bigbuckbunny(), verbosity=0)
    
    T = 0
    M = 0
    N = 0
    C = 0
    accumulation = 0
    for frame in reader.nextFrame():
        M, N, C = frame.shape
        accumulation += np.sum(frame)
        T += 1

    # check the dimensions of the video

    assert_equal(T, 132)
    assert_equal(M, 720)
    assert_equal(N, 1280)
    assert_equal(C, 3)

    # check the numbers

    assert_equal(accumulation / (T * M * N * C), 109.28332841215979)


@unittest.skipIf(not skvideo._HAS_AVCONV, "LibAV required for this test.")
def test_LibAVWriter_aboveversion9():
    # skip if libav not installed or of the proper version
    if not skvideo._HAS_AVCONV:
        return 0
    if np.int(skvideo._LIBAV_MAJOR_VERSION) < 9:
        return 0

    # generate random data for 5 frames
    outputfile = sys._getframe().f_code.co_name + ".mp4"

    outputdata = np.random.random(size=(5, 480, 640, 3)) * 255
    outputdata = outputdata.astype(np.uint8)

    writer = skvideo.io.LibAVWriter(outputfile)
    for i in range(5):
        writer.writeFrame(outputdata[i])
    writer.close()
    os.remove(outputfile)
