
![scikit-video logo](doc/images/scikit-video.png)


scikit-video
============

[![Travis](https://api.travis-ci.org/scikit-video/scikit-video.png?branch=master)](https://travis-ci.org/scikit-video/scikit-video)

##Video Processing SciKit

Borrowing coding styles and conventions from scikit-image and scikit-learn,
scikit-video is a Python module for video processing built on top of 
scipy, numpy, and ffmpeg.

This project is distributed under the 3-clause BSD.

Visit the documentation at http://www.scikit-video.org

##Dependencies:

Integration testing performed using an Ubuntu 12.04 LTS and anaconda packages. Listed below are the minimum versions tested:

- Either ffmpeg (version >= 2.1) or libav (version >= 11.4)
- python2 (2.6 or 2.7)
- numpy (version >= 1.9.2)
- scipy (version >= 0.16.0)
- mediainfo (optional)

##Installation:

### First method:

pip install scikit-video2

### Second method:

Clone the scikit-video repository, run

`python2 setup.py build`

then 

`sudo python2 setup.py install`

##TODO:
- MacOSX and Windows support
- Python 3 support
- Video Quality Assessment metrics
- Temporal filtering helper functions


##For Contributors:

Quick tutorial on how to go about setting up your environment to contribute to scikit-video: https://github.com/beyondmetis/scikit-video/blob/master/CONTRIBUTING.md

##Testing

After installation, you can launch the test suite from outside the source directory (you will need to have the nose package installed):

$ nosetests2 -v skvideo

Copyright &copy; 2015 scikit-video team. Special thanks to Martín Blech for xmltodict, the authors of pymediaprobe, and the developers behind imageio and pyav for releasing under BSD licenses.
