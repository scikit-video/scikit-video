.. _measure:

===========================
Measurement functions
===========================

.. currentmodule:: skvideo.measure

:mod:`skvideo.measure` provides quality assessment tools and other measurement operations.

Full-Reference Quality Assessment
---------------------------------

Use :func:`skvideo.measure.ssim` to measure the perceptually quality difference between two videos, considering only individual frames.

Use :func:`skvideo.measure.mse` or :func:`skvideo.measure.psnr` to measure simple point-wise similarity between two videos.


.. toctree::
    :hidden:
