.. _didacticexample:

Miscellaneous Video Demonstrations
----------------------------------------------

----------------------------------------------
Visualizing growth of sparse filters
----------------------------------------------

Videos can be made of sparse filters evolving over time. Below is a code snippet implementing the K-SVD algorithm. The purpose of the snippet is to visualize the state of sparse basis functions at they are iteratively refined.

.. literalinclude:: sparsevid.py
   :linenos:

The video output for 200 iterations of the K-SVD algorithm:

.. youtube:: hJwX7z5JZb4
    :width: 50%

----------------------------------------------
Selectively manipulating frames
----------------------------------------------

If you want to create a corrupted version of a video, you can use the FFmpegReader/FFmpegWriter in combination. Just make sure that you pass the video metadata along, or you may get incorrect output video (such as incorrect framerate). Provided below is an example corrupting one frame from the source video with white noise:

.. literalinclude:: IOcorrupt.py
   :linenos:

Video output of the corrupted BigBuckBunny sequence:

.. youtube:: q6s5mH39K08
    :width: 50%
