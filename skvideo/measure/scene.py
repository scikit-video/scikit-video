"""
Implementation of scene detection algorithms.

"""

import numpy as np
import os
import scipy.ndimage
import scipy.spatial
import time

from ..utils import *
from ..motion.gme import globalEdgeMotion

from .edge import canny


def _percentage_distance(canny_in, canny_out, r):
    diamond = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]])

    E_1 = scipy.ndimage.morphology.binary_dilation(canny_in, structure=diamond, iterations=r)
    E_2 = scipy.ndimage.morphology.binary_dilation(canny_out, structure=diamond, iterations=r)

    return 1.0 - np.float(np.sum(E_1 & E_2))/np.float(np.sum(E_1))

def _scenedet_edges(videodata, threshold):
    # the first frame is always a new scene
    detected_scenes = [0]
    r = 6

    # grayscale
    luminancedata = rgb2gray(videodata)

    numFrames, height, width, channels = luminancedata.shape

    # lop off the meaningless dimension
    luminancedata = luminancedata[:, :, :, 0]

    for t in range(0, numFrames-1):
        canny_in = canny(luminancedata[t])
        canny_out = canny(luminancedata[t+1])

        # estimate the motion
        disp = globalEdgeMotion(canny_in, canny_out)
        canny_out = np.roll(canny_out, disp[0], axis=0)
        canny_out = np.roll(canny_out, disp[1], axis=1)
        
        # compute percentage
        p_in = _percentage_distance(canny_in, canny_out, r)
        p_out = _percentage_distance(canny_out, canny_in, r)
        # print "percentage: ", bt - at
        p = np.max((p_in, p_out))

        if p > threshold:
            detected_scenes.append(t+1)

    return np.array(detected_scenes)


def _scenedet_intensity(videodata, parameter1):
    # the first frame is always a new scene
    detected_scenes = [0]

    # grayscale
    luminancedata = rgb2gray(videodata)

    numFrames, height, width, channels = luminancedata.shape

    luminancedata = luminancedata[:, :, :, 0]

    for t in range(0, numFrames-1):
        hist1, bins = np.histogram(luminancedata[t], bins=256, range=(0, 255))
        hist2, bins = np.histogram(luminancedata[t+1], bins=256, range=(0, 255))

        hist1 = hist1.astype(np.float)
        hist2 = hist2.astype(np.float)

        hist1 /= 256.0
        hist2 /= 256.0
        
        framediff = np.mean(np.abs(hist1 - hist2))
        if framediff > parameter1:
            detected_scenes.append(t+1)

    return np.array(detected_scenes)


def scenedet(videodata, method='edges', parameter1=None):
    """Scene detection algorithms
    
    Given a sequence of frames, this function
    is able to run find the first index of new
    scenes.

    Parameters
    ----------
    videodata : ndarray
        an input frame sequence, shape (T, M, N, C), (T, M, N), (M, N, C) or (M, N)

    method : string
        "intensity" --> threshold-based (parameter1 defaults to 0.0625) approach using intensity histogram differences. [#f1]_

        "edges" --> threshold-based (parameter1 defaults to 0.5) approach measuring the edge-change fraction after global motion compensation [#f2]_
   
    parameter1 : int
        Number used as a tuning parameter. See method argument for details.

    Returns
    ----------
    sceneCuts : ndarray, shape (numScenes,)

        The indices corresponding to the first frame in the detected scenes.

    References
    ----------
    .. [#f1] Kiyotaka Otsuji and Yoshinobu Tonomura. Projection-detecting filter for video cut detection. Multimedia Systems 1.5, 205-210, 1994.

    .. [#f2] Kevin Mai, Ramin Zabih, and Justin Miller. Feature-based algorithms for detecting and classifying scene breaks. Cornell University, 1995.


    

    """
    videodata = vshape(videodata)

    detected_scenes = []
    if method == "intensity":
        if parameter1 is None:
            parameter1 = 0.0625
        detected_scenes = _scenedet_intensity(videodata, parameter1)
    elif method == "edges":
        if parameter1 is None:
            parameter1 = 0.6
        detected_scenes = _scenedet_edges(videodata, parameter1)
    else:
        raise NotImplementedError

    return detected_scenes


