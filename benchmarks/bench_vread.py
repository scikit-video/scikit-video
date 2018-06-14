"""
=======================
Video Reader benchmark
=======================

Benchmark using the video loading routines included in skvideo.

Output:

Fastest performance of loading 3 test videos:
------------------------------------------------------------
skvideo.io.vread (FFmpeg)                    0.718217 seconds
skvideo.io.vread (LibAV)                     0.815005 seconds
skvideo.io.vreader (FFmpeg)                  0.671952 seconds
skvideo.io.vreader (LibAV)                   0.774765 seconds

"""
# Author: Todd Goodall <tgoodall@utexas.edu>
# License: BSD clause

from time import time

import numpy as np

import skvideo.datasets

try:
    xrange
except NameError:
    xrange = range

if __name__ == "__main__":

    #add in all videos that come with skvideo
    videos = []
    videos.append(skvideo.datasets.bigbuckbunny())
    videos.append(skvideo.datasets.fullreferencepair()[0])
    videos.append(skvideo.datasets.fullreferencepair()[1])

    vread_times_ffmpeg = []
    vread_generator_times_ffmpeg = []
    vread_times_libav = []
    vread_generator_times_libav = []

    # run 10 times, then take min time
    for i in xrange(10):
        # first test time to load each video completely into memory
        time_start = time()
        for vnames in videos:
            skvideo.io.vread(vnames, backend='ffmpeg')
        time_end = time()

        vread_times_ffmpeg.append(time_end - time_start)

        # next test the speed at which the frame generator works
        time_start = time()
        for vnames in videos:
            vobj = skvideo.io.vreader(vnames, backend='ffmpeg')
            for frame in vobj:
                pass
        time_end = time()

        vread_generator_times_ffmpeg.append(time_end - time_start)

    # run 10 times, then take min time
    for i in xrange(10):
        # first test time to load each video completely into memory
        time_start = time()
        for vnames in videos:
            skvideo.io.vread(vnames, backend='libav')
        time_end = time()

        vread_times_libav.append(time_end - time_start)

        # next test the speed at which the frame generator works
        time_start = time()
        for vnames in videos:
            vobj = skvideo.io.vreader(vnames, backend='libav')
            for frame in vobj:
                pass
        time_end = time()

        vread_generator_times_libav.append(time_end - time_start)

    print("")
    print("Fastest performance of loading %d test videos:" % (len(videos),))
    print("-" * 60)
    print("%s %f seconds" % ("skvideo.io.vread (FFmpeg)".ljust(35), np.min(vread_times_ffmpeg)))
    print("%s %f seconds" % ("skvideo.io.vread (LibAV)".ljust(35), np.min(vread_times_libav)))
    print("%s %f seconds" % ("skvideo.io.vreader (FFmpeg)".ljust(35), np.min(vread_generator_times_ffmpeg)))
    print("%s %f seconds" % ("skvideo.io.vreader (LibAV)".ljust(35), np.min(vread_generator_times_libav)))
    print("")
