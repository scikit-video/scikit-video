from ..utils import *
import numpy as np
import scipy.ndimage


def gauss_window(lw, sigma):
    sd = np.float32(sigma)
    lw = int(lw)
    weights = [0.0] * (2 * lw + 1)
    weights[lw] = 1.0
    ss = 1.0
    sd *= sd
    for ii in range(1, lw + 1):
        tmp = np.exp(-0.5 * np.float32(ii * ii) / sd)
        weights[lw + ii] = tmp
        weights[lw - ii] = tmp
        ss += 2.0 * tmp
    for ii in range(2 * lw + 1):
        weights[ii] /= ss
    return weights


def ssim(referenceVideoData, distortedVideoData, bitdepth=8):
    """Computes Structural Similarity (SSIM) Index. [#f1]_

    Both video inputs are compared frame-by-frame to obtain T
    SSIM measurements on the luminance channel.

    Parameters
    ----------
    referenceVideoData : ndarray
        Reference video, ndarray of dimension (T, M, N, C), (T, M, N), (M, N, C), or (M, N),
        where T is the number of frames, M is the height, N is width,
        and C is number of channels. Here C is only allowed to be 1.

    distortedVideoData : ndarray
        Distorted video, ndarray of dimension (T, M, N, C), (T, M, N), (M, N, C), or (M, N),
        where T is the number of frames, M is the height, N is width,
        and C is number of channels. Here C is only allowed to be 1.

    bitdepth : int
        The number of bits each pixel effectively has

    Returns
    -------
    ssim_array : ndarray
        The ssim results, ndarray of dimension (T,), where T
        is the number of frames

    References
    ----------

    .. [#f1] Z. Wang, A. C. Bovik, H. R. Sheikh, and E. P. Simoncelli, "Image quality assessment: From error measurement to structural similarity" IEEE Transactions on Image Processing, vol. 13, no. 1, Jan. 2004.

    """

    referenceVideoData = vshape(referenceVideoData)
    distortedVideoData = vshape(distortedVideoData)

    assert(referenceVideoData.shape == distortedVideoData.shape)

    T, M, N, C = referenceVideoData.shape

    assert C == 1, "ssim called with videos containing %d channels. Please supply only the luminance channel" % (C,)

    referenceVideoData = referenceVideoData[:, :, :, 0]
    distortedVideoData = distortedVideoData[:, :, :, 0]

    extend_mode = 'constant'
    avg_window = gauss_window(5, 1.5)
    K_1 = 0.01
    K_2 = 0.03
    L = np.int(2**bitdepth - 1)

    C1 = (K_1 * L)**2
    C2 = (K_2 * L)**2

    mu1 = np.zeros((M, N), dtype=np.float32)
    mu2 = np.zeros((M, N), dtype=np.float32)
    var1 = np.zeros((M, N), dtype=np.float32)
    var2 = np.zeros((M, N), dtype=np.float32)
    var12 = np.zeros((M, N), dtype=np.float32)

    scores = np.zeros(T, dtype=np.float32)
    for t in range(T):
        referenceFrame = referenceVideoData[t].astype(np.float32)
        distortedFrame = distortedVideoData[t].astype(np.float32)
        scipy.ndimage.correlate1d(referenceFrame, avg_window, 0, mu1, mode=extend_mode)
        scipy.ndimage.correlate1d(mu1, avg_window, 1, mu1, mode=extend_mode)
        scipy.ndimage.correlate1d(distortedFrame, avg_window, 0, mu2, mode=extend_mode)
        scipy.ndimage.correlate1d(mu2, avg_window, 1, mu2, mode=extend_mode)

        mu1_sq = mu1**2
        mu2_sq = mu2**2
        mu1_mu2 = mu1 * mu2

        scipy.ndimage.correlate1d(referenceFrame**2, avg_window, 0, var1, mode=extend_mode)
        scipy.ndimage.correlate1d(var1, avg_window, 1, var1, mode=extend_mode)
        scipy.ndimage.correlate1d(distortedFrame**2, avg_window, 0, var2, mode=extend_mode)
        scipy.ndimage.correlate1d(var2, avg_window, 1, var2, mode=extend_mode)
        scipy.ndimage.correlate1d(referenceFrame * distortedFrame, avg_window, 0, var12, mode=extend_mode)
        scipy.ndimage.correlate1d(var12, avg_window, 1, var12, mode=extend_mode)

        sigma1_sq = var1 - mu1_sq
        sigma2_sq = var2 - mu2_sq
        sigma12 = var12 - mu1_mu2

        ssim_map = ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))

        ssim_map = ssim_map[5:-5, 5:-5]

        scores[t] = np.mean(ssim_map)

    return scores
