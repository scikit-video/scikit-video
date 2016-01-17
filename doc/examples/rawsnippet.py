import skvideo.io
import skvideo.utils
import skvideo.datasets

# since this skvideo does not support images yet
import skimage.io
import numpy as np

filename = skvideo.datasets.bigbuckbunny()
filename_yuv = "test.yuv"

# first produce a yuv for demonstration
vid = skvideo.io.vread(filename)
T, M, N, C = vid.shape

# produces a yuv file using -pix_fmt=yuvj444p
skvideo.io.vwrite(filename_yuv, vid)

# now to demonstrate YUV loading

vid_luma = skvideo.io.vread(filename_yuv, height=M, width=N, outputdict={"-pix_fmt": "gray"})[:, :, :, 0]
vid_luma = skvideo.utils.vshape(vid_luma)

vid_rgb = skvideo.io.vread(filename_yuv, height=M, width=N)

# now load the YUV "as is" with no conversion
vid_yuv444 = skvideo.io.vread(filename_yuv, height=M, width=N, outputdict={"-pix_fmt": "yuvj444p"})

# re-organize bytes, since FFmpeg outputs in planar mode
vid_yuv444 = vid_yuv444.reshape((M * N * T * 3))
vid_yuv444 = vid_yuv444.reshape((T, 3, M, N))
vid_yuv444 = np.transpose(vid_yuv444, (0, 2, 3, 1))


# visualize
skvideo.io.vwrite("luma.mp4", vid_yuv444[:, :, :, 0])
skvideo.io.vwrite("chroma1.mp4", vid_yuv444[:, :, :, 1])
skvideo.io.vwrite("chroma2.mp4", vid_yuv444[:, :, :, 2])

# write out the first frame of each video
skimage.io.imsave("vid_luma_frame1.png", vid_luma[0])
skimage.io.imsave("vid_rgb_frame1.png", vid_rgb[0])

skimage.io.imsave("vid_chroma1.png", vid_yuv444[0, :, :, 1])
skimage.io.imsave("vid_chroma2.png", vid_yuv444[0, :, :, 2])
