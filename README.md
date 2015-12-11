

scikit-video
============

[![Travis](https://api.travis-ci.org/scikit-video/scikit-video.png?branch=master)](https://travis-ci.org/scikit-video/scikit-video)

##Video Processing SciKit

Borrowing coding styles and conventions from scikit-image and scikit-learn,
scikit-video is a Python module for video processing built on top of 
scipy, numpy, ffmpeg, and mediainfo.

This project is distributed under the 3-clause BSD.

##Dependencies:

Integration testing performed using an Ubuntu 12.04 LTS and anaconda packages. Listed below are the minimum versions tested:

- ffmpeg (version >= 1.0)
- mediainfo (version >= 0.7.52)
- python2 (2.6 or 2.7)
- numpy (version >= 1.9.2)
- scipy (version >= 0.16.0)

##Installation:

Clone the scikit-video repository, run

`python2 setup.py build`

then 

`sudo python2 setup.py install`

##Example of reading a video directly into memory:

```python
>>> import skvideo.io
>>> import skvideo.datasets
>>> videodata = skvideo.io.vread(skvideo.datasets.bigbuckbunny())
>>> videodata.shape
(132, 720, 1280, 3)
```

##Example of reading a video frame-by-frame:

```python
>>> import skvideo.io
>>> import skvideo.datasets
>>> videogen = skvideo.io.vread_generator(skvideo.datasets.bigbuckbunny())
>>> for frame in videogen:
...    frame.shape
(720, 1280, 3)
(720, 1280, 3)
     ...
     ...
     ...
(720, 1280, 3)
```


##TODO:
- Introduce quality metrics
- Introduce motion estimation code library
- Introduce temporal filtering helper functions and a library of window functions


##For Contributors:

Quick tutorial on how to go about setting up your environment to contribute to scikit-video: https://github.com/beyondmetis/scikit-video/blob/master/CONTRIBUTING.md

##Testing

After installation, you can launch the test suite from outside the source directory (you will need to have the nose package installed):

$ nosetests2 -v skvideo

Copyright &copy; 2015 Todd Goodall. Special thanks to Martín Blech for xmltodict, the authors of pymediaprobe, and the developers behind imageio and pyav for releasing under BSD licenses.
