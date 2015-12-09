import numpy as np

from os.path import dirname
from os.path import join

def bigbuckbunny():
    module_path = dirname(__file__)
    return join(module_path, 'data', 'bigbuckbunny.mp4')

def fullreferencepair():
    module_path = dirname(__file__)
    return np.array([
            join(module_path, 'data', 'carphone_pristine.mp4'),
            join(module_path, 'data', 'carphone_distorted.mp4'),
    ])

__all__ = ['bigbuckbunny', 'fullreferencepair']
