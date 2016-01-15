.. _examples:

=============
Examples
=============

.. currentmodule:: skvideo

Loading videos efficiently
----------------------------------------------


A typical use case for video research includes loading only the luma channel of a video. Often, researchers will convert a source from its arbitrary format to a YUV file, then only load the Y channel. To do this directly, bypassing the YUV step, one could just run


.. literalinclude:: examples/lumasnippet.py
   :linenos:

Also, for testing a piece of code quickly, the whole video isn't usually required. So only load a couple frames

.. literalinclude:: examples/lumasnippet_trunc.py
   :linenos:


.. toctree::
    :hidden:
