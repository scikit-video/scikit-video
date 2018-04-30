from ..utils import *
import numpy as np
import scipy.ndimage
import scipy.fftpack
import scipy.stats
import scipy.io
import sys

def Li3DDCT_features(videoData):
    """Computes No-reference features from the Spatiotemporal Statistics for Video Quality Assessment paper. [#f1]_

    Since this is a referenceless image quality algorithm, only 1 video is needed. This function provides the raw features pooled over an entire video.

    Parameters
    ----------
    videoData : ndarray
        Reference video, ndarray of dimension (T, M, N, C), (T, M, N), (M, N, C), or (M, N),
        where T is the number of frames, M is the height, N is width,
        and C is number of channels.

    Returns
    -------
    features : ndarray
        A matrix of shape (T, 36) of the computed features.

    References
    ----------

    .. [#f1] X. Li, Q. Guo and X. Lu, "Spatiotemporal Statistics for Video Quality Assessment," in IEEE Transactions on Image Processing, vol. 25, no. 7, pp. 3329-3342, July 2016.
    """

    videoData = vshape(videoData)

    T, M, N, C = videoData.shape

    assert C == 1, "called with video having %d channels. Please supply only the luminance channel." % (C,)
    assert T >= 4, "Only %d input frames. Please supply at least 4" % (T,)

    feats = np.zeros((63*5,), dtype=np.float32)
    newM = np.int32(np.floor(M/4)*4)
    newN = np.int32(np.floor(N/4)*4)

    frameSlices = np.arange(0, T-4, 4)
    Sfeats = np.zeros((len(frameSlices), 63), dtype=np.float32)
    Gammafeats = np.zeros((len(frameSlices), 63), dtype=np.float32)
    Energy1feats = np.zeros((len(frameSlices), 63), dtype=np.float32)
    Energy2feats = np.zeros((len(frameSlices), 63), dtype=np.float32)
    Distfeats = np.zeros((len(frameSlices), 63), dtype=np.float32)

    # scan using groups of 4 frames
    for idx, frameidx in enumerate(frameSlices):
      frames = videoData[frameidx:frameidx+4, :, :, 0].astype(np.float32)

      # ensure multiple of 4 frame width/height
      frames = frames[:, :newM, :newN]
      blocks0 = rolling_window(frames[0], (4, 4))[::2, ::2].reshape(-1, 4, 4)
      blocks1 = rolling_window(frames[1], (4, 4))[::2, ::2].reshape(-1, 4, 4)
      blocks2 = rolling_window(frames[2], (4, 4))[::2, ::2].reshape(-1, 4, 4)
      blocks3 = rolling_window(frames[3], (4, 4))[::2, ::2].reshape(-1, 4, 4)
      block3d = np.stack((blocks0, blocks1, blocks2, blocks3), axis=1)

      # 3d DCT
      block3dDCT = scipy.fftpack.dct(block3d, axis=1)
      block3dDCT = scipy.fftpack.dct(block3dDCT, axis=2)
      block3dDCT = scipy.fftpack.dct(block3dDCT, axis=3)
      block3dDCT = block3dDCT.reshape(-1, 64)
      # shave off the DC component
      block3dDCT = block3dDCT[:, 1:]

      # step 1
      mu = np.mean(np.abs(block3dDCT), axis=0)
      sig = np.std(np.abs(block3dDCT), axis=0)
      sig[sig==0] = 1e-6
      sk = mu/sig
      Sfeats[idx, :] = sk

      Energy1feats[idx, :] = np.mean(np.log2(block3dDCT**2+1e-6), axis=0)

      Nbins = 128
      hist3d = np.zeros((Nbins, 63))
      for i in range(63):
        a, _, _, _, _, _ = aggd_features(block3dDCT[:, i])
        Gammafeats[idx, i] = a
        hist, bins = np.histogram(np.abs(block3dDCT[:, i]), bins=Nbins, range=(0, 2**(16-1)-1))
        hist = hist.astype(np.float32)
        tmp = np.sum(hist)
        if tmp>0:
          hist /= np.sum(hist)
          hist3d[:, i] = hist

      meanHist3d = np.mean(hist3d, axis=1)

      for j in range(Nbins):
        nonzeros = hist3d[j, :]>0
        Energy2feats[idx, nonzeros] += -(hist3d[j, nonzeros] * np.log2(hist3d[j, nonzeros]))

      Distfeats[idx, :] = np.sum(np.abs(hist3d - meanHist3d.reshape(-1, 1)), axis=0)

      #feats[i, 18*0:18*1] = _extract_subband_feats(full_scale)
      #feats[i, 18*1:18*2] = _extract_subband_feats(half_scale)

    Sfeats = np.mean(Sfeats,axis=0)
    Gammafeats = np.mean(Gammafeats,axis=0)
    Energy1feats = np.mean(Energy1feats,axis=0)
    Energy2feats = np.mean(Energy2feats,axis=0)
    Distfeats = np.mean(Distfeats, axis=0)

    return np.hstack((Sfeats, Gammafeats, Energy1feats, Energy2feats, Distfeats))

