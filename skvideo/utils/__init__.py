""" Various utility functions for manipulating video data

"""

from .xmltodict import parse as xmltodictparser
import subprocess as sp
import numpy as np

# python2 only
binary_type = str

def read_n_bytes(f, N):
    """ read_n_bytes(file, n)
    
    Read n bytes from the given file, or less if the file has less
    bytes. Returns zero bytes if the file is closed.
    """
    bb = binary_type()
    while len(bb) < N:
        extra_bytes = f.read(N-len(bb))
        if not extra_bytes:
            break
        bb += extra_bytes
    return bb

def check_dict(dic, key, valueifnot):
    if key not in dic:
        dic[key] = valueifnot


# patch for python 2.6
def check_output(*popenargs, **kwargs):
    closeNULL = 0
    try:
        from subprocess import DEVNULL
        closeNULL = 0
    except ImportError:
        import os
        DEVNULL = open(os.devnull, 'wb')
        closeNULL = 1

    process = sp.Popen(stdout=sp.PIPE, stderr=DEVNULL, *popenargs, **kwargs)
    output, unused_err = process.communicate()
    retcode = process.poll()

    if closeNULL:
        DEVNULL.close()

    if retcode:
        cmd = kwargs.get("args")
        if cmd is None:
            cmd = popenargs[0]
        error = sp.CalledProcessError(retcode, cmd)
        error.output = output
        raise error
    return output

def vshape(videodata):
    """Standardizes the input data shape.

    Transforms video data into the standardized shape (T, M, N, C), where
    T is number of frames, M is height, N is width, and C is number of 
    channels.

    Parameters
    ----------
    videodata : ndarray
        Input data of shape (T, M, N, C), (T, M, N), (M, N, C), or (M, N), where
        T is number of frames, M is height, N is width, and C is number of 
        channels.

    Returns
    -------
    videodataout : ndarray
        Standardized version of videodata, shape (T, M, N, C)

    """
    videodata = np.array(videodata)
    if len(videodata.shape) == 2: 
        a, b = videodata.shape
        return videodata.reshape(1, a, b, 1) 
    elif len(videodata.shape) == 3: 
        a, b, c = videodata.shape
        # check the last dimension small
        # interpret as color channel
        if c in [1, 2, 3, 4]:
            return videodata.reshape(1, a, b, c) 
        else:
            return videodata.reshape(a, b, c, 1) 
    elif len(videodata.shape) == 4: 
        return videodata
    else:
        raise ValueError("Improper data input")

def rgb2gray(videodata):
    """Computes the grayscale video.

    Computes the grayscale video from the input video returning the 
    standardized shape (T, M, N, C), where T is number of frames, 
    M is height, N is width, and C is number of channels (here always 1).

    Parameters
    ----------
    videodata : ndarray
        Input data of shape (T, M, N, C), (T, M, N), (M, N, C), or (M, N), where
        T is number of frames, M is height, N is width, and C is number of 
        channels.

    Returns
    -------
    videodataout : ndarray
        Standardized grayscaled version of videodata, shape (T, M, N, 1)
    """
    videodata = vshape(videodata)
    T, M, N, C = videodata.shape

    if C == 1:
        return videodata
    elif C == 3: # assume RGB
        videodata = videodata[:, :, :, 0]*0.2989 + videodata[:, :, :, 1]*0.5870 + videodata[:, :, :, 2]*0.1140 
        return vshape(videodata)
    else:
        raise NotImplemented
