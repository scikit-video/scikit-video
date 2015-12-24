""" Plugin that uses ffmpeg to read and write series of images to
a wide range of video formats.

"""

# Heavily inspired from Almar Klein's imageio code
# Copyright (c) 2015, imageio contributors
# distributed under the terms of the BSD License (included in release).

import sys
import os
import stat
import re
import time
import threading
import subprocess as sp
import logging
import json
import warnings

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
        as a subprocess. Parameters passed into inputdict are parsed and
        used to set as internal variables about the video. If the parameter,
        such as "Height" is not found in the inputdict, it is found through
        scanning the file's header information. If not in the header, ffprobe
        is used to decode the file to determine the information. In the case
        that the information is not supplied and connot be inferred from the
        input file, a ValueError exception is thrown.

        Parameters
        ----------
        filename : string
            Video file path

        inputdict : dict
            Input dictionary parameters, i.e. how to interpret the input file.

        outputdict : dict
            Output dictionary parameters, i.e. how to encode the data 
            when sending back to the python process.

        Returns
        -------
        none

        """

        # check for filters in the inputdict
        # if 
        # self.parsefilters

        # Output args, for writing to pipe
        self._probe = mprobe(filename)

        self.size = 0
        self.extension = ""
        if "General" in self._probe:
            self.size = np.int(self._probe["General"]["File_size"][0])
            self.extension = self._probe["General"]["File_extension"]

        viddict = {}
        if "Video" in self._probe:
            viddict = self._probe["Video"]

        self.inputfps = -1
        if ("-r" in inputdict):
            self.inputfps = np.int(inputdict["-r"])
        elif "Frame_rate" in viddict:
            self.inputfps = np.int(viddict["Frame_rate"][0])
        else:
            # simply default to a common 25 fps and warn
            self.inputfps = 25
            warnings.warn("No input frame rate detected. Assuming 25 fps. Consult documentation on I/O if this is not desired.", UserWarning) 


        # if we don't have width or height at all, raise exception
        if ("-s" in inputdict):
            widthheight = inputdict["-s"].split('x')
            self.inputwidth = np.int(widthheight[0])
            self.inputheight = np.int(widthheight[1])
        elif (("Width" in viddict) and ("Height" in viddict)):
            self.inputwidth = np.int(self._probe["Video"]["Width"][0])
            self.inputheight = np.int(self._probe["Video"]["Height"][0])
        else:
            raise ValueError("No way to determine width or height from video. Need `-s` in `inputdict`. Consult documentation on I/O.")

        bpp = 0
        # completely unsure of this:
        if ("-pix_fmt" in inputdict):
            # parse this bpp
            self.inputdepth = 3
        elif ("Bit_depth" in viddict):
            self.inputdepth = np.int(self._probe["Video"]["Bit_depth"][0])
            bpp = 0
        else:
            self.inputdepth = 3
            warnings.warn("No input color space detected. Assuming yuv420.", UserWarning)

        if ("-vframes" in inputdict):
            self.inputframenum = np.int(inputdict["-vframes"])
        elif ("Frame_count" in viddict):
            self.inputframenum = np.int(self._probe["Video"]["Frame_count"])
        elif (self.extension == "yuv"):
            # we can compute it based on the input size and color space
            self.inputframenum = np.int(self.size / (self.inputwidth * self.inputheight * 3.0/2.0))
        else:
            self.inputframenum = -1
            warnings.warn("Cannot determine frame count. Scanning input file, this is slow when repeated many times. Need `-vframes` in inputdict. Consult documentation on I/O.", UserWarning) 

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

        if self.inputframenum == -1:
            # open process with supplied arguments,
            # grabbing number of frames using ffprobe
            probecmd = ["ffprobe"] + ["-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries", "stream=nb_read_frames", "-of", "default=nokey=1:noprint_wrappers=1", self._filename]

            # this may fail if the video is raw
            try:
                self.inputframenum = np.int(check_output(probecmd))
            except:
                pass

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
