# -*- coding: utf-8 -*-
# Copyright (c) 2015, imageio contributors
# distributed under the terms of the BSD License.

# insprired/stolen from Almar Klein's imageio code

""" Plugin that uses ffmpeg to read and write series of images to
a wide range of video formats.

Code inspired/based on code from moviepy: https://github.com/Zulko/moviepy/
by Zulko


Media info code comes largely from pymediainfo:

The MIT License

Copyright (c) 2010-2014, Patrick Altman <paltman@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
    THE SOFTWARE.

    http://www.opensource.org/licenses/mit-license.php


"""

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
        """Opens the file, creates the pipe. 
        
        Launches a subprocess of FFmpeg after 
        probing the file for details with :ref:`MProbe`.
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
        for i in xrange(self.inputframenum):
            yield self._readFrame()



# uses FFmpeg to write the given data to a given file with parameters
class FFmpegWriter():
    def __init__(self, filename, datashape, pix_fmt='rgb24', outputdict={}, verbosity=0):
        # pixfmt can be 'gray', 'gray8a', 'rgb24' or 'rgba'

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
        if self._proc is None:  # pragma: no cover
            return  # no process
        if self._proc.poll() is not None:
            return  # process already dead
        if self._proc.stdin:
            self._proc.stdin.close()
        self._proc.wait()
        self._proc = None


    def writeFrame(self, im):
        # Ensure that image is in uint8
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
