import numpy as np
from PIL import Image, ImageChops, ImageFilter

import skvideo.datasets
import skvideo.io

try:
    xrange
except NameError:
    xrange = range


def frame_differencing(X0, X1, threshold=10):
    Xdiff = ImageChops.difference(X0, X1)
    F = Xdiff.point(lambda p: 255 if p > threshold else 0)
    return F


size = 7
erosion = ImageFilter.MinFilter(size=size)
dilation = ImageFilter.MaxFilter(size=size)

filename = skvideo.datasets.bigbuckbunny()
videodata = skvideo.io.vread(filename)
num_frames, height, width, _ = videodata.shape

videometadata = skvideo.io.ffprobe(filename)
frame_rate = videometadata['video']['@avg_frame_rate']

writer = skvideo.io.FFmpegWriter("foreground.mp4", inputdict={
    "-r": frame_rate
})


for i in xrange(num_frames):

    # gaussian blurring, to smooth out the decompression noise and camera motion
    frame = Image.fromarray(videodata[i])
    frame_filt = frame.filter(ImageFilter.GaussianBlur(radius = 3))
    if i == 0:
        frame_background = frame_filt
        pass
    # foreground segmentation using frame differencing
    foreground_mask = frame_differencing(frame_background, frame_filt)
    frame_background = frame_filt
    # mathematical morphology: opening, to denoise foreground mask
    foreground_ = foreground_mask.filter(erosion).filter(dilation)
    # closing, to merge blobs
    foreground = foreground_.filter(dilation).filter(erosion)

    outputframe = np.zeros((height, width*2, 3))
    outputframe[:, :width] = videodata[i]
    outputframe[:, width:] = foreground
    writer.writeFrame(outputframe)

writer.close()
