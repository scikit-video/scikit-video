.. _measure:

===========================
Measurement Tools
===========================

.. currentmodule:: skvideo.measure

:mod:`skvideo.measure` provides quality assessment tools, scene detection, and other measurement operations.

Reduced-Reference Quality Assessment
------------------------------------

Use :func:`skvideo.measure.strred` to measure the perceptually quality difference between two videos, providing a slightly reduced reference score along with a critically reduced reference score (1 number comparison between videos).


Full-Reference Quality Assessment
---------------------------------

Use :func:`skvideo.measure.ssim` to measure the perceptually quality difference between two videos, considering only individual frames.

Use :func:`skvideo.measure.msssim` to measure the perceptually quality difference between two videos, considering only individual frames. Differs from ssim in that this function considers multiple scales.

Use :func:`skvideo.measure.mse`, :func:`skvideo.measure.mad`, or :func:`skvideo.measure.psnr` to measure simple point-wise similarity between two videos.

No-Reference Quality Assessment
---------------------------------

Use :func:`skvideo.measure.brisque_features` to extract frame-by-frame features using the BRISQUE image quality algorithm, useful for frame-level quality analysis and training your own frame-based quality-aware model.

Use :func:`skvideo.measure.videobliinds_features` to extract features using the Video Bliinds algorithm, useful for training your own quality-aware model.

Use :func:`skvideo.measure.viideo_features` to extract features using the Viideo Oracle algorithm, useful for training your own quality-aware model. 

Use :func:`skvideo.measure.viideo_score` to return the score of the Viideo Oracle algorithm.

Scene detection
---------------------------------

Use :func:`skvideo.measure.scenedet` to find frames that start scene boundaries. Check the documentation on selecting the specific detection algorithm.

.. toctree::
    :hidden:
