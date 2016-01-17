import skvideo.io
import skvideo.datasets
import skvideo.utils

filename = skvideo.datasets.bigbuckbunny()

print("Loading only luminance channel")
vid = skvideo.io.vread(filename, outputdict={"-pix_fmt": "gray"})[:, :, :, 0]
print(vid.shape)
print("Enforcing video shape")
vid = skvideo.utils.vshape(vid)
print(vid.shape)
print("")

print("Loading only first 5 luminance channel frames")
vid = skvideo.io.vread(filename, num_frames=5, outputdict={"-pix_fmt": "gray"})[:, :, :, 0]
print(vid.shape)
print("Enforcing video shape")
vid = skvideo.utils.vshape(vid)
print(vid.shape)
print("")
