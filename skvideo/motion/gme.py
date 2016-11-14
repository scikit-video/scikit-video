"""
Implementation of global motion estimators.

"""

import numpy as np
import os
import scipy.ndimage
import scipy.spatial

from ..utils import *


def _hausdorff_distance(E_1, E_2):
    # binary structure
    diamond = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]])

    # extract only 1-pixel border line of objects
    E_1_per = E_1 - scipy.ndimage.morphology.binary_erosion(E_1, structure=diamond)
    E_2_per = E_2 - scipy.ndimage.morphology.binary_erosion(E_2, structure=diamond)

    A = scipy.ndimage.morphology.distance_transform_edt(~E_2_per)[E_1_per].max()
    B = scipy.ndimage.morphology.distance_transform_edt(~E_1_per)[E_2_per].max()
    return np.max((A, B))



def globalEdgeMotion(frame1, frame2, r=6, method='hamming'):
    """Global motion estimation using edge features
    
    Given two frames, find a robust global translation vector
    found using edge information.

    Parameters
    ----------
    frame1 : ndarray
        first input frame, shape (1, M, N, C), (1, M, N), (M, N, C) or (M, N)

    frame2 : ndarray
        second input frame, shape (1, M, N, C), (1, M, N), (M, N, C) or (M, N)

    r : int
        Search radius for measuring correspondences.

    method : string
        "hamming" --> use Hamming distance when measuring edge correspondence distances. The distance used in the census transform. [#f1]_

        "hausdorff" --> use Hausdorff distance when measuring edge correspondence distances. [#f2]_

    Returns
    ----------
    globalMotionVector  : ndarray, shape (2,)
        The motion to minimize edge distances by moving frame2 with respect to frame1.

    References
    ----------
    .. [#f1] Ramin Zabih and John Woodfill. Non-parametric local transforms for computing visual correspondence. Computer Vision-ECCV, 151-158, 1994. 
    
    .. [#f2] Kevin Mai, Ramin Zabih, and Justin Miller. Feature-based algorithms for detecting and classifying scene breaks. Cornell University, 1995.

    """

    # if type bool, then these are edge maps. No need to convert them
    if frame1.dtype != np.bool:
        E_1 = canny(frame1)
    else:
        E_1 = frame1

    if frame2.dtype != np.bool:
        E_2 = canny(frame2)
    else:
        E_2 = frame2

    distances = []
    displacements = []
    for dx in range(-r, r+1, 1):
        for dy in range(-r, r+1, 1):
            cimage = np.roll(E_2, dx, axis=0)
            cimage = np.roll(cimage, dy, axis=1)
            # smallest distance between a point of points found in cimage
            if method == 'hamming':
                distance = scipy.spatial.distance.hamming(np.ravel(cimage), np.ravel(E_1))
            elif method == 'hausdorff':
                distance = _hausdorff_distance(cimage, E_2)
            else:
                raise Notimplemented
            # compute # of bit flip distance
            distances.append(distance)
            displacements.append([dx, dy])

    idx = np.argmin(distances)
    return displacements[idx]
