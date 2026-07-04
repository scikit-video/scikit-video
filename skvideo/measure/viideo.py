import numpy as np
import scipy.ndimage
import scipy.special

from ..utils import vshape

# VIIDEO's own AGGD shape grid (estimateaggdparam.m: gam = 0.2:0.01:5).
# NOTE: this is deliberately NOT skvideo's shared aggd_features grid
# (0.2:0.001:10, which is NIQE's). VIIDEO's features ARE the quantized shape
# parameters, so reproducing the reference requires the reference grid.
_VIIDEO_GAM = np.arange(0.2, 5.0 + 1e-9, 0.01)
_VIIDEO_PREC = (scipy.special.gamma(2.0 / _VIIDEO_GAM) ** 2) / (
    scipy.special.gamma(1.0 / _VIIDEO_GAM) * scipy.special.gamma(3.0 / _VIIDEO_GAM))


def _gaussian2d(n, sigma):
    """fspecial('gaussian', [n n], sigma), normalized to sum 1."""
    ax = np.arange(n, dtype=np.float64) - (n - 1) / 2.0
    g = np.exp(-(ax ** 2) / (2.0 * sigma ** 2))
    k = np.outer(g, g)
    return k / k.sum()


_SHIFTS = [(1, 0), (0, 1), (1, 1), (1, -1)]  # computeVIIDEOscore.m line 87


def _aggd_blocks(P):
    """estimateaggdparam.m over a stack of flattened blocks P (nb, npix), float64.

    Returns (nb, 3) = [alpha, betal, betar]. Faithful to the reference:
      - all-zero block          -> [inf, inf, inf]   (marked invalid)
      - one-sided block (no -ve or no +ve samples) -> betal/betar = NaN
    Both are dropped downstream (the reference deletes nonfinite feature rows).
    Right tail uses strictly > 0 (zeros belong to neither tail).
    """
    absP = np.abs(P)
    zero = absP.sum(axis=1) == 0
    neg = P < 0
    pos = P > 0
    nneg = neg.sum(axis=1)
    npos = pos.sum(axis=1)
    P2 = P * P
    with np.errstate(divide="ignore", invalid="ignore"):
        leftstd = np.sqrt(np.where(nneg > 0, (P2 * neg).sum(axis=1) / nneg, np.nan))
        rightstd = np.sqrt(np.where(npos > 0, (P2 * pos).sum(axis=1) / npos, np.nan))
        gammahat = leftstd / rightstd
        rhat = (absP.mean(axis=1) ** 2) / P2.mean(axis=1)
        rhatnorm = (rhat * (gammahat ** 3 + 1) * (gammahat + 1)) / ((gammahat ** 2 + 1) ** 2)
    d = (_VIIDEO_PREC[None, :] - rhatnorm[:, None]) ** 2
    d = np.where(np.isnan(d), np.inf, d)  # MATLAB min over NaN -> first index
    alpha = _VIIDEO_GAM[np.argmin(d, axis=1)]
    rr = np.sqrt(scipy.special.gamma(1.0 / alpha) / scipy.special.gamma(3.0 / alpha))
    out = np.stack([alpha, leftstd * rr, rightstd * rr], axis=1)
    out[zero] = np.inf
    return out


def _blkproc_aggd(im, bs, ov):
    """blkproc(im, [bs bs], [ov ov], @estimateaggdparam): each distinct bs x bs
    block is extended by an ov-pixel border on ALL sides (zero-padded at image
    edges), giving an (bs+2*ov) square patch. Blocks are always full size - the
    reference never truncates edge blocks.
    """
    H, W = im.shape
    Mb = -(-H // bs)
    Nb = -(-W // bs)
    padded = np.zeros((Mb * bs + 2 * ov, Nb * bs + 2 * ov), dtype=np.float64)
    padded[ov:ov + H, ov:ov + W] = im
    side = bs + 2 * ov
    patches = np.empty((Mb * Nb, side * side), dtype=np.float64)
    n = 0
    for j in range(Nb):
        for i in range(Mb):
            patches[n] = padded[i * bs:i * bs + side, j * bs:j * bs + side].ravel()
            n += 1
    return _aggd_blocks(patches)  # (Mb*Nb, 3)


def _featurevector(y1, y2, bs, ov, window):
    """computeVIIDEOfeaturevector: (nblocks, 28) for one frame pair."""
    cols = []
    X = y1 - y2
    for _scale in range(2):
        mu = scipy.ndimage.correlate(X, window, mode="nearest")
        sigma = np.sqrt(np.abs(
            scipy.ndimage.correlate(X * X, window, mode="nearest") - mu * mu))
        structdis = (X - mu) / (sigma + 1.0)
        f = _blkproc_aggd(structdis, bs, ov)
        cols.append(f[:, 0:1])
        cols.append(((f[:, 1] + f[:, 2]) / 2.0)[:, None])
        for sh in _SHIFTS:
            shifted = np.roll(structdis, sh, axis=(0, 1))
            cols.append(_blkproc_aggd(structdis * shifted, bs, ov))
        X = mu
    return np.concatenate(cols, axis=1)  # (nblocks, 28)


def viideo_features(videoData, blocksize=(18, 18), blockoverlap=(8, 8), filterlength=7):
    """Computes VIIDEO features. [#f1]_ [#f2]_

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
        The individual features of the algorithm, shape (T//2, nblocks, 28).

    References
    ----------

    .. [#f1] A. Mittal, M. A. Saad and A. C. Bovik, "VIIDEO Software Release", URL: http://live.ece.utexas.edu/research/quality/VIIDEO_release.zip, 2014.

    .. [#f2] A. Mittal, M. A. Saad and A. C. Bovik, "A 'Completely Blind' Video Integrity Oracle", IEEE Transactions on Image Processing, 2016.

    """
    videoData = vshape(videoData)
    T, M, N, C = videoData.shape
    if not (C == 1):
        raise ValueError("viideo called with video having %d channels. Please supply only the luminance channel." % (C,))

    window = _gaussian2d(filterlength, filterlength / 6.0)
    feats = []
    for k in range(T // 2):
        y1 = videoData[2 * k, :, :, 0].astype(np.float64)
        y2 = videoData[2 * k + 1, :, :, 0].astype(np.float64)
        feats.append(_featurevector(y1, y2, blocksize[0], blockoverlap[0], window))
    return np.array(feats)


def viideo_score(videoData, blocksize=(18, 18), blockoverlap=(8, 8), filterlength=7):
    """Computes VIIDEO score. [#f1]_ [#f2]_

    Since this is a referenceless quality algorithm, only 1 video is needed. This function
    provides the score computed by the algorithm. Higher score = lower quality.

    This implementation is a faithful port of the LIVE reference
    ``computeVIIDEOscore.m`` (verified to match it to ~1e-5 on the release demo
    clips). It does NOT reuse skvideo's shared ``aggd_features`` (which carries
    NIQE's shape grid); VIIDEO requires its own grid and special-value handling.

    Parameters
    ----------
    videoData : ndarray
        Video, ndarray of dimension (T, M, N, C), (T, M, N), (M, N, C), or (M, N).

    blocksize : tuple (2,)
        Spatial block size. NOTE: the defaults (18, 18)/(8, 8) are the QCIF demo
        configuration shipped in the LIVE release (``testscript.m``). The block
        size used to produce the paper's LIVE VQA results (Table II) was 72; the
        spatial overlap at that block size is not stated in the paper or release
        (the demo ratio 8/18 implies ~32, but ~32 vs 36 is not separable within
        sampling noise). Choose block/overlap to match your intended reference.

    blockoverlap: tuple (2,)

    Returns
    -------
    score : float
        The video quality score.

    References
    ----------

    .. [#f1] A. Mittal, M. A. Saad and A. C. Bovik, "VIIDEO Software Release", URL: http://live.ece.utexas.edu/research/quality/VIIDEO_release.zip, 2014.

    .. [#f2] A. Mittal, M. A. Saad and A. C. Bovik, "A 'Completely Blind' Video Integrity Oracle", IEEE Transactions on Image Processing, 2016.

    """
    features = viideo_features(videoData, blocksize=blocksize,
                              blockoverlap=blockoverlap, filterlength=filterlength)
    npairs = features.shape[0]
    length = npairs - 1
    gap = length // 10
    step = max(int(round(gap / 2.0)), 1)

    scorevect = []
    for itr in range(0, length, step):
        f1_cum = []
        f2_cum = []
        for t in range(itr, min(itr + gap, length - 1) + 1):
            low1 = features[t, :, 2:14]
            low2 = features[t + 1, :, 2:14]
            high1 = features[t, :, 16:28]
            high2 = features[t + 1, :, 16:28]
            vec1 = np.abs(low1 - low2)
            vec2 = np.abs(high1 - high2)
            # delete any block (row) with a nonfinite feature in either subband
            bad = np.any(~np.isfinite(vec1) | ~np.isfinite(vec2), axis=1)
            if not bad.all():
                f1_cum.append(vec1[~bad])
                f2_cum.append(vec2[~bad])
        if f1_cum:
            F1 = np.vstack(f1_cum)
            F2 = np.vstack(f2_cum)
            C = np.empty(F1.shape[1])
            for c in range(F1.shape[1]):
                a, b = F1[:, c], F2[:, c]
                if len(a) < 2 or a.std() == 0 or b.std() == 0:
                    C[c] = np.nan  # corr of a constant column is undefined
                else:
                    C[c] = np.corrcoef(a, b)[0, 1]
            scorevect.append(np.mean(C))

    scorevect = np.array(scorevect, dtype=np.float64)
    change = np.abs(np.roll(scorevect, 1) - scorevect)
    return float(np.nanmean(scorevect) + np.nanmean(change))
