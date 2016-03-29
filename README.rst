
![scikit-video logo](doc/images/scikit-video.png)



scikit-video v1.1.2
===================

[![The BSD-3 License](https://img.shields.io/badge/license-BSD--3--Clause-blue.svg)](https://spdx.org/licenses/BSD-3-Clause#licenseText)
[![Travis](https://api.travis-ci.org/scikit-video/scikit-video.png?branch=master)](https://travis-ci.org/scikit-video/scikit-video)
[![Coverage Status](https://coveralls.io/repos/github/scikit-video/scikit-video/badge.svg?branch=master)](https://coveralls.io/github/scikit-video/scikit-video?branch=master)
[![CircleCI](https://circleci.com/gh/scikit-video/scikit-video/tree/master.svg?style=shield&circle-token=:circle-token)](https://circleci.com/gh/scikit-video/scikit-video)


##Video Processing SciKit

Borrowing coding styles and conventions from scikit-image and scikit-learn,
scikit-video is a Python module for video processing built on top of 
scipy, numpy, and ffmpeg/libav.

This project is distributed under the 3-clause BSD.

Visit the documentation at http://www.scikit-video.org


##Dependencies

Here are the requirements needed to use scikit-video.

- Either ffmpeg (version >= 2.1) or libav (either version 10 or 11)
- python (2.6, 2.7, 3.3, and 3.5)
- numpy (version >= 1.9.2)
- scipy (version >= 0.16.0)
- mediainfo (optional)

##Installation

`$ sudo pip install sk-video`

##Installation from github

1. Make sure minimum dependencies (above) are installed. In addition, install setuptools (python-setuptools or python2-setuptools).

2. Clone the scikit-video repository, enter the project directory, then run

   `$ python setup.py build`

3. In that same project directory, run the command

   `$ sudo python setup.py install`

where `python` may refer to either python2 or python3.

##Known conflicts

If you installed scikit-video prior to version 1.1.2, you may have an import conflict. Run the following command to fix it

`$ sudo pip uninstall scikit-video`

To check that the conflict no longer exists, import skvideo and print the file path

```python
import skvideo
print skvideo.__file__
```

if setup correctly, you should see `sk_video` in the path:

`/usr/lib/python2.7/site-packages/sk_video-1.1.1-py2.7.egg/skvideo/__init__.pyc`


##TODO/Roadmap
- Windows support
- Spatial-Temporal filtering helper functions
- Speedup motion estimation routines
- More ffmpeg/avconv interfacing


##For Contributors

Quick tutorial on how to go about setting up your environment to contribute to scikit-video: 

https://github.com/beyondmetis/scikit-video/blob/master/CONTRIBUTING.md


##Testing

After installation, you can launch the test suite from outside the source directory (you will need to have the nose package installed). To ensure that both python2 and python3 versions pass:

$ nosetests2 -v skvideo

$ nosetests3 -v skvideo

Copyright &copy; 2015 scikit-video team. Special thanks to Martín Blech for xmltodict, the authors of pymediaprobe, and the developers behind imageio and pyav for releasing under BSD licenses.
