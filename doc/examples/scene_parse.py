import matplotlib.pyplot as plt
import numpy as np

import skvideo.measure

try:
    xrange
except NameError:
    xrange = range

def getPlot(edgelist1, edgelist2, t, w, h, T):
    myDPI = 100
    fig = plt.figure(figsize=(w/myDPI, h/myDPI), dpi=myDPI)
    plt.subplot(211)
    plt.title("histogram algorithm")
    plt.plot(edgelist1)
    plt.plot([t, t], [0, 1])
    plt.xlim([0, T])
    plt.ylim([0, 1])

    plt.subplot(212)
    plt.title("edges algorithm")
    plt.plot(edgelist2)
    plt.plot([t, t], [0, 1])
    plt.xlim([0, T])
    plt.ylim([0, 1])
    
    plt.tight_layout()
    fig.canvas.draw()
 
    # Get the RGBA buffer from the figure
    w,h = fig.canvas.get_width_height()
    buf = np.fromstring(fig.canvas.tostring_argb(), dtype=np.uint8)
    buf.shape = (h, w, 4)
    plot = buf[:, :, 1:]
    plt.close()

    return plot

filename = skvideo.datasets.bikes()

videodata = skvideo.io.vread(filename)
videometadata = skvideo.io.ffprobe(filename)
frame_rate = videometadata['video']['@avg_frame_rate']
num_frames = int(videometadata['video']['@nb_frames'])
width = int(videometadata['video']['@width'])
height = int(videometadata['video']['@height'])

# using the "edge" algorithm
scene_edge_idx = skvideo.measure.scenedet(videodata, method='edges')
scene_edge = np.zeros((num_frames,))
scene_edge[scene_edge_idx] = 1

# using the "luminance" algorithm
scene_lum_idx = skvideo.measure.scenedet(videodata, method='histogram', parameter1=1.0)
scene_lum = np.zeros((num_frames,))
scene_lum[scene_lum_idx] = 1

# make a video that tracks the scene cuts as the video plays
writer = skvideo.io.FFmpegWriter("scene_cuts.mp4", inputdict={
    "-r": frame_rate,
})

for i in xrange(num_frames):
    outputframe = np.zeros((height, width*2, 3))

    chart = getPlot(scene_lum, scene_edge, i, width, height, num_frames)

    outputframe[:, :width] = videodata[i]
    outputframe[:, width:] = chart
    writer.writeFrame(outputframe)

writer.close()
