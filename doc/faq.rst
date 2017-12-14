.. _faq:

===========================
Frequently Asked Questions
===========================

What is scikit-video?
~~~~~~~~~~~~~~~~~~~~~

Scikit-video allows users easy access to video files through the use of the FFmpeg/LibAV backend. This toolkit 
privides both high-level and low-level abstractions for reading and writing video files.

Scikit-video comes bundled with state-of-the-art quality measurement tools allowing users to begin curating
their own video collections. Using the latest quality-aware tools allows researchers to easily compare their algorithms
against a consistent and peer-reviewed set of tools.

Finally, scikit-video provides helpful utilities, like scene-boundary detectors and block-motion estimators commonly
used in video processing algorithms.

How do I tell scikit-video to use different FFmpeg/LibAV installs?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can use the function :mod:`skvideo.setFFmpegPath` or :mod:`skvideo.setLibAVPath` in the core :mod:`skvideo` API.

I installed scikit-video, but the API I installed does not match the website! How do I fix this?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You may be using an old version of scikit-video. Uninstall it using

.. code-block:: python

    $ sudo pip uninstall sk-video
    $ sudo pip install scikit-video

You can verify the module path by importing skvideo and printing the path to the init file

.. code-block:: python

    import skvideo
    print(skvideo.__file__)

This should produce output like

.. code-block:: python

  /usr/lib/python*/site-packages/scikit_video-*.*.*-py*.egg/skvideo/__init__.pyc



Loading videos using vread is sooooo slow!
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You may not have supplied `num_frames`. The autodetection process sometimes requires two passes on an input video (depending on the type of video), which can make a huge difference for a large video corpus. By supplying `num_frames`, your code may speed up tremendously.

How do I report a bug with scikit-video?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Please give us a full report of your problem in the issue tracker over on `github <https://github.com/scikit-video/scikit-video/issues/new>`_.

How do I contribute to make scikit-video better?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Please fork our project, make a new branch on your fork, then make changes there. Improvements are always welcome, and we'd love to see an included benchmark and test to show it working nicely. If you want more complete instructions, check out the contributing doc: 

https://github.com/scikit-video/scikit-video/blob/master/CONTRIBUTING.rst.

.. toctree::
   :hidden:
