from ..utils import *

import numpy as np
import scipy.misc
import scipy.io

from os.path import dirname
from os.path import join

# only used during training 
#from skimage.util.shape import view_as_windows

def _niqe_extract_subband_feats(mscncoefs):
    # alpha_m,  = extract_ggd_features(mscncoefs)
    alpha_m, N, bl, br, lsq, rsq = aggd_features(mscncoefs.copy())
    pps1, pps2, pps3, pps4 = paired_product(mscncoefs)
    alpha1, N1, bl1, br1, lsq1, rsq1 = aggd_features(pps1)
    alpha2, N2, bl2, br2, lsq2, rsq2 = aggd_features(pps2)
    alpha3, N3, bl3, br3, lsq3, rsq3 = aggd_features(pps3)
    alpha4, N4, bl4, br4, lsq4, rsq4 = aggd_features(pps4)
    return np.array([alpha_m, (bl+br)/2.0,
            alpha1, N1, bl1, br1,  # (V)
            alpha2, N2, bl2, br2,  # (H)
            alpha3, N3, bl3, bl3,  # (D1)
            alpha4, N4, bl4, bl4,  # (D2)
    ])

def get_patches_train_features(img, patch_size, stride=8):
    return _get_patches_generic(img, patch_size, 1, stride)

def get_patches_test_features(img, patch_size, stride=8):
    return _get_patches_generic(img, patch_size, 0, stride)

def extract_on_patches(img, patch_size):
    h, w = img.shape
    patch_size = np.int(patch_size)
    patches = []
    for j in range(0, h-patch_size+1, patch_size):
        for i in range(0, w-patch_size+1, patch_size):
            patch = img[j:j+patch_size, i:i+patch_size]
            patches.append(patch)

    patches = np.array(patches)
    
    patch_features = []
    for p in patches:
        patch_features.append(_niqe_extract_subband_feats(p))
    patch_features = np.array(patch_features)

    return patch_features

def _get_patches_generic(img, patch_size, is_train, stride):
    h, w = np.shape(img)
    if h < patch_size or w < patch_size:
        print("Input image is too small")
        exit(0)

    # ensure that the patch divides evenly into img
    hoffset = (h % patch_size)
    woffset = (w % patch_size)

    if hoffset > 0: 
        img = img[:-hoffset, :]
    if woffset > 0:
        img = img[:, :-woffset]


    img = img.astype(np.float32)
    img2 = scipy.misc.imresize(img, 0.5, interp='bicubic', mode='F')

    mscn1, var, mu = compute_image_mscn_transform(img)
    mscn1 = mscn1.astype(np.float32)

    mscn2, _, _ = compute_image_mscn_transform(img2)
    mscn2 = mscn2.astype(np.float32)


    feats_lvl1 = extract_on_patches(mscn1, patch_size)
    feats_lvl2 = extract_on_patches(mscn2, patch_size/2)

    feats = np.hstack((feats_lvl1, feats_lvl2))# feats_lvl3))

    #if is_train:
    #    variancefield = view_as_windows(var, (patch_size, patch_size), step=patch_size)
    #    variancefield = variancefield.reshape(-1, patch_size, patch_size)
    #    avg_variance = np.mean(np.mean(variancefield, axis=2), axis=1)
    #    avg_variance /= np.max(avg_variance)
    #    feats = feats[avg_variance > 0.75]

    return feats

def niqe(inputVideoData):
    """Computes Naturalness Image Quality Evaluator. [#f1]_

    Input a video of any quality and get back its distance frame-by-frame
    from naturalness.

    Parameters
    ----------
    inputVideoData : ndarray
        Input video, ndarray of dimension (T, M, N, C), (T, M, N), (M, N, C), or (M, N),
        where T is the number of frames, M is the height, N is width,
        and C is number of channels. Here C is only allowed to be 1.

    Returns
    -------
    niqe_array : ndarray
        The niqe results, ndarray of dimension (T,), where T
        is the number of frames

    References
    ----------

    .. [#f1] Mittal, Anish, Rajiv Soundararajan, and Alan C. Bovik. "Making a 'completely blind' image quality analyzer." IEEE Signal Processing Letters 20.3 (2013): 209-212.

    """
    # cache
    patch_size = 96
    module_path = dirname(__file__)

    # TODO: memoize
    params = scipy.io.loadmat(join(module_path, 'data', 'niqe_image_params.mat'))
    pop_mu = np.ravel(params["pop_mu"])
    pop_cov = params["pop_cov"]


    # load the training data
    inputVideoData = vshape(inputVideoData)

    T, M, N, C = inputVideoData.shape

    assert C == 1, "niqe called with videos containing %d channels. Please supply only the luminance channel" % (C,)
    assert M > (patch_size*2+1), "niqe called with small frame size, requires > 192x192 resolution video using current training parameters"
    assert N > (patch_size*2+1), "niqe called with small frame size, requires > 192x192 resolution video using current training parameters"

    niqe_scores = np.zeros(T, dtype=np.float32)

    for t in range(T):
      feats = get_patches_test_features(inputVideoData[t, :, :, 0], patch_size)
      sample_mu = np.mean(feats, axis=0)
      sample_cov = np.cov(feats.T)

      X = sample_mu - pop_mu
      covmat = ((pop_cov+sample_cov)/2.0)
      pinvmat = scipy.linalg.pinv(covmat)
      niqe_scores[t] = np.sqrt(np.dot(np.dot(X, pinvmat), X))

    return niqe_scores
