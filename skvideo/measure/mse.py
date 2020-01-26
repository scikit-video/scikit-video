from ..utils import *
import numpy as np
import scipy.ndimage
from PIL import Image


def mse(referenceVideoData, distortedVideoData):
    """Computes mean-squared error (MSE).

    Both video inputs are compared frame-by-frame to obtain T
    MSE measurements.

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
    mse_array : ndarray
        The mse results, ndarray of dimension (T,), where T
        is the number of frames

    """

    referenceVideoData = vshape(referenceVideoData)
    distortedVideoData = vshape(distortedVideoData)

    assert(referenceVideoData.shape == distortedVideoData.shape)

    T, M, N, C = referenceVideoData.shape

    assert C == 1, "mse called with videos containing %d channels. Please supply only the luminance channel" % (C,)

    scores = np.zeros(T, dtype=np.float32)
    for t in range(T):
        referenceFrame = referenceVideoData[t].astype(np.float32)
        distortedFrame = distortedVideoData[t].astype(np.float32)

        mse = np.mean((referenceFrame - distortedFrame)**2)

        scores[t] = mse

    return scores


def mse_rgb(referenceVideoData: np.ndarray, distortedVideoData: np.ndarray):
    """Convenience wrapper to allow computing mean-squared error (MSE) on multi-channel videos.

    Both video inputs are compared frame-by-frame to obtain T
    MSE measurements.

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
    mse_array : ndarray
        The mse results, ndarray of dimension (T,), where T
        is the number of frames

    """
    # It would be preferable to use a vreader-like generator to avoid doubling memory usage,
    # but currently mse() itself takes only a raw ndarray.
    referenceVideoLuminance = np.empty(referenceVideoData.shape[:-1])
    distortedVideoLuminance = np.empty(distortedVideoData.shape[:-1])
    for frameIndex in range(referenceVideoData.shape[0]):
        referenceVideoLuminance[frameIndex, :, :] = Image.fromarray(referenceVideoData[frameIndex, :, :, :]).convert('L')
        distortedVideoLuminance[frameIndex, :, :] = Image.fromarray(distortedVideoData[frameIndex, :, :, :]).convert('L')
    return mse(referenceVideoLuminance, distortedVideoLuminance)

