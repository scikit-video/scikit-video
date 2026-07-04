"""
Implementation of global motion estimators.

"""

import numpy as np
import scipy.ndimage
import scipy.spatial

from ..utils import canny, rgb2gray, vshape


def _hausdorff_distance(E_1, E_2):
    # binary structure
    diamond = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]])

    # extract only 1-pixel border line of objects
    E_1_per = E_1^scipy.ndimage.binary_erosion(E_1, structure=diamond)
    E_2_per = E_2^scipy.ndimage.binary_erosion(E_2, structure=diamond)

    A = scipy.ndimage.distance_transform_edt(~E_2_per)[E_1_per].max()
    B = scipy.ndimage.distance_transform_edt(~E_1_per)[E_2_per].max()
    return np.max((A, B))



def globalEdgeMotion(frame1, frame2, r=6, method='hamming'):
    """Global motion estimation using edge features
    
    Given two frames, find a robust global translation vector
    found using edge information. Frames must be luminance, RGB, or edge masks.

    Parameters
    ----------
    frame1 : ndarray
        first input frame. Edge mask if dtype=bool, else luminance or rgb image. shape (1, M, N, C), (1, M, N), (M, N, C) or (M, N)

    frame2 : ndarray
        second input frame. Edge mask if dtype=bool, else luminance or rgb image. shape (1, M, N, C), (1, M, N), (M, N, C) or (M, N)

    r : int
        Search radius for measuring correspondences.

    method : string
        "hamming" --> use Hamming distance when measuring edge correspondence distances. The distance used in the census transform. [#f1]_

        "hausdorff" --> use Hausdorff distance when measuring edge correspondence distances. [#f2]_

    Returns
    ----------
    globalMotionVector  : list of int, length 2
        The motion to minimize edge distances by moving frame2 with respect
        to frame1. Returns ``[0, 0]`` when either frame contains no edges
        (no edge correspondence to minimize), so a blank/edgeless frame
        yields "no detected motion" rather than a spurious or crashing
        result.

    References
    ----------
    .. [#f1] Ramin Zabih and John Woodfill. Non-parametric local transforms for computing visual correspondence. Computer Vision-ECCV, 151-158, 1994. 
    
    .. [#f2] Kevin Mai, Ramin Zabih, and Justin Miller. Feature-based algorithms for detecting and classifying scene breaks. Cornell University, 1995.

    """

    frame1 = vshape(frame1)
    frame2 = vshape(frame2)
    
    if frame1.shape != frame2.shape:
        raise ValueError("frame1 and frame2 must have the same shape; got %s vs %s" % (frame1.shape, frame2.shape))

    T, M, N, C = frame1.shape

    if C == 3:
        frame1 = rgb2gray(frame1)
        frame2 = rgb2gray(frame2)
    elif C != 1:
        raise ValueError("called with frames having %d channels. Please supply only the luminance channel or RGB images." % (C,))

    # if type bool, then these are edge maps. No need to convert them, but
    # still squeeze to 2D so the roll/morphology ops below see (M, N) like
    # the canny() path produces (vshape made them 4D).
    if frame1.dtype != bool:
        E_1 = canny(frame1.squeeze())
    else:
        E_1 = frame1.squeeze()
    if frame2.dtype != bool:
        E_2 = canny(frame2.squeeze())
    else:
        E_2 = frame2.squeeze()

    # If either frame has no edges, there is no edge correspondence to
    # minimize: every displacement ties (hamming would argmin to the first,
    # i.e. (-r, -r)) and the hausdorff distance does an empty-array reduction
    # and crashes. Report no detectable motion.
    if not E_1.any() or not E_2.any():
        return [0, 0]

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
                # cimage is the shifted frame2 edge map; measure its distance
                # to frame1's edges (E_1), matching the hamming branch.
                distance = _hausdorff_distance(cimage, E_1)
            else:
                raise NotImplementedError(
                    "Unknown method %r; expected 'hamming' or 'hausdorff'." % (method,)
                )
            # compute # of bit flip distance
            distances.append(distance)
            displacements.append([dx, dy])

    idx = np.argmin(distances)
    return displacements[idx]
