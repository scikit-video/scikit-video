
![scikit-video logo](doc/images/scikit-video.png)



scikit-video v1.0.1
===================

[![The BSD-3 License](https://img.shields.io/badge/license-BSD--3--Clause-blue.svg)](https://spdx.org/licenses/BSD-3-Clause#licenseText)
[![Travis](https://api.travis-ci.org/scikit-video/scikit-video.png?branch=master)](https://travis-ci.org/scikit-video/scikit-video)


##Video Processing SciKit

Borrowing coding styles and conventions from scikit-image and scikit-learn,
scikit-video is a Python module for video processing built on top of 
scipy, numpy, and ffmpeg/libav.

This project is distributed under the 3-clause BSD.

Visit the documentation at http://www.scikit-video.org

##Dependencies:

Here are the requirements needed to use scikit-video.

- Either ffmpeg (version >= 2.1) or libav (version >= 11.4)
- python (2.6, 2.7, 3.3, and 3.5)
- numpy (version >= 1.9.2)
- scipy (version >= 0.16.0)
- mediainfo (optional)

##Installation:

Clone the scikit-video repository, run

`python2 setup.py build`

then 

`sudo python2 setup.py install`

##TODO/Roadmap:
- MacOSX and Windows support
- Video Quality Assessment metrics
- Spatial-Temporal filtering helper functions
- Speedup motion estimation routines
- More Interfacing with backend ffmpeg/avconv to take advantage of filter routines


##For Contributors:

Quick tutorial on how to go about setting up your environment to contribute to scikit-video: 

https://github.com/beyondmetis/scikit-video/blob/master/CONTRIBUTING.md

##Testing

After installation, you can launch the test suite from outside the source directory (you will need to have the nose package installed). To ensure that both python2 and python3 versions pass:

$ nosetests2 -v skvideo

$ nosetests3 -v skvideo

Copyright &copy; 2015 scikit-video team. Special thanks to Martín Blech for xmltodict, the authors of pymediaprobe, and the developers behind imageio and pyav for releasing under BSD licenses.
