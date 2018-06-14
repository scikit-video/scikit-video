import skvideo.measure
import numpy as np
import numpy as np

import skvideo.measure

outputfile = "test.mp4"
outputdata = np.random.random(size=(30, 480, 640, 3)) * 255
outputdata = outputdata.astype(np.uint8)

# start the FFmpeg writing subprocess with following parameters
writer = skvideo.io.FFmpegWriter(outputfile, outputdict={
  '-vcodec': 'libx264', '-b': '300000000'
})

for i in range(30):
  writer.writeFrame(outputdata[i])
writer.close()

inputdata = skvideo.io.vread(outputfile)

# test each frame's SSIM score
mSSIM = 0
for i in range(30):
  mSSIM += skvideo.measure.ssim(np.mean(inputdata[i], axis=2), np.mean(outputdata[i], axis=2))

mSSIM /= 30.0
print(mSSIM)
