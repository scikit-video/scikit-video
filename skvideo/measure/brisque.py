from ..utils import *
import numpy as np
import scipy.ndimage
import scipy.fftpack
import scipy.stats
import scipy.io
import sys

gamma_range = np.arange(0.2, 10, 0.001)
a = scipy.special.gamma(2.0/gamma_range)
a *= a
b = scipy.special.gamma(1.0/gamma_range)
c = scipy.special.gamma(3.0/gamma_range)
prec_gammas = a/(b*c)

def gauss_window(lw, sigma):
    sd = np.float32(sigma)
    lw = int(lw)
    weights = [0.0] * (2 * lw + 1)
    weights[lw] = 1.0
    sum = 1.0
    sd *= sd
    for ii in range(1, lw + 1):
        tmp = np.exp(-0.5 * np.float32(ii * ii) / sd)
        weights[lw + ii] = tmp
        weights[lw - ii] = tmp
        sum += 2.0 * tmp
    for ii in range(2 * lw + 1):
        weights[ii] /= sum
    return weights
avg_window = gauss_window(3, 7.0/6.0)

def extract_aggd_features(imdata):
    #flatten imdata
    imdata.shape = (len(imdata.flat),)
    imdata2 = imdata*imdata
    left_data = imdata2[imdata<0]
    right_data = imdata2[imdata>=0]
    left_mean_sqrt = 0
    right_mean_sqrt = 0
    if len(left_data) > 0:
        left_mean_sqrt = np.sqrt(np.average(left_data))
    if len(right_data) > 0:
        right_mean_sqrt = np.sqrt(np.average(right_data))

    if right_mean_sqrt != 0:
      gamma_hat = left_mean_sqrt/right_mean_sqrt
    else:
      gamma_hat = np.inf
    #solve r-hat norm

    imdata2_mean = np.mean(imdata2)
    if imdata2_mean != 0:
      r_hat = (np.average(np.abs(imdata))**2) / (np.average(imdata2))
    else:
      r_hat = np.inf
    rhat_norm = r_hat * (((gamma_hat**3 + 1)*(gamma_hat + 1)) / ((gamma_hat**2 + 1)**2))

    #solve alpha by guessing values that minimize ro
    pos = np.argmin((prec_gammas - rhat_norm)**2);
    alpha = gamma_range[pos]

    gam1 = scipy.special.gamma(1.0/alpha)
    gam2 = scipy.special.gamma(2.0/alpha)
    gam3 = scipy.special.gamma(3.0/alpha)

    aggdratio = np.sqrt(gam1) / np.sqrt(gam3)
    bl = aggdratio * left_mean_sqrt
    br = aggdratio * right_mean_sqrt

    #mean parameter
    N = (br - bl)*(gam2 / gam1)#*aggdratio
    return (alpha, N, bl, br, left_mean_sqrt, right_mean_sqrt)

def extract_ggd_features(imdata):
    nr_gam = 1/prec_gammas
    sigma_sq = np.var(imdata)
    E = np.mean(np.abs(imdata))
    rho = sigma_sq/E**2
    pos = np.argmin(np.abs(nr_gam - rho));
    return gamma_range[pos], sigma_sq

def calc_image(image):
    #extend_mode = 'constant'
    extend_mode = 'constant'
    h, w = np.shape(image)
    mu_image = np.zeros((h, w), dtype=np.float32)
    var_image = np.zeros((h, w), dtype=np.float32)
    image = np.array(image).astype('float32')
    scipy.ndimage.correlate1d(image, avg_window, 0, mu_image, mode=extend_mode)
    scipy.ndimage.correlate1d(mu_image, avg_window, 1, mu_image, mode=extend_mode)
    scipy.ndimage.correlate1d(image**2, avg_window, 0, var_image, mode=extend_mode)
    scipy.ndimage.correlate1d(var_image, avg_window, 1, var_image, mode=extend_mode)
    var_image = np.sqrt(np.abs(var_image - mu_image**2))
    return (image - mu_image)/(var_image + 1), var_image, mu_image

def paired_p(new_im):
    shift1 = np.roll(new_im.copy(), 1, axis=1)
    shift2 = np.roll(new_im.copy(), 1, axis=0)
    shift3 = np.roll(np.roll(new_im.copy(), 1, axis=0), 1, axis=1)
    shift4 = np.roll(np.roll(new_im.copy(), 1, axis=0), -1, axis=1)

    H_img = shift1 * new_im
    V_img = shift2 * new_im
    D1_img = shift3 * new_im
    D2_img = shift4 * new_im

    return (H_img, V_img, D1_img, D2_img)

def _extract_subband_feats(mscncoefs):
    # alpha_m,  = extract_ggd_features(mscncoefs)
    alpha_m, sigma_sq = extract_ggd_features(mscncoefs.copy())
    pps1, pps2, pps3, pps4 = paired_p(mscncoefs)
    alpha1, N1, bl1, br1, lsq1, rsq1 = extract_aggd_features(pps1)
    alpha2, N2, bl2, br2, lsq2, rsq2 = extract_aggd_features(pps2)
    alpha3, N3, bl3, br3, lsq3, rsq3 = extract_aggd_features(pps3)
    alpha4, N4, bl4, br4, lsq4, rsq4 = extract_aggd_features(pps4)
    return np.array([
            alpha_m, sigma_sq,
            alpha1, N1, lsq1**2, rsq1**2,  # (V)
            alpha2, N2, lsq2**2, rsq2**2,  # (H)
            alpha3, N3, lsq3**2, rsq3**2,  # (D1)
            alpha4, N4, lsq4**2, rsq4**2,  # (D2)
    ])


def brisque_features(videoData):
    """Computes Blind/Referenceless Image Spatial QUality Evaluator (BRISQUE) features. [#f1]_ [#f2]_

    Since this is a referenceless image quality algorithm, only 1 video is needed. This function
    provides the raw features extracted per frame.

    Parameters
    ----------
    videoData : ndarray
        Reference video, ndarray of dimension (T, M, N, C), (T, M, N), (M, N, C), or (M, N),
        where T is the number of frames, M is the height, N is width,
        and C is number of channels.

    Returns
    -------
    features : ndarray
        A matrix of shape (T, 36) of the computed BRISQUE features.

    References
    ----------

    .. [#f1] A. Mittal, A. K. Moorthy and A. C. Bovik, "No-Reference Image Quality Assessment in the Spatial Domain" IEEE Transactions on Image Processing, 2012. 
    .. [#f2] A. Mittal, A. K. Moorthy and A. C. Bovik, "Referenceless Image Spatial Quality Evaluation Engine," 45th Asilomar Conference on Signals, Systems and Computers , November 2011.

    """

    videoData = vshape(videoData)

    T, M, N, C = videoData.shape

    assert C == 1, "brisque_features called with video having %d channels. Please supply only the luminance channel." % (C,)

    feats = np.zeros((T, 36), dtype=np.float32)
    for i in range(T):
      full_scale = videoData[i, :, :, 0].astype(np.float32)
      half_scale = scipy.misc.imresize(full_scale, 0.5, interp='bicubic', mode='F')

      full_scale, _, _ = calc_image(full_scale)
      half_scale, _, _ = calc_image(half_scale)

      feats[i, 18*0:18*1] = _extract_subband_feats(full_scale)
      feats[i, 18*1:18*2] = _extract_subband_feats(half_scale)

    return feats
