import warnings
warnings.filterwarnings('ignore', category=UserWarning)

from numpy.testing import assert_equal, assert_almost_equal
import os
import sys
import numpy as np
import skvideo.io
import skvideo.datasets
import skvideo.measure

if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest

#TODO: Check blas implementation, then check numerical accuracy.
#      The required inverse operation in ST-RRED differs across
#      blas implementations

def test_scenedet():
    vidpath = skvideo.datasets.bikes()

    vid = skvideo.io.vread(vidpath)

    boundaries = skvideo.measure.scenedet(vid)

    correct_boundaries = [0, 30, 76, 137, 187, 242]

    assert len(correct_boundaries) == len(boundaries), "Scene detection failed."

    error = np.sum(np.abs(correct_boundaries - boundaries))
    
    assert error < 1e-9, "Wrong boundaries detected"
