.. _benchmarks:

===========================
Benchmarking scikit-video
===========================

To be useful in any project, we would like to approach real-time performance. Some algorithms implemented may not be able to achieve this (exhaustive search algorithms, for example), but we still set our goals high!

All tests computed for scikit-video v1.0.0

Reading files
-----------------------

The average performance over ten iterations of :func:`skvideo.io.vread` and :func:`skvideo.io.vreader`.

Mean performance on loading 3 test videos:
------------------------------------------------------------
skvideo.io.vread                    1.346741 seconds
skvideo.io.vreader                  1.311501 seconds

The generator is slightly faster on my laptop, but could be faster depending on the disk and memory speeds.

Block Motion estimation
-----------------------

Using the default settings on the `carphone_pristine.mp4` sequence, shape (120, 144, 176, 3)

Performance on block motion algorithms using skvideo.motion.blockMotion:
------------------------------------------------------------
exhaustive                          43.946715 seconds
3-step search                       17.558664 seconds
"new" 3-step search                 32.340459 seconds
simple and efficient 3-step search  13.861776 seconds
4-step search                       36.315580 seconds
adaptive rood pattern search        21.413136 seconds
diamond search                      25.679036 seconds

We can see that 3-step search is currently the fastest algorithm at 17.5 seconds. That comes out to 0.146 seconds per frame, for 144x176 sized frames. Clearly this is not realtime, which makes sense given that the core computations are in non-optimized python.


.. toctree::
    :hidden:
