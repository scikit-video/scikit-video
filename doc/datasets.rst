.. _datasets:

===========================
Test Datasets
===========================

.. currentmodule:: skvideo.datasets

:mod:`skvideo.datasets` provides several test videos for benchmarking and testing internal code.


Big Buck Bunny sequence
-----------------------

Use :func:`skvideo.datasets.bigbuckbunny` for the absolute path to the bigbuckbunny sequence, used for general testing.

.. raw:: html 

   <center><video controls width=75% src="_static/bigbuckbunny.mp4"></video></center> 

Bikes sequence
-----------------------

Use :func:`skvideo.datasets.bikes` for the absolute path to the bikes sequence, used for scene detection testing.

.. raw:: html 

   <center><video controls width=75% src="_static/bikes.mp4"></video></center> 


Carphone pristine and distorted sequences
-----------------------------------------

Use :func:`skvideo.datasets.fullreferencepair` for both pristine and distorted versions of the carphone sequence, used for full-reference quality algorithm testing.

.. raw:: html 

   <center><video controls width=38% src="_static/carphone_pristine.mp4"></video> <video controls width=38% src="_static/carphone_distorted.mp4"></video></center> 

.. toctree::
    :hidden:
