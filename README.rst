.. -*- mode: rst -*-

|skvideologo|_

|BSD3|_ |Travis|_ |Coveralls|_ |CircleCI|_ |Python27|_ |Python35|_ |PyPi|_ 

.. |BSD3| image:: https://img.shields.io/badge/license-BSD--3--Clause-blue.svg
.. _BSD3: https://opensource.org/licenses/BSD-3-Clause

.. |Travis| image:: https://api.travis-ci.org/scikit-video/scikit-video.png?branch=master
.. _Travis: https://travis-ci.org/scikit-video/scikit-video

.. |Coveralls| image:: https://coveralls.io/repos/github/scikit-video/scikit-video/badge.svg?branch=master
.. _Coveralls: https://coveralls.io/github/scikit-video/scikit-video?branch=master

.. |CircleCI| image:: https://circleci.com/gh/scikit-video/scikit-video/tree/master.svg?style=shield&circle-token=:circle-token
.. _CircleCI: https://circleci.com/gh/scikit-video/scikit-video

.. |Python27| image:: https://img.shields.io/badge/python-2.7-blue.svg
.. _Python27: https://badge.fury.io/py/sk-video

.. |Python35| image:: https://img.shields.io/badge/python-3.5-blue.svg
.. _Python35: https://badge.fury.io/py/sk-video

.. |PyPi| image:: https://badge.fury.io/py/sk-video.svg
.. _PyPi: https://badge.fury.io/py/sk-video

.. |skvideologo| image:: doc/images/scikit-video.png
.. _skvideologo: http://www.scikit-video.org


Video Processing SciKit
-----------------------

Borrowing coding styles and conventions from scikit-image and scikit-learn,
scikit-video is a Python module for video processing built on top of 
scipy, numpy, and ffmpeg/libav.

This project is distributed under the 3-clause BSD.

Visit the documentation at http://www.scikit-video.org


Dependencies and Installation
-----------------------------

Here are the requirements needed to use scikit-video.

- Either ffmpeg (version >= 2.1) or libav (either version 10 or 11)
- python (2.6, 2.7, 3.3, and 3.5)
- numpy (version >= 1.9.2)
- scipy (version >= 0.16.0)
- PIL/Pillow (version >= 3.1)
- scikit-learn (version >= 0.18)
- mediainfo (optional)

Installation::

$ sudo pip install sk-video

Installing from github

1. Make sure minimum dependencies (above) are installed. In addition, install setuptools (python-setuptools or python2-setuptools).

2. Clone the scikit-video repository, enter the project directory, then run::

   $ python setup.py build

3. In that same project directory, run the command::

   $ sudo python setup.py install

where `python` may refer to either python2 or python3.

Known conflicts
---------------

If you installed scikit-video prior to version 1.1.2, you may have an import conflict. Run the following command to fix it::

    $ sudo pip uninstall scikit-video

To check that the conflict no longer exists, import skvideo and print the file path::

    import skvideo
    print(skvideo.__file__)

if setup correctly, you should see `sk_video` in the path::

/usr/lib/python2.7/site-packages/sk_video-*.*.*-py2.7.egg/skvideo/__init__.pyc


TODO/Roadmap
------------
- Windows support
- Spatial-Temporal filtering helper functions
- Speedup routines (using cython and/or opencl)
- More ffmpeg/avconv interfacing
- Wrapping ffmpeg/avconv inside a subprocess to reduce memory overhead 
- Add additional algorithms and maintain more comprehensive benchmarks


For Contributors
----------------

Quick tutorial on how to go about setting up your environment to contribute to scikit-video: 

https://github.com/beyondmetis/scikit-video/blob/master/CONTRIBUTING.md


Testing
-------

After installation, you can launch the test suite from outside the source directory (you will need to have the nose package installed). To ensure that both python2 and python3 versions pass::

    $ nosetests2 -v skvideo
    $ nosetests3 -v skvideo

Copyright 2015-2016, scikit-video developers (BSD license).
