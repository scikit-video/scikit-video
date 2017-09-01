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


def _percentage_distance(canny_in, canny_out, r):
    diamond = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]])

    E_1 = scipy.ndimage.morphology.binary_dilation(canny_in, structure=diamond, iterations=r)
    E_2 = scipy.ndimage.morphology.binary_dilation(canny_out, structure=diamond, iterations=r)

    return 1.0 - np.float32(np.sum(E_1 & E_2))/np.float32(np.sum(E_1))

def _scenedet_edges(videodata, threshold, min_scene_len=2):
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

        if (p > threshold) and (t - detected_scenes[len(detected_scenes)-1] > min_scene_len):
            detected_scenes.append(t+1)

    return np.array(detected_scenes)


def _scenedet_histogram(videodata, parameter1, min_scene_len=2):
    # the first frame is always a new scene
    detected_scenes = [0]

    # grayscale
    numFrames, height, width, channels = videodata.shape

    for t in range(0, numFrames-1):
        curr = rgb2gray(videodata[t])
        nxt = rgb2gray(videodata[t+1])
        curr = curr[0, :, :, 0]
        nxt = nxt[0, :, :, 0]
        hist1, bins = np.histogram(curr, bins=256, range=(0, 255))
        hist2, bins = np.histogram(nxt, bins=256, range=(0, 255))

        hist1 = hist1.astype(np.float32)
        hist2 = hist2.astype(np.float32)

        hist1 /= 256.0
        hist2 /= 256.0
        
        framediff = np.mean(np.abs(hist1 - hist2))
        if (framediff > parameter1) and (t - detected_scenes[len(detected_scenes)-1] > min_scene_len):
            detected_scenes.append(t+1)

    return np.array(detected_scenes)


def _scenedet_intensity(videodata, parameter1, min_scene_len=2, colorspace='hsv'):

    detected_scenes = [0]

    numFrames, height, width, channels = videodata.shape

    for t in range(0, numFrames-1):
        frame0 = videodata[t].astype(np.float32)
        frame1 = videodata[t+1].astype(np.float32)

        delta = np.sum(np.abs(frame1 - frame0)/(height * width * channels))

        if (delta > parameter1) and (t - detected_scenes[len(detected_scenes)-1] > min_scene_len):
            detected_scenes.append(t+1)

    return np.array(detected_scenes)



def scenedet(videodata, method='histogram', parameter1=None, min_scene_length=2):
    """Scene detection algorithms
    
    Given a sequence of frames, this function
    is able to run find the first index of new
    scenes.

    Parameters
    ----------
    videodata : ndarray
        an input frame sequence, shape (T, M, N, C), (T, M, N), (M, N, C) or (M, N)

    method : string
        "histogram" --> threshold-based (parameter1 defaults to 1.0) approach using intensity histogram differences. [#f1]_

        "edges" --> threshold-based (parameter1 defaults to 0.5) approach measuring the edge-change fraction after global motion compensation [#f2]_

        "intensity" --> Detects fast cuts using changes in colour and intensity between frames. Parameter1 is the threshold used for detection, which defaults to 30.0.

    parameter1 : int
        Number used as a tuning parameter. See method argument for details.

    min_scene_length : int
        Number used for determining minimum scene length.

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
    if method == "histogram":
        if parameter1 is None:
            parameter1 = 1.0
        detected_scenes = _scenedet_histogram(videodata, parameter1, min_scene_length)
    elif method == "edges":
        if parameter1 is None:
            parameter1 = 0.6
        detected_scenes = _scenedet_edges(videodata, parameter1, min_scene_length)
    elif method == "intensity":
        if parameter1 is None:
            parameter1 = 1.0
        detected_scenes = _scenedet_intensity(videodata, parameter1, min_scene_length)
    else:
        raise NotImplementedError

    return detected_scenes


