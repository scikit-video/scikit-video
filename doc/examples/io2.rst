.. _ioexampleimages:

Image Reading and Writing
----------------------------------------------

The trivial video is a video of 1 frame. This is how images are interpreted by scikit-video. Let's walk through the following example for interpreting images:

.. literalinclude:: imagedata.py
   :linenos:

Running this code yields this output:

.. code-block:: python

    Number of frames: 1
    Number of rows: 720
    Number of cols: 1280
    Number of channels: 3

As you can see, the 1280x720 sized image has loaded without problems, and is treated as a rgb video with 1 frame.

If you'd like to upscale this image during loading, you can run the following:

.. literalinclude:: imagedata2.py
   :linenos:

Running this code yields this output:

.. code-block:: python

    Number of frames: 1
    Number of rows: 1440
    Number of cols: 2560
    Number of channels: 3

Notice that the upscaling type is set to "bilinear" by simply writing it out in plain English. You can also upscale using other parameters that ffmpeg/avconv support.

Note that although ffmpeg/avconv supports relative scaling, scikit-video doesn't support that yet. Future support can be added by parsing the video filter "-vf" commands, so that scikit-video is aware of the buffer size expected from the ffmpeg/avconv subprocess.

Of course, images can be written just as easily as they can be read. 

.. literalinclude:: imagedata3.py
   :linenos:

Again, the output:

.. code-block:: python

    Random image, shape (720, 1280)

First, notice that the shape of the image is height x width. Scikit-Video always interprets images and video matrices as a height then a width, which is a standard matrix format. Second, notice that writing images does not require them to be in the same format as videos. Scikit-Video will interpret shapes of (1, M, N), (M, N), (M, N, C) as images where M is height, N is width, and C is the number of channels. Internally, scikit-video standardizes shapes and datatypes for accurate reading and writing through the ffmpeg/avconv subprocess.
