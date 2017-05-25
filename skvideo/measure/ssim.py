from ..utils import *
import numpy as np
import scipy.ndimage

def _ssim_core(referenceVideoFrame, distortedVideoFrame, K_1, K_2, bitdepth, scaleFix, avg_window):

    referenceVideoFrame = referenceVideoFrame.astype(np.float32)
    distortedVideoFrame = distortedVideoFrame.astype(np.float32)

    M, N = referenceVideoFrame.shape

    extend_mode = 'constant'
    if avg_window is None:
      avg_window = gen_gauss_window(5, 1.5)
    
    L = np.int(2**bitdepth - 1)

    C1 = (K_1 * L)**2
    C2 = (K_2 * L)**2

    factor = np.int(np.max((1, np.round(np.min((M, N))/256.0))))
    factor_lpf = np.ones((factor,factor), dtype=np.float32)
    factor_lpf /= np.sum(factor_lpf)

    if scaleFix:
      M = np.int(np.round(np.float(M) / factor + 1e-9))
      N = np.int(np.round(np.float(N) / factor + 1e-9))

    mu1 = np.zeros((M, N), dtype=np.float32)
    mu2 = np.zeros((M, N), dtype=np.float32)
    var1 = np.zeros((M, N), dtype=np.float32)
    var2 = np.zeros((M, N), dtype=np.float32)
    var12 = np.zeros((M, N), dtype=np.float32)

    # scale if enabled
    if scaleFix and (factor > 1):
        referenceVideoFrame = scipy.signal.correlate2d(referenceVideoFrame, factor_lpf, mode='same', boundary='symm')
        distortedVideoFrame = scipy.signal.correlate2d(distortedVideoFrame, factor_lpf, mode='same', boundary='symm')
        referenceVideoFrame = referenceVideoFrame[::factor, ::factor]
        distortedVideoFrame = distortedVideoFrame[::factor, ::factor]

    scipy.ndimage.correlate1d(referenceVideoFrame, avg_window, 0, mu1, mode=extend_mode)
    scipy.ndimage.correlate1d(mu1, avg_window, 1, mu1, mode=extend_mode)
    scipy.ndimage.correlate1d(distortedVideoFrame, avg_window, 0, mu2, mode=extend_mode)
    scipy.ndimage.correlate1d(mu2, avg_window, 1, mu2, mode=extend_mode)

    mu1_sq = mu1**2
    mu2_sq = mu2**2
    mu1_mu2 = mu1 * mu2

    scipy.ndimage.correlate1d(referenceVideoFrame**2, avg_window, 0, var1, mode=extend_mode)
    scipy.ndimage.correlate1d(var1, avg_window, 1, var1, mode=extend_mode)
    scipy.ndimage.correlate1d(distortedVideoFrame**2, avg_window, 0, var2, mode=extend_mode)
    scipy.ndimage.correlate1d(var2, avg_window, 1, var2, mode=extend_mode)
    scipy.ndimage.correlate1d(referenceVideoFrame * distortedVideoFrame, avg_window, 0, var12, mode=extend_mode)
    scipy.ndimage.correlate1d(var12, avg_window, 1, var12, mode=extend_mode)

    sigma1_sq = var1 - mu1_sq
    sigma2_sq = var2 - mu2_sq
    sigma12 = var12 - mu1_mu2

    ssim_map = ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))
    cs_map = (2*sigma12 + C2)/(sigma1_sq + sigma2_sq + C2)

    ssim_map = ssim_map[5:-5, 5:-5]
    cs_map = cs_map[5:-5, 5:-5]

    mssim = np.mean(ssim_map)
    mcs = np.mean(cs_map)

    return mssim, ssim_map, mcs, cs_map


def ssim(referenceVideoData, distortedVideoData, K_1 = 0.01, K_2 = 0.03, bitdepth=8, scaleFix=True, avg_window=None):
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

    K_1 : float
        Luminance saturation weight

    K_2 : float
        Contrast saturation weight

    bitdepth : int
        The number of bits each pixel effectively has

    scaleFix : bool
        Whether to scale the input frame size based on assumed distance, to improve subjective correlation.

    avg_window : ndarray
        2-d averaging window, normalized to unit volume.

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

    ssim_scores = np.zeros(T, dtype=np.float32)

    for t in range(T):
      mssim, ssim_map, mcs, cs_map = _ssim_core(referenceVideoData[t, :, :, 0], distortedVideoData[t, :, :, 0], K_1 = K_1, K_2 = K_2, bitdepth=bitdepth, scaleFix=scaleFix, avg_window=avg_window)
      ssim_scores[t] = mssim

    return ssim_scores


def ssim_full(referenceVideoData, distortedVideoData, K_1 = 0.01, K_2 = 0.03, bitdepth=8, scaleFix=True, avg_window=None):
    """Returns all parameters from the Structural Similarity (SSIM) Index. [#f1]_

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

    K_1 : float
        Luminance saturation weight

    K_2 : float
        Contrast saturation weight

    bitdepth : int
        The number of bits each pixel effectively has

    scaleFix : bool
        Whether to scale the input frame size based on assumed distance, to improve subjective correlation.

    avg_window : ndarray
        2-d averaging window, normalized to unit volume.

    Returns
    -------
    ssim_array : ndarray
        The ssim results, ndarray of dimension (T,), where T
        is the number of frames

    ssim_map_array : ndarray
        The ssim maps, ndarray of dimension (T,M-10, N-10), where T
        is the number of frames, and MxN are the widthxheight

    contrast_array : ndarray
        The ssim result based on only on contrast (no luminance masking),
        ndarray of dimension (T,), where T is the number of frames

    contrast_map_array : ndarray
        The ssim contrast-only maps, ndarray of dimension (T,M-10, N-10), where T
        is the number of frames, and MxN are the widthxheight


    References
    ----------

    .. [#f1] Z. Wang, A. C. Bovik, H. R. Sheikh, and E. P. Simoncelli, "Image quality assessment: From error measurement to structural similarity" IEEE Transactions on Image Processing, vol. 13, no. 1, Jan. 2004.

    """
    referenceVideoData = vshape(referenceVideoData)
    distortedVideoData = vshape(distortedVideoData)

    assert(referenceVideoData.shape == distortedVideoData.shape)


    T, M, N, C = referenceVideoData.shape

    assert C == 1, "ssim called with videos containing %d channels. Please supply only the luminance channel" % (C,)

    ssim_maps = np.zeros((T, M-10, N-10), dtype=np.float32)
    contrast_maps = np.zeros((T, M-10, N-10), dtype=np.float32)
    ssim_scores = np.zeros(T, dtype=np.float32)
    contrast_scores = np.zeros(T, dtype=np.float32)

    for t in range(T):
      mssim, ssim_map, mcs, cs_map = _ssim_core(referenceVideoData[t, :, :, 0], distortedVideoData[t, :, :, 0], K_1 = K_1, K_2 = K_2, bitdepth=bitdepth, scaleFix=scaleFix, avg_window=avg_window)
      ssim_scores[t] = mssim
      contrast_scores[t] = mcs
      ssim_maps[t] = ssim_map
      contrast_maps[t] = cs_map

    return ssim_scores, ssim_maps, contrast_scores, contrast_maps

