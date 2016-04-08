.. _measure:

===========================
Measurement functions
===========================

.. currentmodule:: skvideo.measure

:mod:`skvideo.measure` provides quality assessment tools, scene detection, and other measurement operations.

Full-Reference Quality Assessment
---------------------------------

Use :func:`skvideo.measure.ssim` to measure the perceptually quality difference between two videos, considering only individual frames.

Use :func:`skvideo.measure.mse` or :func:`skvideo.measure.psnr` to measure simple point-wise similarity between two videos.

Scene detection
---------------------------------

Use :func:`skvideo.measure.scenedet` to find frames that start scene boundaries. At this moment, two very distinct scene detection techniques are implemented. The first, "luminance", thresholds based on histogram luminance values to find scene tranisitions. The second, "edge", uses canny edge detection to measure how edges evolve between motion-compensated frames.

.. toctree::
    :hidden:
