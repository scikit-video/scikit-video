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

def motion_feature_extraction(frames):
    # setup
    frames = frames.astype(np.float32)
    mblock=10
    h = gen_gauss_window(2, 0.5)
    # step 1: motion vector calculation
    motion_vectors = blockMotion(frames, method='N3SS', mbSize=mblock, p=np.int(1.5*mblock))
    motion_vectors = motion_vectors.astype(np.float32)

    # step 2: compute coherency
    Eigens = np.zeros((motion_vectors.shape[0], motion_vectors.shape[1], motion_vectors.shape[2], 2), dtype=np.float32)
    for i in range(motion_vectors.shape[0]):
      motion_frame = motion_vectors[i]

      upper_left = np.zeros_like(motion_frame[:, :, 0])
      lower_right= np.zeros_like(motion_frame[:, :, 0])
      off_diag = np.zeros_like(motion_frame[:, :, 0])
      scipy.ndimage.correlate1d(motion_frame[:, :, 0]**2, h, 0, upper_left, mode='reflect') 
      scipy.ndimage.correlate1d(upper_left, h, 1, upper_left, mode='reflect') 
      scipy.ndimage.correlate1d(motion_frame[:, :, 1]**2, h, 0, lower_right, mode='reflect') 
      scipy.ndimage.correlate1d(lower_right, h, 1, lower_right, mode='reflect') 
      scipy.ndimage.correlate1d(motion_frame[:, :, 1]*motion_frame[:, :, 0], h, 0, off_diag, mode='reflect') 
      scipy.ndimage.correlate1d(off_diag, h, 1, off_diag, mode='reflect')

      for y in range(motion_vectors.shape[1]):
        for x in range(motion_vectors.shape[2]):
          mat = np.array([
            [upper_left[y, x], off_diag[y, x]],
            [off_diag[y, x], lower_right[y, x]],
          ])
          w, _ = np.linalg.eig(mat)
          Eigens[i, y, x] = w 

    num = (Eigens[:, :, :, 0] - Eigens[:, :, :, 1])**2
    den = (Eigens[:, :, :, 0] + Eigens[:, :, :, 1])**2

    Coh10x10 = np.zeros_like(num)
    Coh10x10[den!=0] = num[den!=0] / den[den!=0]

    meanCoh10x10 = np.mean(Coh10x10)

    # step 3: global motion
    mode10x10 = np.zeros((motion_vectors.shape[0]), dtype=np.float32)
    mean10x10 = np.zeros((motion_vectors.shape[0]), dtype=np.float32)
    for i in range(motion_vectors.shape[0]):
      motion_frame = motion_vectors[i]
      motion_amplitude = np.sqrt(motion_vectors[i, :, :, 0]**2 + motion_vectors[i, :, :, 1]**2) 
      mode10x10[i] = scipy.stats.mode(motion_amplitude, axis=None)[0]
      mean10x10[i] = np.mean(motion_amplitude)

    motion_diff = np.abs(mode10x10 - mean10x10)
    G = np.mean(motion_diff) / (1 + np.mean(mode10x10))

    return np.array([meanCoh10x10, G])

def _extract_subband_feats(mscncoefs):
    # alpha_m,  = extract_ggd_features(mscncoefs)
    alpha_m, N, bl, br, lsq, rsq = aggd_features(mscncoefs.copy())
    pps1, pps2, pps3, pps4 = paired_product(mscncoefs)
    alpha1, N1, bl1, br1, lsq1, rsq1 = aggd_features(pps1)
    alpha2, N2, bl2, br2, lsq2, rsq2 = aggd_features(pps2)
    alpha3, N3, bl3, br3, lsq3, rsq3 = aggd_features(pps3)
    alpha4, N4, bl4, br4, lsq4, rsq4 = aggd_features(pps4)
    # print bl1, br1
    # print bl2, br2
    # print bl3, br3
    # print bl4, br4
    # exit(0)
    return np.array([alpha_m, (bl+br)/2.0]), np.array([
            alpha1, N1, bl1, br1,  # (V)
            alpha2, N2, bl2, br2,  # (H)
            alpha3, N3, bl3, br3,  # (D1)
            alpha4, N4, bl4, br4,  # (D2)
    ])

def extract_on_patches(img, blocksizerow, blocksizecol):
    h, w = img.shape
    blocksizerow = np.int(blocksizerow)
    blocksizecol = np.int(blocksizecol)
    patches = []
    for j in range(0, np.int(h-blocksizerow+1), np.int(blocksizerow)):
        for i in range(0, np.int(w-blocksizecol+1), np.int(blocksizecol)):
            patch = img[j:j+blocksizerow, i:i+blocksizecol]
            patches.append(patch)

    patches = np.array(patches)
    
    patch_features = []
    for p in patches:
        mscn_features, pp_features = _extract_subband_feats(p)
        patch_features.append(np.hstack((mscn_features, pp_features)))
    patch_features = np.array(patch_features)

    return patch_features

def computequality(img, blocksizerow, blocksizecol, mu_prisparam, cov_prisparam):
    img = img[:, :, 0]
    h, w = img.shape

    if (h < blocksizerow) or (w < blocksizecol):
        print("Input frame is too small")
        exit(0)

    # ensure that the patch divides evenly into img
    hoffset = (h % blocksizerow)
    woffset = (w % blocksizecol)

    if hoffset > 0: 
        img = img[:-hoffset, :]
    if woffset > 0:
        img = img[:, :-woffset]

    img = img.astype(np.float32)
    img2 = scipy.misc.imresize(img, 0.5, interp='bicubic', mode='F')

    mscn1, var, mu = compute_image_mscn_transform(img, extend_mode='nearest')
    mscn1 = mscn1.astype(np.float32)

    mscn2, _, _ = compute_image_mscn_transform(img2, extend_mode='nearest')
    mscn2 = mscn2.astype(np.float32)

    feats_lvl1 = extract_on_patches(mscn1, blocksizerow, blocksizecol)
    feats_lvl2 = extract_on_patches(mscn2, blocksizerow/2, blocksizecol/2)

    # stack the scale features
    feats = np.hstack((feats_lvl1, feats_lvl2))# feats_lvl3))

    mu_distparam = np.mean(feats, axis=0)
    cov_distparam = np.cov(feats.T)

    invcov_param = np.linalg.pinv((cov_prisparam + cov_distparam)/2)

    xd = mu_prisparam - mu_distparam 
    quality = np.sqrt(np.dot(np.dot(xd, invcov_param), xd.T))[0][0]

    return np.hstack((mu_distparam, [quality]))


def compute_niqe_features(frames):
    blocksizerow = 96
    blocksizecol = 96

    T, M, N, C = frames.shape
    assert ((M >= blocksizerow*2) & (N >= blocksizecol*2)), "Video too small for NIQE extraction"

    module_path = dirname(__file__)
    params = scipy.io.loadmat(join(module_path, 'data', 'frames_modelparameters.mat'))
    mu_prisparam = params['mu_prisparam']
    cov_prisparam = params['cov_prisparam']

    niqe_features = np.zeros((frames.shape[0]-10, 37))
    idx = 0
    for i in range(5, frames.shape[0]-5):
      niqe_features[idx] = computequality(frames[i], blocksizerow, blocksizecol, mu_prisparam, cov_prisparam)
      idx += 1

    niqe_features = np.mean(niqe_features, axis=0)
    return niqe_features

def temporal_dc_variation_feature_extraction(frames):
    frames = frames.astype(np.float32)
    mblock=16
    mbsize=16
    ih = np.int(frames.shape[1]/mbsize)*mbsize
    iw = np.int(frames.shape[2]/mbsize)*mbsize
    # step 1: motion vector calculation
    motion_vectors = blockMotion(frames, method='N3SS', mbSize=mblock, p=7)
    # step 2: compensated temporal dct differences
    dct_motion_comp_diff = np.zeros((motion_vectors.shape[0], motion_vectors.shape[1], motion_vectors.shape[2]), dtype=np.float32)
    for i in range(motion_vectors.shape[0]):
      for y in range(motion_vectors.shape[1]):
        for x in range(motion_vectors.shape[2]):
          patchP = frames[i+1, y*mblock:(y+1)*mblock, x*mblock:(x+1)*mblock, 0].astype(np.float32)
          patchI = frames[i, y*mblock+motion_vectors[i, y, x, 0]:(y+1)*mblock+motion_vectors[i, y, x, 0], x*mblock+motion_vectors[i, y, x, 1]:(x+1)*mblock+motion_vectors[i, y, x, 1], 0].astype(np.float32)
          diff = patchP - patchI
          t = scipy.fftpack.dct(scipy.fftpack.dct(diff, axis=1, norm='ortho'), axis=0, norm='ortho')
          #dct_motion_comp_diff[i, y*mblock:(y+1)*mblock, x*mblock:(x+1)*mblock] = t 
          dct_motion_comp_diff[i, y, x] = t[0, 0] 

    dct_motion_comp_diff = dct_motion_comp_diff.reshape(motion_vectors.shape[0], -1) 

    std_dc = np.std(dct_motion_comp_diff, axis=1)
    dt_dc_temp = np.abs(std_dc[1:] - std_dc[:-1])

    dt_dc_measure1 = np.mean(dt_dc_temp)
    return np.array([dt_dc_measure1])

def NSS_spectral_ratios_feature_extraction(frames):
    def zigzag(data):
      nrows, ncols = data.shape
      d=sum([list(data[::-1,:].diagonal(i)[::(i+nrows+1)%2*-2+1])for i in range(-nrows,nrows+len(data[0]))], [])
      return np.array(d)

    mblock=5

    # step 1: compute local dct frame differences
    dct_diff5x5 = np.zeros((frames.shape[0]-1, np.int(frames.shape[1]/mblock), np.int(frames.shape[2]/mblock),mblock**2), dtype=np.float32)
    for i in range(dct_diff5x5.shape[0]):
      for y in range(dct_diff5x5.shape[1]):
        for x in range(dct_diff5x5.shape[2]):
          diff = frames[i+1, y*mblock:(y+1)*mblock, x*mblock:(x+1)*mblock].astype(np.float32) - frames[i, y*mblock:(y+1)*mblock, x*mblock:(x+1)*mblock].astype(np.float32)  
          t = scipy.fftpack.dct(scipy.fftpack.dct(diff, axis=1, norm='ortho'), axis=0, norm='ortho')
          dct_diff5x5[i, y, x] = t.ravel()
    dct_diff5x5 = dct_diff5x5.reshape(dct_diff5x5.shape[0],dct_diff5x5.shape[1] * dct_diff5x5.shape[2], -1)

    # step 2: compute gamma
    g = np.arange(0.03, 10+0.001, 0.001)
    r = (scipy.special.gamma(1/g) * scipy.special.gamma(3/g)) / (scipy.special.gamma(2/g)**2)

    gamma_matrix = np.zeros((dct_diff5x5.shape[0], mblock**2), dtype=np.float32) 
    for i in range(dct_diff5x5.shape[0]):
      for s in range(mblock**2):
        temp = dct_diff5x5[i, :, s]
        mean_gauss = np.mean(temp)
        var_gauss = np.var(temp, ddof=1)
        mean_abs = np.mean(np.abs(temp - mean_gauss))**2
        rho = var_gauss/(mean_abs + 1e-7)

        gamma_gauss = 11
        for x in range(len(g)-1):
          if (rho <= r[x]) and (rho > r[x+1]):
            gamma_gauss = g[x]
            break
        gamma_matrix[i, s] = gamma_gauss

    gamma_matrix = gamma_matrix.reshape(dct_diff5x5.shape[0], mblock, mblock)

    #zigzag = lambda N,w,h:[N[i*w+s-i]for s in range(w+h+1)for i in range(h)[::s%2*2-1]if-1<s-i<w]

    freq_bands = np.zeros((dct_diff5x5.shape[0], mblock**2))
    for i in range(dct_diff5x5.shape[0]):
      freq_bands[i] = zigzag(gamma_matrix[i]) 

    lf_gamma5x5 = freq_bands[:, 1:np.int((mblock**2-1)/3)+1]
    mf_gamma5x5 = freq_bands[:, np.int((mblock**2-1)/3)+1:2*np.int((mblock**2-1)/3)+1]
    hf_gamma5x5 = freq_bands[:, np.int(2*(mblock**2-1)/3)+1:]

    geomean_lf_gam = scipy.stats.mstats.gmean(lf_gamma5x5.T)
    geomean_mf_gam = scipy.stats.mstats.gmean(mf_gamma5x5.T)
    geomean_hf_gam = scipy.stats.mstats.gmean(hf_gamma5x5.T)

    geo_high_ratio = scipy.stats.mstats.gmean(geomean_hf_gam/(0.1 + (geomean_mf_gam + geomean_lf_gam)/2))
    geo_low_ratio = scipy.stats.mstats.gmean(geomean_mf_gam/(0.1 + geomean_lf_gam))
    geo_HL_ratio = scipy.stats.mstats.gmean(geomean_hf_gam/(0.1 + geomean_lf_gam))
    geo_HM_ratio = scipy.stats.mstats.gmean(geomean_hf_gam/(0.1 + geomean_mf_gam))
    geo_hh_ratio = scipy.stats.mstats.gmean(((geomean_hf_gam + geomean_mf_gam)/2)/(0.1 + geomean_lf_gam))

    mean_dc = np.mean(dct_diff5x5[:, :, 0], axis=1) 
    dt_dc_measure2 = np.mean(np.abs(mean_dc[1:] - mean_dc[:-1]))
    
    return np.array([dt_dc_measure2, geo_HL_ratio, geo_HM_ratio, geo_hh_ratio, geo_high_ratio, geo_low_ratio])

def videobliinds_features(videoData):
    """Computes Video Bliinds features. [#f1]_

    Since this is a referenceless quality algorithm, only 1 video is needed. This function
    provides the raw features used by the algorithm.

    Parameters
    ----------
    videoData : ndarray
        Reference video, ndarray of dimension (T, M, N, C), (T, M, N), (M, N, C), or (M, N),
        where T is the number of frames, M is the height, N is width,
        and C is number of channels.

    Returns
    -------
    features : ndarray, shape (46,)
        |  The individual features of the algorithm. The features are arranged as follows:
        |  
        |    features[:36] : spatial niqe vector averaged over the video, shape (36,)
        |    features[36] : niqe naturalness score, shape (1,)
        |    features[37:39] : DC measurements between frames, shape (2,)
        |    features[39:44] : Natural Video Statistics, shape (5,)
        |    features[44] : Motion coherence, shape (1,)
        |    features[45] : Global motion, shape (1,)

    References
    ----------

    .. [#f1] M. Saad and A.C. Bovik, "Blind prediction of natural video quality" IEEE Transactions on Image Processing, December 2013.

    """

    videoData = vshape(videoData)

    T, M, N, C = videoData.shape

    assert C == 1, "videobliinds called with video having %d channels. Please supply only the luminance channel." % (C,)

    dt_dc_measure1 = temporal_dc_variation_feature_extraction(videoData)
    spectral_features = NSS_spectral_ratios_feature_extraction(videoData)
    temporal_features = motion_feature_extraction(videoData)
    niqe_features = compute_niqe_features(videoData)

    features = np.hstack((
      niqe_features,
      np.log(1+dt_dc_measure1),
      np.log(1+spectral_features),
      np.log(1+temporal_features),
    ))

    return features
