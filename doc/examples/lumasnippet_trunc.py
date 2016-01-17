import skvideo.io

vid = skvideo.io.vread("testvideo.mp4", outputdict={"-pix_fmt": "gray"}, num_frames=3)
