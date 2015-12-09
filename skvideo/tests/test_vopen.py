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

def test_vopen():
    outputfile = "test.mp4"

    np.random.seed(0)

    # generate random data for 5 frames
    outputdata = np.random.random(size=(5, 480, 640, 3)) * 255
    outputdata = outputdata.astype(np.uint8)

    # open up a handler
    vhandle = skvideo.io.vopen(outputdata, frameSize=(480, 640))
    for i in xrange(5):
        vhandle.write(outputdata[i, :, :, :])
    vhandle.close(outputdata)

    # check a hash of the output file
    h = hashfile(open(outputfile, 'rb'), hashlib.sha256())
    assert_equal("7670dc3556bfc447210b66869a81774cab06774c05160a16d9865995f20e7b12", h)

    # remove test file
    os.remove(outputfile)
