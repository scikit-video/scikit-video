import skvideo.io
import numpy as np

# create random data, sized 1280x720
image = np.random.random(size=(720, 1280))*255
print("Random image, shape (%d, %d)" % image.shape)

skvideo.io.vwrite("output.png", image)
