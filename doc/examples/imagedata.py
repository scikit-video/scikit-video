import skvideo.io

# a frame from the bigbuckbunny sequence
vid = skvideo.io.vread("vid_luma_frame1.png")
T, M, N, C = vid.shape

print("Number of frames: %d" % (T,))
print("Number of rows: %d" % (M,))
print("Number of cols: %d" % (N,))
print("Number of channels: %d" % (C,))
