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

def ssim_index_new(im1, im2, K_1, K_2, avg_window):
    extend_mode='constant'
    C1 = (K_1 * 255)**2
    C2 = (K_2 * 255)**2
    M, N = im1.shape
    mu1 = np.zeros((M, N), dtype=np.float32)
    mu2 = np.zeros((M, N), dtype=np.float32)
    var1 = np.zeros((M, N), dtype=np.float32)
    var2 = np.zeros((M, N), dtype=np.float32)
    var12 = np.zeros((M, N), dtype=np.float32)

    referenceFrame = im1.astype(np.float32)
    distortedFrame = im2.astype(np.float32)
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
    cs_map = (2*sigma12 + C2)/(sigma1_sq + sigma2_sq + C2)

    ssim_map = ssim_map[5:-5, 5:-5]
    cs_map = cs_map[5:-5, 5:-5]

    mssim = np.mean(ssim_map)
    mcs = np.mean(cs_map)

    return mssim, ssim_map, mcs, cs_map


def compute_msssim(frame1, frame2, method='product'):
    extend_mode = 'constant'
    avg_window = np.array(gauss_window(5, 1.5))
    K_1 = 0.01
    K_2 = 0.03
    level = 5
    weight1 = np.array([0.0448, 0.2856, 0.3001, 0.2363, 0.1333])
    weight2 = weight1.copy()
    weight2 /= np.sum(weight2)

    downsample_filter = np.ones(2, dtype=np.float32)/2.0

    im1 = frame1.astype(np.float32)
    im2 = frame2.astype(np.float32)

    overall_mssim1 = []
    overall_mssim2 = []
    for i in range(level):
      mssim_array, ssim_map_array, mcs_array, cs_map_array = ssim_index_new(im1, im2, K_1, K_2, avg_window)
      filtered_im1 = scipy.ndimage.correlate1d(im1, downsample_filter, 0)
      filtered_im1 = scipy.ndimage.correlate1d(filtered_im1, downsample_filter, 1)
      filtered_im1 = filtered_im1[1:, 1:]

      filtered_im2 = scipy.ndimage.correlate1d(im2, downsample_filter, 0)
      filtered_im2 = scipy.ndimage.correlate1d(filtered_im2, downsample_filter, 1)
      filtered_im2 = filtered_im2[1:, 1:]

      im1 = filtered_im1[::2, ::2]
      im2 = filtered_im2[::2, ::2]

      if i != level-1:
        overall_mssim1.append(mcs_array**weight1[i])
        overall_mssim2.append(mcs_array*weight2[i])

    if method == "product":
      overall_mssim = np.product(overall_mssim1) * mssim_array
    else:
      overall_mssim = np.sum(overall_mssim2) + mssim_array

    return overall_mssim


def msssim(referenceVideoData, distortedVideoData, method='product'):
    """Computes Multiscale Structural Similarity (MS-SSIM) Index. [#f1]_

    Both video inputs are compared frame-by-frame to obtain T
    MS-SSIM measurements on the luminance channel.

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

    method : str
        Whether to use "product" (default) or to use "sum" for combing multiple scales into the single score.

    Returns
    -------
    msssim_array : ndarray
        The MS-SSIM results, ndarray of dimension (T,), where T
        is the number of frames

    References
    ----------

    .. [#f1] Z. Wang, E. P. Simoncelli and A. C. Bovik, "Multi-scale structural similarity for image quality assessment," IEEE Asilomar Conference Signals, Systems and Computers, Nov. 2003.

    """

    referenceVideoData = vshape(referenceVideoData)
    distortedVideoData = vshape(distortedVideoData)

    assert(referenceVideoData.shape == distortedVideoData.shape)

    T, M, N, C = referenceVideoData.shape

    assert C == 1, "MS-SSIM called with videos containing %d channels. Please supply only the luminance channel" % (C,)
    assert (M >= 176) | (N >= 176), "You supplied a resolution of %dx%d. MS-SSIM can only be used with videos large enough having multiple scales. Please use only with resolutions >= 176x176." % (M, N)

    scores = np.zeros(T, dtype=np.float32)
    for t in range(T):
        referenceFrame = referenceVideoData[t, :, :, 0].astype(np.float32)
        distortedFrame = distortedVideoData[t, :, :, 0].astype(np.float32)
    
        scores[t] = compute_msssim(referenceFrame, distortedFrame, method=method)

    return scores
