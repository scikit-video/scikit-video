import matplotlib.pyplot as plt
import numpy as np
import scipy.misc

import skvideo.datasets

try:
    xrange
except NameError:
    xrange = range

def getPlots(motionData):
    motionMagnitude = np.sqrt(np.sum(motionData**2, axis=2))

    fig = plt.figure()
    plt.quiver(motionData[::-1, :, 0], motionData[::-1, :, 1])
    fig.axes[0].get_xaxis().set_visible(False)
    fig.axes[0].get_yaxis().set_visible(False)
    plt.tight_layout()
    fig.canvas.draw()
 
    # Get the RGBA buffer from the figure
    w,h = fig.canvas.get_width_height()
    buf = np.fromstring(fig.canvas.tostring_argb(), dtype=np.uint8)
    buf.shape = (h, w, 4)
    quiver = buf[:, :, 1:]
    plt.close()

    fig = plt.figure()
    plt.imshow(motionMagnitude, cmap="Greys_r")
    fig.axes[0].get_xaxis().set_visible(False)
    fig.axes[0].get_yaxis().set_visible(False)
    plt.tight_layout()
    fig.canvas.draw()

    w,h = fig.canvas.get_width_height()
    buf = np.fromstring(fig.canvas.tostring_argb(), dtype=np.uint8)
    buf.shape = (h, w, 4)
    magnitude = buf[:, :, 1:]
    plt.close()

    # histogram it
    fig = plt.figure()
    hist, bins = np.histogram(motionMagnitude, bins=10, range=(-0.5, 9.5))
    center = (bins[1:] + bins[:-1])/2.0
    plt.scatter(center, hist)
    plt.xlabel("Motion magnitude")
    plt.ylabel("Count")
    plt.ylim([0, 14000])
    plt.grid()
    plt.tight_layout()
    fig.canvas.draw()

    w,h = fig.canvas.get_width_height()
    buf = np.fromstring(fig.canvas.tostring_argb(), dtype=np.uint8)
    buf.shape = (h, w, 4)
    histogram = buf[:, :, 1:]
    plt.close()

    return quiver, magnitude, histogram


filename = skvideo.datasets.bigbuckbunny()

videodata = skvideo.io.vread(filename)

videometadata = skvideo.io.ffprobe(filename)
frame_rate = videometadata['video']['@avg_frame_rate']

T, M, N, C = videodata.shape

motionData = skvideo.motion.blockMotion(videodata)

writer = skvideo.io.FFmpegWriter("motion.mp4", inputdict={
    "-r": frame_rate
})

for i in xrange(T-1):
    a, b, c = getPlots(motionData[i])
    frame = scipy.misc.imresize(videodata[i+1], (a.shape[0], a.shape[1], 3))

    outputframe = np.zeros((frame.shape[0]*2, frame.shape[1]*2, 3), dtype=np.uint8)

    outputframe[:frame.shape[0], :frame.shape[1]] = frame
    outputframe[frame.shape[0]:, :frame.shape[1]] = a
    outputframe[:frame.shape[0], frame.shape[1]:] = b
    outputframe[frame.shape[0]:, frame.shape[1]:] = c

    writer.writeFrame(outputframe)

writer.close()
