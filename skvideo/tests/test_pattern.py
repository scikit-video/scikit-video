import skvideo.io
import skvideo.utils
import numpy as np
import os
import sys

if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest


def pattern_sinusoid(backend):
    # write out a sine wave
    sinusoid1d = np.zeros((100, 100))

    for i in range(100):
        sinusoid1d[i, :] = 127*np.sin(2 * np.pi * i / 100) + 128

    skvideo.io.vwrite("sinusoid1d.yuv", sinusoid1d)

    # load it and resave it to check the pipeline for drift
    videoData1 = skvideo.io.vread("sinusoid1d.yuv", width=100, height=100)

    skvideo.io.vwrite("sinusoid1d_resaved.yuv", videoData1)
    videoData2 = skvideo.io.vread("sinusoid1d_resaved.yuv", width=100, height=100)

    # check slices
    sinusoidDataOriginal = np.array(sinusoid1d[:, 1])
    sinusoidDataVideo1 = skvideo.utils.rgb2gray(videoData1[0])[0, :, 1, 0]
    sinusoidDataVideo2 = skvideo.utils.rgb2gray(videoData2[0])[0, :, 1, 0]

    # check that the mean squared error is within 1 pixel
    floattopixel_mse = np.mean((sinusoidDataOriginal-sinusoidDataVideo1)**2)
    assert floattopixel_mse < 1, "Possible conversion error between floating point and raw video. MSE=%f" % (floattopixel_mse,)

    # check that saving and loading a loaded file is identical
    pixeltopixel_mse = np.mean((sinusoidDataVideo1-sinusoidDataVideo2)**2)
    assert pixeltopixel_mse == 0, "Creeping error inside vread/vwrite."
    os.remove("sinusoid1d.yuv")
    os.remove("sinusoid1d_resaved.yuv")


def pattern_noise(backend):
    np.random.seed(1)
    # write out random data
    randomNoiseData = np.random.random((100, 100))*255
    randomNoiseData[0, 0] = 0
    randomNoiseData[0, 1] = 1
    randomNoiseData[0, 2] = 255

    skvideo.io.vwrite("randomNoisePattern.yuv", randomNoiseData, backend=backend)

    # load it and resave it to check the pipeline for drift
    videoData1 = skvideo.io.vread("randomNoisePattern.yuv", width=100, height=100, backend=backend)

    skvideo.io.vwrite("randomNoisePattern_resaved.yuv", videoData1, backend=backend)
    videoData2 = skvideo.io.vread("randomNoisePattern_resaved.yuv", width=100, height=100, backend=backend)

    # check slices
    randomDataOriginal = np.array(randomNoiseData)
    randomDataVideo1 = skvideo.utils.rgb2gray(videoData1[0])[0, :, :, 0]
    randomDataVideo2 = skvideo.utils.rgb2gray(videoData2[0])[0, :, :, 0]

    # check that the mean squared error is within 1 pixel
    floattopixel_mse = np.mean((randomDataOriginal-randomDataVideo1)**2)
    assert floattopixel_mse < 1, "Possible conversion error between floating point and raw video. MSE=%f" % (floattopixel_mse,)

    # check that saving and loading a loaded file is identical
    pixeltopixel_mse = np.mean((randomDataVideo1-randomDataVideo2)**2)
    assert pixeltopixel_mse == 0, "Creeping error inside vread/vwrite."

    os.remove("randomNoisePattern.yuv")
    os.remove("randomNoisePattern_resaved.yuv")


@unittest.skipIf(not skvideo._HAS_FFMPEG, "FFmpeg required for this test.")
def test_sinusoid_ffmpeg():
    pattern_sinusoid('ffmpeg')


@unittest.skipIf(not skvideo._HAS_AVCONV, "LibAV required for this test.")
def test_sinusoid_libav():
    pattern_sinusoid('libav')


@unittest.skipIf(not skvideo._HAS_FFMPEG, "FFmpeg required for this test.")
def test_noisepattern_ffmpeg():
    pattern_noise('ffmpeg')

@unittest.skipIf(not skvideo._HAS_AVCONV, "LibAV required for this test.")
def test_noisepattern_libav():
    pattern_noise('libav')
