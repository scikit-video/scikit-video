.. _faq:

===========================
Frequently Asked Questions
===========================

How do I tell scikit-video to use different FFmpeg installs?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can use the function :mod:`skvideo.setFFmpegPath`.

I installed scikit-video, but the API I installed does not match the website! How do I fix this?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You may be using an old version of scikit-video. Uninstall it using

.. code-block:: python

    $ sudo pip uninstall scikit-video
    $ sudo pip install sk-video

You can verify the module path by importing skvideo and printing the path to the init file

.. code-block:: python

    import skvideo
    print skvideo.__file__

This should produce output like

.. code-block:: python

    /usr/lib/python2.7/site-packages/sk_video-1.1.1-py2.7.egg/skvideo/__init__.pyc



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
