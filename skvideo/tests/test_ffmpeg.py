from numpy.testing import assert_equal
import os
import sys
import numpy as np
import skvideo.io
import skvideo.datasets


def test_FFmpegReader():
    reader = skvideo.io.FFmpegReader(skvideo.datasets.bigbuckbunny(), verbosity=0)
    
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


def test_FFmpegWriter():
    # generate random data for 5 frames
    outputfile = sys._getframe().f_code.co_name + ".mp4"

    outputdata = np.random.random(size=(5, 480, 640, 3)) * 255
    outputdata = outputdata.astype(np.uint8)

    writer = skvideo.io.FFmpegWriter(outputfile)
    for i in xrange(5):
        writer.writeFrame(outputdata[i])
    writer.close()
    os.remove(outputfile)
