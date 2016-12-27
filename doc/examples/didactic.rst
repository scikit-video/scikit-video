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

.. raw:: html 

   <center><video controls width=75% src="../_static/sparsity.mp4"></video></center> 

----------------------------------------------
Selectively manipulating frames
----------------------------------------------

If you want to create a corrupted version of a video, you can use the FFmpegReader/FFmpegWriter in combination. Just make sure that you pass the video metadata along, or you may get incorrect output video (such as incorrect framerate). Provided below is an example corrupting one frame from the source video with white noise:

.. literalinclude:: IOcorrupt.py
   :linenos:

Video output of the corrupted BigBuckBunny sequence:

.. raw:: html 

   <center><video controls width=75% src="../_static/corrupted_video.mp4"></video></center> 
