scikit-video
============

##Video Processing SciKit

Borrowing coding styles and conventions from scikit-image and scikit-learn,
scikit-video is a Python module for video processing built on top of 
SciPy, Numpy, and libav. 

This project is available under the BSD.

##Dependencies:

- At least one of {ffmpeg, libav}
- python2
- numpy
- scipy
- (optional) pygame, matplotlib for plotting video frames

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

Copyright 2015 Todd Goodall
