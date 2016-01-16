.. _faq:

===========================
Frequently Asked Questions
===========================

Loading videos using vread is sooooo slow!
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You may not have supplied `num_frames`. The autodetection process sometimes requires two passes on an input video (depending on the type of video), which can make a huge difference for a large video corpus. By supplying `num_frames`, your code may speed up tremendously.

How do I report a bug with scikit-video?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Please give us a full report of your problem in the issue tracker over on github.

How do I contribute to make scikit-video better?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Please fork our project, make a new branch on your fork, then make changes there. Improvements are always welcome, and we'd love to see an included benchmark and test to show it working nicely. If you want more complete instructions, check out the contributing doc: 

https://github.com/scikit-video/scikit-video/blob/master/CONTRIBUTING.md.


.. toctree::
    :hidden:
