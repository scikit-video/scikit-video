from numpy.testing import assert_equal
import os
import sys
import numpy as np
import skvideo.io
import skvideo.datasets
import inspect

def test_FFmpegReader():
    reader = skvideo.io.FFmpegReader(skvideo.datasets.bigbuckbunny(), verbosity=1)
    
    t = 0
    h = 0
    w = 0
    c = 0
    accumulation = 0
    for frame in reader.nextFrame():
        h, w, c = frame.shape
        accumulation += np.sum(frame)
        t += 1

    # check the dimensions of the video

    assert_equal(t, 132)
    assert_equal(h, 720)
    assert_equal(w, 1280)
    assert_equal(c, 3)

    # check the numbers

    assert_equal(109.28332841215979, accumulation / (t * h * w * c))

def test_FFmpegWriter():
    # generate random data for 5 frames
    outputfile = sys._getframe().f_code.co_name + ".mp4"

    outputdata = np.random.random(size=(5, 480, 640, 3)) * 255
    outputdata = outputdata.astype(np.uint8)

    writer = skvideo.io.FFmpegWriter(outputfile, (5, 480, 640, 3))
    for i in xrange(5):
        writer.writeFrame(outputdata[i, :, :, :])
    writer.close()
    os.remove(outputfile)
