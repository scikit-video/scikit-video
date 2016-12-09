from ..utils import *
from ..motion import blockMotion
import numpy as np
import scipy.ndimage
import scipy.fftpack
import scipy.stats
import scipy.io
import sys

from os.path import dirname
from os.path import join

gamma_range = np.arange(0.2, 10, 0.001)
a = scipy.special.gamma(2.0/gamma_range)
a *= a
b = scipy.special.gamma(1.0/gamma_range)
c = scipy.special.gamma(3.0/gamma_range)
prec_gammas = a/(b*c)

def gauss_window_full(lw, sigma):
    sd = float(sigma)
    lw = int(lw)
    weights = [0.0] * (lw)
    sd *= sd
    center = (lw-1)/2.0
    for ii in range(lw):
        x = ii - center
        tmp = np.exp(-0.5 * float(x * x) / sd)
        weights[ii] = tmp
    weights /= np.sum(weights)
    return weights

def extract_aggd_features(imdata):

    if np.sum(np.abs(imdata)) == 0:
      return [np.inf]*6
    #flatten imdata
    imdata.shape = (len(imdata.flat),)
    imdata2 = imdata*imdata
    left_data = imdata2[imdata<0]
    right_data = imdata2[imdata>0]
    left_mean_sqrt = 0
    right_mean_sqrt = 0
    if len(left_data) > 0:
        left_mean_sqrt = np.sqrt(np.average(left_data))
    if len(right_data) > 0:
        right_mean_sqrt = np.sqrt(np.average(right_data))

    gamma_hat = left_mean_sqrt/right_mean_sqrt
    #solve r-hat norm
    r_hat = (np.average(np.abs(imdata))**2) / (np.average(imdata2))
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
    sigma_sq = np.average(imdata**2)
    E = np.average(np.abs(imdata))
    rho = sigma_sq/E**2
    pos = np.argmin(np.abs(nr_gam - rho));
    return gamma_range[pos], np.sqrt(sigma_sq)

def calc_image(image, avg_window):
    extend_mode = 'nearest'#'nearest'#'wrap'
    w, h = np.shape(image)
    mu_image = np.zeros((w, h))
    var_image = np.zeros((w, h))
    image = np.array(image).astype('float')
    scipy.ndimage.correlate1d(image, avg_window, 0, mu_image, mode=extend_mode)
    scipy.ndimage.correlate1d(mu_image, avg_window, 1, mu_image, mode=extend_mode)
    scipy.ndimage.correlate1d(image**2, avg_window, 0, var_image, mode=extend_mode)
    scipy.ndimage.correlate1d(var_image, avg_window, 1, var_image, mode=extend_mode)
    var_image = np.sqrt(np.abs(var_image - mu_image**2))
    return (image - mu_image)/(var_image + 1), var_image, mu_image

def paired_p(new_im):

    # shifts                   = [ 0 1;1 0 ;1 1;1 -1];
    #new_im /= 0.353257 #make the RV unit variance
    shift1 = np.roll(new_im.copy(), 1, axis=1)
    shift2 = np.roll(new_im.copy(), 1, axis=0)
    shift3 = np.roll(np.roll(new_im.copy(), 1, axis=0), 1, axis=1)
    shift4 = np.roll(np.roll(new_im.copy(), 1, axis=0), -1, axis=1)

    H_img = shift1 * new_im
    V_img = shift2 * new_im
    D1_img = shift3 * new_im
    D2_img = shift4 * new_im

    #return (V_img, H_img, D1_img, D2_img)
    #return (H_img, V_img, D1_img, D2_img)
    return (H_img, V_img, D1_img, D2_img)


def viideo_features(videoData, blocksize=(18, 18), blockoverlap=(8, 8), filterlength=7):
    """Computes VIIDEO features. [#f1]_

    Since this is a referenceless quality algorithm, only 1 video is needed. This function
    provides the raw features used by the algorithm.

    Parameters
    ----------
    videoData : ndarray
        Reference video, ndarray of dimension (T, M, N, C), (T, M, N), (M, N, C), or (M, N),
        where T is the number of frames, M is the height, N is width,
        and C is number of channels.

    blocksize : tuple (2,)
      
    blockoverlap: tuple (2,)

    Returns
    -------
    features : ndarray
        The individual features of the algorithm.

    References
    ----------

    .. [#f1] A. Mittal, M. A. Saad and A. C. Bovik, “VIIDEO Software Release", URL: http://live.ece.utexas.edu/research/quality/VIIDEO_release.zip, 2014.

    .. [#f2] A. Mittal, M. A. Saad and A. C. Bovik, "A ‘Completely Blind’ Video Integrity Oracle", submitted to IEEE Transactions in Image Processing, 2014.

    """

    videoData = vshape(videoData)

    T, M, N, C = videoData.shape

    assert C == 1, "viideo called with video having %d channels. Please supply only the luminance channel." % (C,)

    hf = gauss_window_full(filterlength, filterlength/6.0)
    blockstrideY = blocksize[0] - blockoverlap[0]
    blockstrideX = blocksize[1] - blockoverlap[1]
    Mn = M/blockstrideY
    Nn = N/blockstrideX

    # compute every 2 frames
    features = np.zeros((T/2, Mn, Nn, 28), dtype=np.float32)
    for k in range(T/2):
      frame1 = videoData[k*2, :, :, 0]
      frame2 = videoData[k*2+1, :, :, 0]

      diff = frame1 - frame2

      for itr in range(0, 2):
        mscn,_,mu= calc_image(diff, hf)

        h, v, d1, d2 = paired_p(mscn)
        
        for i in range(Mn):
          for j in range(Nn):
            yp = i*blockstrideY
            xp = j*blockstrideX
            patch = mscn[yp:yp+blocksize[0], xp:xp+blocksize[1]].copy()
            ph = h[yp:yp+blocksize[0], xp:xp+blocksize[1]].copy()
            pv = v[yp:yp+blocksize[0], xp:xp+blocksize[1]].copy()
            pd1 = d1[yp:yp+blocksize[0], xp:xp+blocksize[1]].copy()
            pd2 = d2[yp:yp+blocksize[0], xp:xp+blocksize[1]].copy()
            shape, _, bl, br, _, _ = extract_aggd_features(patch)
            shapeh, _, blh, brh, _, _ = extract_aggd_features(ph)
            shapev, _, blv, brv, _, _ = extract_aggd_features(pv)
            shaped1, _, bld1, brd1, _, _ = extract_aggd_features(pd1)
            shaped2, _, bld2, brd2, _, _ = extract_aggd_features(pd2)

            features[k, i, j, itr*14:(itr+1)*14] = np.array([
              shape, (bl + br)/2.0,
              shapeh, blh, brh,
              shapev, blv, brv,
              shaped1, bld1, brd1,
              shaped2, bld2, brd2,
            ])
        diff = mu

    return features
