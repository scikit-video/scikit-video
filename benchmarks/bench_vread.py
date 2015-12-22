"""
=======================
Video Reader benchmark
=======================

Benchmark using the video loading routines included in skvideo.

Output:

Mean performance on loading 3 test videos:
------------------------------------------------------------
skvideo.io.vread                    1.346741 seconds
skvideo.io.vreader                  1.311501 seconds

"""
# Author: Todd Goodall <tgoodall@utexas.edu>
# License: BSD clause

import os
from time import time
import numpy as np
import skvideo.io
import skvideo.datasets


if __name__ == "__main__":

    #add in all videos that come with skvideo
    videos = []
    videos.append(skvideo.datasets.bigbuckbunny())
    videos.append(skvideo.datasets.fullreferencepair()[0])
    videos.append(skvideo.datasets.fullreferencepair()[1])

    # run once to warm the HD cache
    for vnames in videos:
        skvideo.io.vread(vnames)

    vread_times = []
    vread_generator_times = []

    # run 10 times to get an average time
    for i in xrange(10):
        # first test time to load each video completely into memory
        time_start = time()
        for vnames in videos:
            skvideo.io.vread(vnames)
        time_end = time()

        vread_times.append(time_end - time_start)

        # next test the speed at which the frame generator works
        time_start = time()
        for vnames in videos:
            vobj = skvideo.io.vreader(vnames) 
            for frame in vobj:
                pass
        time_end = time()

        vread_generator_times.append(time_end - time_start)
        

    print("")
    print("Mean performance on loading %d test videos:" % (len(videos),))
    print("-" * 60)
    print("%s %f seconds" % ("skvideo.io.vread".ljust(35), np.mean(vread_times)))
    print("%s %f seconds" % ("skvideo.io.vreader".ljust(35), np.mean(vread_generator_times)))
    print("")
