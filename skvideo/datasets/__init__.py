import numpy as np

from os.path import dirname
from os.path import join

def bikes():
    """Test video data for video scene detection algorithms

    Returns
    -------
    path : string
        Absolute path to bikes.mp4
    """
    module_path = dirname(__file__)
    return join(module_path, 'data', 'bikes.mp4')

def bigbuckbunny():
    """Test video data for general video algorithms

    Returns
    -------
    path : string
        Absolute path to bigbuckbunny.mp4
    """
    module_path = dirname(__file__)
    return join(module_path, 'data', 'bigbuckbunny.mp4')

def fullreferencepair():
    """Test video data for full-reference video quality algorithms

    The sequence "carphone" is provided for quality-based
    test cases where two videos of the same dimensions are
    needed.

    Returns
    -------
    paths : ndarray, shape (2,)
        First element contains the absolute path to
        a pristine video. Second element contains
        absolute path to a distorted video.
    """
    module_path = dirname(__file__)
    return np.array([
            join(module_path, 'data', 'carphone_pristine.mp4'),
            join(module_path, 'data', 'carphone_distorted.mp4'),
    ])

__all__ = ['bikes', 'bigbuckbunny', 'fullreferencepair']
