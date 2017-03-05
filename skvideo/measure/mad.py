from ..utils import *
import numpy as np
import scipy.ndimage


def mad(referenceVideoData, distortedVideoData):
    """Computes mean absolute deviation (MAD).

    Both video inputs are compared frame-by-frame to obtain T
    MAD measurements.

    Parameters
    ----------
    referenceVideoData : ndarray
        Reference video, ndarray of dimension (T, M, N, C), (T, M, N), (M, N, C), or (M, N),
        where T is the number of frames, M is the height, N is width,
        and C is number of channels.

    distortedVideoData : ndarray
        Distorted video, ndarray of dimension (T, M, N, C), (T, M, N), (M, N, C), or (M, N),
        where T is the number of frames, M is the height, N is width,
        and C is number of channels.

    Returns
    -------
    mad_array : ndarray
        The mad results, ndarray of dimension (T,), where T
        is the number of frames

    """

    referenceVideoData = vshape(referenceVideoData)
    distortedVideoData = vshape(distortedVideoData)

    assert(referenceVideoData.shape == distortedVideoData.shape)

    T, M, N, C = referenceVideoData.shape

    assert C == 1, "mad called with videos containing %d channels. Please supply only the luminance channel" % (C,)

    scores = np.zeros(T, dtype=np.float32)
    for t in range(T):
        referenceFrame = referenceVideoData[t].astype(np.float32)
        distortedFrame = distortedVideoData[t].astype(np.float32)

        mad = np.mean(np.abs(referenceFrame - distortedFrame))

        scores[t] = mad

    return scores
