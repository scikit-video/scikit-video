.. _ioexamplevideo:

Video Reading and Writing
----------------------------------------------

A typical use case for video research includes loading only the luma channel of a video. Often, researchers will convert a source from its arbitrary format to a YUV file, then only load the Y channel. Also, to test an algorithm, only the first N frames are needed. The next example shows how this can be done without generating YUV files


.. literalinclude:: lumasnippet.py
   :linenos:

Running this produces the following

.. code-block:: python

    Loading only luminance channel
    (132, 720, 1280)
    Enforcing video shape
    (132, 720, 1280, 1)

    Loading only first 5 luminance channel frames
    (5, 720, 1280)
    Enforcing video shape
    (5, 720, 1280, 1)


Given an input raw video format like yuv, one must specify the width, height, and format. By default, scikit-video assumes pix_fmt is yuvj444p, to provide consistent saving and loading of video content while also maintaining signal fidelity. Note that the current state of skvideo does not support direct loading of yuv420p (i.e. loading into rgb format still works, but you cannot access the yuv420 chroma channels directly yet. This is a data organization issue.)

.. literalinclude:: rawsnippet.py
   :linenos:

Luminance video (luma.mp4)

.. raw:: html 

   <center><video controls width=75% src="../_static/luma.mp4"></video></center> 

Chroma channel 1 video (chroma1.mp4)

.. raw:: html 

   <center><video controls width=75% src="../_static/chroma1.mp4"></video></center> 

Chroma channel 2 video (chroma2.mp4)

.. raw:: html 

   <center><video controls width=75% src="../_static/chroma2.mp4"></video></center> 

Luminance frame (vid_luma_frame1.png)

.. image:: images/vid_luma_frame1.png

RGB frame (vid_rgb_frame1.png)

.. image:: images/vid_rgb_frame1.png

Chroma channel 1 frame (vid_chroma1.png)

.. image:: images/vid_chroma1.png

Chroma channel 2 frame (vid_chroma2.png)

.. image:: images/vid_chroma2.png

Video Writing with Quality
----------------------------------------------

Specifying FFmpeg parameters using the outputdict parameter allows for higher video quality. As you change the bitrate through the "-b" parameter, the video output approaches the fidelity of the original signal.

.. literalinclude:: outputdictexample.py
   :linenos:

