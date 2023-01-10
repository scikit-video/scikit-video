import numpy as np

import skvideo.datasets

filename = skvideo.datasets.bigbuckbunny()

vid_in = skvideo.io.FFmpegReader(filename)
data = skvideo.io.ffprobe(filename)['video']
rate = data['@r_frame_rate']
T = int(data['@nb_frames'])

vid_out = skvideo.io.FFmpegWriter("corrupted_video.mp4", inputdict={
      '-r': rate,
    },
    outputdict={
      '-vcodec': 'libx264',
      '-pix_fmt': 'yuv420p',
      '-r': rate,
})
for idx, frame in enumerate(vid_in.nextFrame()):
  print("Writing frame %d/%d" % (idx, T))
  if (idx >= (T/2)) & (idx <= (T/2 + 10)):
    frame = np.random.normal(128, 128, size=frame.shape).astype(np.uint8)
  vid_out.writeFrame(frame)
vid_out.close()
