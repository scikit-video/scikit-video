.. _examples:

=============
Examples
=============

.. currentmodule:: skvideo

Video loading
----------------------------------------------


A typical use case for video research includes loading only the luma channel of a video. Often, researchers will convert a source from its arbitrary format to a YUV file, then only load the Y channel. Also, to test an algorithm, only the first N frames are needed. The next example shows how this can be done without generating YUV files


.. literalinclude:: examples/lumasnippet.py
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

.. literalinclude:: examples/rawsnippet.py
   :linenos:

Luminance video (luma.mp4)

.. youtube:: 1RrVxVE8igs
    :width: 50%

Chroma channel 1 video (chroma1.mp4)

.. youtube:: AZ0v_wDeDx0
    :width: 50%

Chroma channel 2 video (chroma2.mp4)

.. youtube:: R7-1COKxLUs
    :width: 50%


Luminance frame (vid_luma_frame1.png)

.. image:: images/vid_luma_frame1.png

RGB frame (vid_rgb_frame1.png)

.. image:: images/vid_rgb_frame1.png

Chroma channel 1 frame (vid_chroma1.png)

.. image:: images/vid_chroma1.png

Chroma channel 2 frame (vid_chroma2.png)

.. image:: images/vid_chroma2.png

.. toctree::
    :hidden:
