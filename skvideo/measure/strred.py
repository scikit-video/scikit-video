from ..utils import *
import numpy as np
import scipy.ndimage


def est_params(frame, blk, sigma_nn):
    h, w = frame.shape
    sizeim = np.floor(np.array(frame.shape)/blk) * blk
    sizeim = sizeim.astype(np.int)
    #sizeim += 1

    frame = frame[:sizeim[0], :sizeim[1]]

    #paired_products
    temp = []
    for u in range(blk):
      for v in range(blk):
        temp.append(np.ravel(frame[v:(sizeim[0]-(blk-v)+1), u:(sizeim[1]-(blk-u)+1)]))
    temp = np.array(temp)

    cov_mat = np.cov(temp, bias=1)

    # force PSD
    eigval, eigvec = np.linalg.eig(cov_mat)
    Q = np.matrix(eigvec)
    xdiag = np.matrix(np.diag(np.maximum(eigval, 0)))
    cov_mat = Q*xdiag*Q.T

    temp = []
    for u in range(blk):
      for v in range(blk):
        temp.append(np.ravel(frame[v::blk, u::blk]))
    temp = np.array(temp)

    V,d = np.linalg.eig(cov_mat)

    # Estimate local variance
    ss = np.zeros((sizeim[0]/blk, sizeim[1]/blk), dtype=np.float32)
    if np.max(V) > 0:
      ss = np.dot(np.linalg.inv(cov_mat), temp)
      ss = np.sum(np.multiply(ss, temp) / (blk**2), axis=0)
      ss = ss.reshape(sizeim/blk)

    V = V[V>0]
    # Compute entropy
    ent = np.zeros_like(ss)
    for u in range(V.shape[0]):
      ent += np.log2(ss * V[u] + sigma_nn) + np.log(2*np.pi*np.exp(1))

    return ss, ent


def extract_info(frame1, frame2):
    blk = 3
    sigma_nsq = 0.1
    sigma_nsqt = 0.1
    band = 0

    model = SpatialSteerablePyramid(height=6)
    dframe1 = model.decompose(frame1, filtfile="sp5Filters")
    dframe2 = model.decompose(frame2, filtfile="sp5Filters")
    y1 = dframe1[4][band]
    y2 = dframe2[4][band]

    ydiff = y1 - y2

    ss, q = est_params(y1, blk, sigma_nsq)
    ssdiff, qdiff = est_params(ydiff, blk, sigma_nsqt)

    spatial = np.multiply(q, np.log2(1 + ss))
    temporal = np.multiply(qdiff, np.multiply(np.log2(1 + ss), np.log2(1 + ssdiff)))

    return spatial, temporal



def strred(referenceVideoData, distortedVideoData):
    """Computes Spatio-Temporal Reduced Reference Entropic Differencing (ST-RRED) Index. [#f1]_

    Both video inputs are compared over frame differences, with quality determined by
    differences in the entropy per subband.

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

    Returns
    -------
    strred_array : ndarray
        The ST-RRED results, ndarray of dimension ((T-1)/2, 4), where T
        is the number of frames.  Each row holds spatial score, temporal score, 
        reduced reference spatial score, and reduced reference temporal score.

    strred : float
        The final ST-RRED score if all blocks are averaged after comparing 
        reference and distorted data. This is close to full-reference.

    strredssn : float
        The final ST-RRED score if all blocks are averaged before comparing 
        reference and distorted data. This is the reduced reference score.

    References
    ----------

    .. [#f1] R. Soundararajan and A. C. Bovik, "Video Quality Assessment by Reduced Reference Spatio-temporal Entropic Differencing," IEEE Transactions on Circuits and Systems for Video Technology, April 2013.

    """

    referenceVideoData = vshape(referenceVideoData)
    distortedVideoData = vshape(distortedVideoData)

    assert(referenceVideoData.shape == distortedVideoData.shape)

    T, M, N, C = referenceVideoData.shape

    assert C == 1, "strred called with videos containing %d channels. Please supply only the luminance channel" % (C,)

    referenceVideoData = referenceVideoData[:, :, :, 0]
    distortedVideoData = distortedVideoData[:, :, :, 0]

    rreds = []
    rredt = []

    rredssn = []
    rredtsn = []

    for i in range(0, T-1, 2):
      refFrame1 = referenceVideoData[i]
      refFrame2 = referenceVideoData[i+1]

      disFrame1 = distortedVideoData[i]
      disFrame2 = distortedVideoData[i+1]

      spatialRef, temporalRef = extract_info(refFrame1, refFrame2) 
      spatialDis, temporalDis = extract_info(disFrame1, disFrame2) 

      rreds.append(np.mean(np.abs(spatialRef - spatialDis)))
      rredt.append(np.mean(np.abs(temporalRef - temporalDis)))

      rredssn.append(np.abs(np.mean(spatialRef - spatialDis)))
      rredtsn.append(np.abs(np.mean(temporalRef - temporalDis)))

    rreds = np.array(rreds)
    rredt = np.array(rredt)
    rredssn = np.array(rredssn)
    rredtsn = np.array(rredtsn)

    srred = np.mean(rreds)
    trred = np.mean(rredt)
    srredsn = np.mean(rredssn)
    trredsn = np.mean(rredtsn)

    strred = srred * trred
    strredsn = srredsn * trredsn

    return np.hstack((rreds.reshape(-1, 1), rredt.reshape(-1, 1), rredssn.reshape(-1, 1), rredtsn.reshape(-1, 1))), strred, strredsn
