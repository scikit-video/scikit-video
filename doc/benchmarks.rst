.. _benchmarks:

===========================
Benchmarking scikit-video
===========================

To be useful in any project, we would like to approach real-time performance. Some algorithms implemented may not be able to achieve this (exhaustive search algorithms, for example), but we still set our goals high!

All tests computed for scikit-video v1.1.1

Reading speed
-------------

Minimum time from 10 trials, loading the 3 test videos in :mod:`skvideo.datasets`:

.. cssclass:: table-striped

============================== ================
Method 		                   Time
============================== ================
skvideo.io.vread (FFmpeg)      0.718217 seconds
skvideo.io.vread (LibAV)       0.815005 seconds
skvideo.io.vreader (FFmpeg)    0.671952 seconds
skvideo.io.vreader (LibAV)     0.774765 seconds
============================== ================

The fastest backend appears to be FFmpeg for both :func:`skvideo.io.vread` and :func:`skvideo.io.vreader`. Naturally, since :func:`skvideo.io.vreader` uses a yield-based generator to supply frames, it is faster to use than :func:`skvideo.io.vread` which allocates space then copies data frame-by-frame.

Block Motion estimation
-----------------------

Using the default settings on the `carphone_pristine.mp4` sequence, shape (120, 144, 176, 3)

Performance on block motion algorithms using skvideo.motion.blockMotion:

.. cssclass:: table-striped

==================================  =================
Method 		   		    Time
==================================  =================
exhaustive                          43.946715 seconds
3-step search                       17.558664 seconds
"new" 3-step search                 32.340459 seconds
simple and efficient 3-step search  13.861776 seconds
4-step search                       36.315580 seconds
adaptive rood pattern search        21.413136 seconds
diamond search                      25.679036 seconds
==================================  =================

------------------------------------------------------------

We can see that 3-step search is currently the fastest algorithm at 17.5 seconds. That comes out to 0.146 seconds per frame, for 144x176 sized frames. Clearly this is not realtime, which makes sense given that the core computations are in non-optimized python.


.. toctree::
    :hidden:
