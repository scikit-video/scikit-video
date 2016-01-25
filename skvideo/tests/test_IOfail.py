import skvideo.io
import sys
import numpy as np
import hashlib
import os
from numpy.testing import assert_equal
from nose.tools import *


@raises(OSError)
def test_failedread():

    # try to read invalid path
    skvideo.io.vread("garbage")


@raises(AssertionError)
def test_failedwrite():

    # try to read invalid path
    np.random.seed(0)

    # generate random data for 5 frames
    outputdata = np.random.random(size=(5, 480, 640, 3)) * 255
    outputdata = outputdata.astype(np.uint8)

    # 'garbage' folder does not exist
    skvideo.io.vwrite("garbage/garbage.mp4", outputdata)


@raises(AssertionError)
def test_failedextension():

    # try to read invalid path
    np.random.seed(0)

    # generate random data for 5 frames
    outputdata = np.random.random(size=(5, 480, 640, 3)) * 255
    outputdata = outputdata.astype(np.uint8)

    # 'garbage' extension does not exist
    skvideo.io.vwrite("garbage.garbage", outputdata)
