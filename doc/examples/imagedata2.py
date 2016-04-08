import skvideo.io

# upscale frame from the bigbuckbunny sequence by a factor of 2
vid = skvideo.io.vread("vid_luma_frame1.png",
                       outputdict={
                           "-sws_flags": "bilinear",
                           "-s": "2560x1440"
                       }
)
T, M, N, C = vid.shape

print("Number of frames: %d" % (T,))
print("Number of rows: %d" % (M,))
print("Number of cols: %d" % (N,))
print("Number of channels: %d" % (C,))
