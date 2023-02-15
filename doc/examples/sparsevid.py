import matplotlib.pyplot as plt
import numpy as np
import scipy
import sklearn.linear_model
from matplotlib import gridspec
from sklearn.feature_extraction import image

import skvideo.datasets

try:
    xrange
except NameError:
    xrange = range

np.random.seed(0)

# use greedy K-SVD algorithm with OMP
def code_step(X, D):
  model = sklearn.linear_model.OrthogonalMatchingPursuit(
          n_nonzero_coefs=5, fit_intercept=False, normalize=False
  )
  #C = sklearn.
  model.fit(D.T, X.T)
  return model.coef_

def dict_step(X, C, D):
  unused_indices = []
  for k in xrange(D.shape[0]):
    usedidx = np.abs(C[:, k])>0

    if np.sum(usedidx) <= 1:
      print("Skipping filter #%d" % (k,))
      unused_indices.append(k)
      continue

    selectNotK = np.arange(D.shape[0]) != k
    used_coef = C[usedidx, :][:, selectNotK]

    E_kR = X[usedidx, :].T - np.dot(used_coef, D[selectNotK, :]).T

    U, S, V = scipy.sparse.linalg.svds(E_kR, k=1)

    # choose sign based on largest dot product
    choicepos = np.dot(D[k,:], U[:, 0])
    choiceneg = np.dot(D[k,:], -U[:, 0])

    if choicepos > choiceneg:
      D[k, :] = U[:, 0]
      C[usedidx, k] = S[0] * V[0, :]
    else:
      D[k, :] = -U[:, 0]
      C[usedidx, k] = -S[0] * V[0, :]


  # re-randomize filters that were not used
  for i in unused_indices:
    D[i, :] = np.random.normal(size=D.shape[1])
    D[i, :] /= np.sqrt(np.dot(D[i,:], D[i,:]))

  return D

def plot_weights(basis):
    n_filters, n_channels, height, width = basis.shape
    ncols = 10
    nrows = 10
    fig = plt.figure()
    gs = gridspec.GridSpec(nrows, ncols)
    rown = 0
    coln = 0
    for filter in xrange(n_filters):
            ax = fig.add_subplot(gs[rown, coln])
            mi = np.min(basis[filter, 0, :, :])
            ma = np.max(basis[filter, 0, :, :])
            ma = np.max((np.abs(mi), np.abs(ma)))
            mi = -ma
            ax.imshow(basis[filter, 0, :, :], vmin=mi, vmax=ma, cmap='Greys_r', interpolation='none')
            ax.xaxis.set_major_locator(plt.NullLocator())
            ax.yaxis.set_major_locator(plt.NullLocator())
            coln += 1
            if coln >= ncols:
                coln = 0
                rown += 1
    gs.tight_layout(fig, pad=0, h_pad=0, w_pad=0)
    fig.canvas.draw()
    buf, sz = fig.canvas.print_to_buffer()
    data = np.fromstring(buf, dtype=np.uint8).reshape(sz[1], sz[0], -1)[:, :, :3]
    plt.close()
    return data

# a 5 fps video encoded using x264
writer = skvideo.io.FFmpegWriter("sparsity.mp4", 
  inputdict={
    "-r": "10"
  },
  outputdict={
  '-vcodec': 'libx264', '-b': '30000000'
})

# open the first frame of bigbuckbunny
filename = skvideo.datasets.bigbuckbunny()
vidframe = skvideo.io.vread(filename, outputdict={"-pix_fmt": "gray"})[0, :, :, 0]

# initialize D
D = np.random.normal(size=(100, 7*7))
for i in range(D.shape[0]):
  D[i, :] /= np.sqrt(np.dot(D[i,:], D[i,:]))


X = image.extract_patches_2d(vidframe, (7, 7))
X = X.reshape(X.shape[0], -1).astype(float)

# sumsample about 10000 patches
X = X[np.random.permutation(X.shape[0])[:10000]]

for i in range(200):
  print("Iteration %d / %d" % (i, 200))
  C = code_step(X, D)
  D = dict_step(X, C, D)
  frame = plot_weights(D.reshape(100, 1, 7, 7))
  writer.writeFrame(frame)
writer.close()
