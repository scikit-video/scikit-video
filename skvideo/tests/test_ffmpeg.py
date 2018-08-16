import os
import sys

import numpy as np
from numpy.testing import assert_equal

import skvideo.datasets
import skvideo.io

if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest


@unittest.skipIf(not skvideo._HAS_FFMPEG, "FFmpeg required for this test.")
def test_FFmpegReader():
    reader = skvideo.io.FFmpegReader(
        skvideo.datasets.bigbuckbunny(), verbosity=0)

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

    reader = skvideo.io.FFmpegReader(
        skvideo.datasets.bigbuckbunny(), verbosity=0)

    T = 0
    M = 0
    N = 0
    C = 0
    accumulation = 0

    for frame in reader:
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


@unittest.skipIf(not skvideo._HAS_FFMPEG, "FFmpeg required for this test.")
def test_FFmpegReader_16bits():
    reader16 = skvideo.io.FFmpegReader(skvideo.datasets.bigbuckbunny(), outputdict={
                                       '-pix_fmt': 'rgb48le'}, verbosity=0)
    reader8 = skvideo.io.FFmpegReader(skvideo.datasets.bigbuckbunny(), outputdict={
                                      '-pix_fmt': 'rgb24'}, verbosity=0)

    T = 0
    M = 0
    N = 0
    C = 0
    accumulation = 0

    for frame8, frame16 in zip(reader8.nextFrame(), reader16.nextFrame()):
        # testing with the measure module may be a better idea but would add a dependency

        # check that there is no more than a 3/256th defference between the 8bit and 16 bit decoded image
        assert(np.max(np.abs(frame8.astype('int32') -
                             (frame16//256).astype('int32'))) < 4)
        # then check that the mean difference is less than 1
        assert(np.mean(np.abs(frame8.astype('float32') -
                              (frame16//256).astype('float32'))) < 1.0)
        M, N, C = frame8.shape
        accumulation += np.sum(frame16//256)
        T += 1

    # check the dimensions of the video

    assert_equal(T, 132)
    assert_equal(M, 720)
    assert_equal(N, 1280)
    assert_equal(C, 3)

    # check the numbers : there's probably a better way to do this

    assert_equal(accumulation / (T * M * N * C), 108.89236060967751)


@unittest.skipIf(not skvideo._HAS_FFMPEG, "FFmpeg required for this test.")
def test_FFmpegReader_fps():
    reader = skvideo.io.FFmpegReader(skvideo.datasets.bigbuckbunny(), outputdict={
                                     "-r": "10"}, verbosity=0)

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

    assert_equal(T, 54)
    assert_equal(M, 720)
    assert_equal(N, 1280)
    assert_equal(C, 3)

    # check the numbers

    assert_equal(accumulation / (T * M * N * C), 109.16349342126415)


@unittest.skipIf(not skvideo._HAS_FFMPEG, "FFmpeg required for this test.")
def test_FFmpegWriter():
    # generate random data for 5 frames
    outputfile = sys._getframe().f_code.co_name + ".mp4"

    outputdata = np.random.random(size=(5, 480, 640, 3)) * 255
    outputdata = outputdata.astype(np.uint8)

    writer = skvideo.io.FFmpegWriter(outputfile)
    for i in range(5):
        writer.writeFrame(outputdata[i])
    writer.close()
    os.remove(outputfile)
