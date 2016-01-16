.. _examples:

=============
Examples
=============

.. currentmodule:: skvideo

Video loading
----------------------------------------------


A typical use case for video research includes loading only the luma channel of a video. Often, researchers will convert a source from its arbitrary format to a YUV file, then only load the Y channel. To do this directly, bypassing the YUV step, one could just run


.. literalinclude:: examples/lumasnippet.py
   :linenos:

Also, for testing a piece of code quickly, the whole video isn't usually required. So only load a couple frames

.. literalinclude:: examples/lumasnippet_trunc.py
   :linenos:

If you would like to read a raw format like yuv, you must specify the width, height, and pixel type. By default, scikit-video assumes that your pix_fmt is yuvj444p. This assumption is to provide consistent saving and loading of video content while maintaining signal fidelity.

.. literalinclude:: examples/rawsnippet.py
   :linenos:



.. toctree::
    :hidden:
