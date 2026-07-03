=============
I/O
=============

.. _io_ref:

:mod:`skvideo.io`: Video input and output utilities
===================================================

.. automodule:: skvideo.io
   :no-members:
   :no-inherited-members:

Classes
-------
.. currentmodule:: skvideo.io

.. autosummary::
   :toctree: generated/
   :template: class.rst

   FFmpegWriter
   FFmpegReader
   LibAVWriter
   LibAVReader

.. deprecated:: 1.3.0
   ``LibAVWriter`` and ``LibAVReader`` (the libav/avconv backend) are
   deprecated and will be removed in a future release. Use the FFmpeg
   backend.

Functions
---------
.. autosummary::
   :toctree: generated/
   :template: function.rst

   vread
   vreader
   vwrite
   mprobe
   ffprobe
   avprobe

.. deprecated:: 1.3.0
   ``mprobe`` (mediainfo) and ``avprobe`` (libav) are deprecated and
   will be removed in a future release. Use :func:`skvideo.io.ffprobe`.
