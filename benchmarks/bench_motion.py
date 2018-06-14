"""
=======================
Block Motion Estimation benchmark
=======================

Benchmark using the block motion estimation routines included in skvideo.

Output for sequence of size (120, 144, 176, 3)

Performance on block motion algorithms using skvideo.motion.blockMotion:
------------------------------------------------------------
exhaustive                          43.946715 seconds
3-step search                       17.558664 seconds
"new" 3-step search                 32.340459 seconds
Simple and Efficient 3-step search  13.861776 seconds
4-step search                       36.315580 seconds
Adaptive Rood Pattern search        21.413136 seconds
Diamond search                      25.679036 seconds

"""
# Author: Todd Goodall <tgoodall@utexas.edu>
# License: BSD clause

from time import time

import skvideo.motion

if __name__ == "__main__":
    # TODO: as code gets faster, make benchmark more 
    # rigorous

    # for time, use small pristine video
    vidname = skvideo.datasets.fullreferencepair()[0]
    vdata = skvideo.io.vread(vidname)

    # first 2 frames

    estimator_titles = ["exhaustive", 
		"3-step search", 
		"\"new\" 3-step search", 
		"Simple and Efficient 3-step search",
		"4-step search",
		"Adaptive Rood Pattern search",
		"Diamond search",
    ]
    estimators = ["ES", "3SS", "N3SS", "SE3SS", "4SS", "ARPS", "DS"]
    times = []

    for es in estimators:
	print(es)
        time_start = time()
	skvideo.motion.blockMotion(vdata, method=es)
        time_end = time()
	times.append(time_end - time_start)

    print("")
    print(vdata.shape)
    print("Performance on block motion algorithms using skvideo.motion.blockMotion:")
    print("-" * 60)
    for (title, time) in zip(estimator_titles, times):
	    print("%s %f seconds" % (title.ljust(35), time))
    print("")
