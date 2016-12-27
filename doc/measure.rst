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

No-Reference Quality Assessment
---------------------------------

Use :func:`skvideo.measure.videobliinds_features` to extract features using the Video Bliinds algorithm, useful for training your own quality-aware model.

Use :func:`skvideo.measure.viideo_features` to extract features using the Viideo Oracle algorithm, useful for training your own quality-aware model. 

Use :func:`skvideo.measure.viideo_score` to return the score of the Viideo Oracle algorithm.

Scene detection
---------------------------------

Use :func:`skvideo.measure.scenedet` to find frames that start scene boundaries. Check the documentation on selecting the specific detection algorithm.

.. toctree::
    :hidden:
