""" Plugin that uses ffmpeg to read and write series of images to
a wide range of video formats.

"""

# Copyright (c) 2015, imageio contributors
# distributed under the terms of the BSD License (included in release).
# lifted from Almar Klein's imageio code

import sys
import os
import stat
import re
import time
import threading
import subprocess as sp
import logging
import json

import numpy as np

from mprobe import mprobe
from .._utils import *

# uses FFmpeg to read the given file with parameters
class FFmpegReader():
    """Reads frames using FFmpeg

    Using FFmpeg as a backend, this class
    provides sane initializations meant to
    handle the default case well.

    """
    def __init__(self, filename, inputdict={}, outputdict={}, verbosity=0):
        """Initializes FFmpeg in reading mode with the given parameters

        During initialization, additional parameters about the video file
        are parsed using :func:`skvideo.io.mprobe`. Then FFmpeg is launched
        as a subprocess.

        Parameters
        ----------
        filename : string
            Video file path

        inputdict : dict
            Input dictionary parameters. How to interpret the filename.

        outputdict : dict
            Output dictionary parameters. How to provide and interpret 
            the data during the read.

        Returns
        -------
        none

        """

        # Output args, for writing to pipe
        self._probe = mprobe(filename)

        # set the width, height, numframes
        self.inputwidth = np.int(self._probe["Video"]["Width"][0])
        self.inputheight = np.int(self._probe["Video"]["Height"][0])
        self.inputfps = np.float(self._probe["Video"]["Frame_rate"][0])
        self.inputframenum = np.int(self._probe["Video"]["Frame_count"])
        self.inputdepth = np.int(self._probe["Video"]["Bit_depth"][0])
        self.inputdepth = 3

        self._filename = filename


        oargs = ['-f', 'image2pipe',
                 '-pix_fmt', 'rgb24', #self._pix_fmt,
                 '-vcodec', 'rawvideo']

        # Create input args
        iargs = []
        for key in inputdict.keys():
            iargs.append(key)
            iargs.append(inputdict[key])

        for key in outputdict.keys():
            oargs.append(key)
            oargs.append(outputdict[key])

        # Create process
        cmd = ["ffmpeg"] + iargs + ['-i', self._filename] + oargs + ['-']

        if verbosity == 0:
            self._proc = sp.Popen(cmd, stdin=sp.PIPE,
                                  stdout=sp.PIPE, stderr=sp.PIPE)
        else:
            self._proc = sp.Popen(cmd, stdin=sp.PIPE,
                                  stdout=sp.PIPE, stderr=None)

    def getShape(self):
        """Returns a tuple (T, M, N, C) 
        
        Returns the video shape in number of frames, height, width, and channels per pixel.
        """
           
        return self.inputframenum, self.inputheight, self.inputwidth, self.inputdepth 


    def _close(self):
        self._terminate(0.05)  # Short timeout
        self._proc = None

    def _terminate(self, timeout=1.0):
        """ Terminate the sub process.
        """
        # Check
        if self._proc is None:  # pragma: no cover
            return  # no process
        if self._proc.poll() is not None:
            return  # process already dead
        # Terminate process
        self._proc.terminate()
        # Wait for it to close (but do not get stuck)
        etime = time.time() + timeout
        while time.time() < etime:
            time.sleep(0.01)
            if self._proc.poll() is not None:
                break

    def _read_frame_data(self):
        # Init and check
        framesize = self.inputdepth * self.inputwidth * self.inputheight
        assert self._proc is not None

        try:
            # Read framesize bytes
            s = read_n_bytes(self._proc.stdout, framesize)
            # Check
            assert len(s) == framesize
        except Exception as err:
            self._terminate()
            err1 = str(err)
            raise RuntimeError("%s" % (err1,))
        return s

    def _readFrame(self):
        # Read and convert to numpy array
        # t0 = time.time()
        s = self._read_frame_data()
        result = np.fromstring(s, dtype='uint8')
        result = result.reshape((self.inputheight, self.inputwidth, self.inputdepth))
        # t1 = time.time()
        # print('etime', t1-t0)

        # Store and return
        self._lastread = result
        return result

    def nextFrame(self):
        """Yields frames using a generator 
        
        Returns T ndarrays of size (M, N, C), where T is number of frames, 
        M is height, N is width, and C is number of channels per pixel.

        """
        for i in xrange(self.inputframenum):
            yield self._readFrame()


class FFmpegWriter():
    """Writes frames using FFmpeg

    Using FFmpeg as a backend, this class
    provides sane initializations for the default case.
    """
    def __init__(self, filename, datashape, pix_fmt='rgb24', outputdict={}, verbosity=0):
        """Initializes FFmpeg in writing mode with the given parameters

        Parameters
        ----------
        filename : string
            Video file path

        datashape : ndarray
            Tuple of configuration (T, M, N, C), where T
            is the number of frames, M is the height, N is
            width, and C is depth. C is currently hardcoded to 3.

        pix_fmt : string
            Can be one of 'gray', 'gray8a', 'rgb24' or 'rgba'. 
            which corresponds to 1, 2, 3, and 4 bytes per pixel, respectively.

        Returns
        -------
        none

        """

        self._filename = filename

        # TODO: check that size was passed into the dictionary

        if len(datashape) == 4:
            self.inputframenum, self.inputheight, self.inputwidth, self.inputdepth = datashape
        else:
            self.inputframenum, self.inputheight, self.inputwidth = datashape
            self.inputdepth = 1

        # TODO: check dictionary for settings, and provide defaults

        cmd = ["ffmpeg", '-y']
        cmd.extend(["-s", "%sx%s" % (self.inputwidth, self.inputheight)])
        cmd.extend(["-pix_fmt", pix_fmt])
        cmd.extend(["-f", "rawvideo"])
        cmd.extend(["-i", "-"])

        # all the output commands based on outputdict
        cmd.extend(["-pix_fmt", "yuv420p"])

        # here is where the settings should go
        #check_dict(outputdict, "-y", "")
        #check_dict(outputdict, "-f", "rawvideo")
        #check_dict(outputdict, "-s", "%sx%s" % (self.inputheight, self.inputwidth))
        #check_dict(outputdict, "-pix_fmt", self._pix_fmt)
        #check_dict(outputdict, "-r", "%.08f" % (30,))
        #check_dict(outputdict, "-vcodec", "libx264")

        #for key in outputdict.keys():
        #    cmd.append(key)
        #    cmd.append(outputdict[key])


        # lastly, append filename onto the command
        cmd.append(self._filename)

        # For showing command if needed
        self._cmd = " ".join(cmd)

        # Launch process
        if verbosity == 0:
            self._proc = sp.Popen(cmd, stdin=sp.PIPE,
                                  stdout=sp.PIPE, stderr=sp.PIPE)
        else:
            self._proc = sp.Popen(cmd, stdin=sp.PIPE,
                                  stdout=sp.PIPE, stderr=None)

    def close(self):
	"""Closes the video and terminates FFmpeg process

	"""
        if self._proc is None:  # pragma: no cover
            return  # no process
        if self._proc.poll() is not None:
            return  # process already dead
        if self._proc.stdin:
            self._proc.stdin.close()
        self._proc.wait()
        self._proc = None


    def writeFrame(self, im):
	"""Sends ndarray frames to FFmpeg

	"""

        # Ensure that ndarray image is in uint8
        im = np.array(im)
        im = im.astype(np.uint8)

        if len(im.shape) == 3:
            h, w, c = im.shape
        else:
            h, w = im.shape
            c = 1

        # Check size of image
        if h != self.inputheight or w != self.inputwidth:
            raise ValueError('All images in a movie should have same size')
        if c != self.inputdepth:
            raise ValueError('All images in a movie should have same '
                             'number of channels')

        assert self._proc is not None  # Check status

        # Write
        try:
            self._proc.stdin.write(im.tostring())
        except IOError as e:
            # Show the command and stderr from pipe
            msg = '{0:}\n\nFFMPEG COMMAND:\n{1:}\n\nFFMPEG STDERR ' \
                  'OUTPUT:\n'.format(e, self._cmd)
            raise IOError(msg)
