from ..utils import *
import numpy as np
import scipy.ndimage


def psnr(referenceVideoData, distortedVideoData, bitdepth=8):
    """Computes Peak Signal to Noise Ratio (PSNR).

    Both video inputs are compared frame-by-frame to obtain T
    PSNR measurements.

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

    bitdepth : int
        The number of bits each pixel effectively has

    Returns
    -------
    psnr_array : ndarray
        The psnr results, ndarray of dimension (T,), where T
        is the number of frames

    """

    referenceVideoData = vshape(referenceVideoData)
    distortedVideoData = vshape(distortedVideoData)

    bitdepth = np.int(bitdepth)

    assert(referenceVideoData.shape == distortedVideoData.shape)

    T, M, N, C = referenceVideoData.shape

    assert C == 1, "psnr called with videos containing %d channels. Please supply only the luminance channel" % (C,)

    maxvalue = np.int(2**bitdepth - 1)
    maxsq = maxvalue**2

    scores = np.zeros(T, dtype=np.float)
    for t in range(T):
        referenceFrame = referenceVideoData[t].astype(np.float)
        distortedFrame = distortedVideoData[t].astype(np.float)

        mse = np.mean((referenceFrame - distortedFrame)**2)
        psnr = 10 * np.log10(maxsq / mse)

        scores[t] = psnr

    return scores
