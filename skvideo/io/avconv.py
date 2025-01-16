""" Plugin that uses Libav to read and write series of images to
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

from .avprobe import avprobe
from ..utils import *
from .. import _HAS_AVCONV
from .. import _AVCONV_PATH
from .. import _AVCONV_APPLICATION

# uses libav to read the given file with parameters
class LibAVReader():
    """Reads frames using Libav

    Using libav as a backend, this class
    provides sane initializations meant to
    handle the default case well.

    """

    def __init__(self, filename, inputdict=None, outputdict=None, verbosity=0):
        """Initializes libav in reading mode with the given parameters

        During initialization, additional parameters about the video file
        are parsed using :func:`skvideo.io.avprobe`. Then avconv is launched
        as a subprocess. Parameters passed into inputdict are parsed and
        used to set as internal variables about the video. If the parameter,
        such as "Height" is not found in the inputdict, it is found through
        scanning the file's header information. If not in the header, avprobe
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
        # check if avconv exists in the path
        assert _HAS_AVCONV, "Cannot find installation of libav (which comes with avprobe)."


        israw = 0

        if not inputdict:
            inputdict = {}

        if not outputdict:
            outputdict = {}

        # General information
        _, self.extension = os.path.splitext(filename)
        self.size = os.path.getsize(filename)
        self.probeInfo = avprobe(filename)

        viddict = {}
        if "video" in self.probeInfo:
            viddict = self.probeInfo["video"]

        self.inputfps = -1
        if ("-r" in inputdict):
            self.inputfps = np.int(inputdict["-r"])
        elif "avg_frame_rate" in viddict:
            # check for the slash
            frtxt = viddict["avg_frame_rate"]
            parts = frtxt.split('/') 
            if len(parts) > 1:
                num = np.float(parts[0])
                den = np.float(parts[1])
                if den == 0:
                  self.inputfps = 25
                else:
                  self.inputfps = np.float(parts[0])/np.float(parts[1])
            else:
                self.inputfps = np.float(frtxt)
        else:
            # simply default to a common 25 fps and warn
            self.inputfps = 25
            # No input frame rate detected. Assuming 25 fps. Consult documentation on I/O if this is not desired.

        # if we don't have width or height at all, raise exception
        if ("-s" in inputdict):
            widthheight = inputdict["-s"].split('x')
            self.inputwidth = np.int(widthheight[0])
            self.inputheight = np.int(widthheight[1])
        elif (("width" in viddict) and ("height" in viddict)):
            self.inputwidth = np.int(viddict["width"])
            self.inputheight = np.int(viddict["height"])
        else:
            raise ValueError("No way to determine width or height from video. Need `-s` in `inputdict`. Consult documentation on I/O.")

        self.bpp = -1 # bits per pixel
        self.pix_fmt = ""
        # completely unsure of this:
        if ("-pix_fmt" in inputdict):
            self.pix_fmt = inputdict["-pix_fmt"]
        elif ("pix_fmt" in viddict):
            # parse this bpp
            self.pix_fmt = viddict["pix_fmt"]
        else:
            self.pix_fmt = "yuvj444p"
            if verbosity != 0:
                warnings.warn("No input color space detected. Assuming yuvj444p.", UserWarning)

        self.inputdepth = np.int(bpplut[self.pix_fmt][0])
        self.bpp = np.int(bpplut[self.pix_fmt][1])

        if (self.extension == ".yuv"):
            israw = 1

        if ("-vframes" in outputdict):
            self.inputframenum = np.int(outputdict["-vframes"])
        elif ("nb_frames" in viddict):
            self.inputframenum = np.int(viddict["nb_frames"])
        elif israw == 1:
            # we can compute it based on the input size and color space
            self.inputframenum = np.int(self.size / (self.inputwidth * self.inputheight * (self.bpp/8.0)))
        else:
            self.inputframenum = -1
            if verbosity != 0:
                warnings.warn("Cannot determine frame count. Scanning input file, this is slow when repeated many times. Need `-vframes` in inputdict. Consult documentation on I/O.", UserWarning) 

        if israw != 0:
            inputdict['-pix_fmt'] = self.pix_fmt

        self._filename = filename

        if '-f' not in outputdict:
            outputdict['-f'] = "rawvideo"

        if '-pix_fmt' not in outputdict:
            outputdict['-pix_fmt'] = "rgb24"

        if '-s' in outputdict:
            widthheight = outputdict["-s"].split('x')
            self.outputwidth = np.int(widthheight[0])
            self.outputheight = np.int(widthheight[1])
        else:
            self.outputwidth = self.inputwidth
            self.outputheight = self.inputheight

        self.outputdepth = np.int(bpplut[outputdict['-pix_fmt']][0])
        self.outputbpp = np.int(bpplut[outputdict['-pix_fmt']][1])


        # Create input args
        iargs = []
        for key in inputdict.keys():
            iargs.append(key)
            iargs.append(inputdict[key])

        oargs = []
        for key in outputdict.keys():
            oargs.append(key)
            oargs.append(outputdict[key])

        if self.inputframenum == -1:
            # open process with supplied arguments,
            # grabbing number of frames using ffprobe
            probecmd = [_AVCONV_PATH + "/avprobe"] + ["-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries", "stream=nb_read_frames", "-of", "default=nokey=1:noprint_wrappers=1", self._filename]
            self.inputframenum = np.int(check_output(probecmd).split('\n')[0])

        # Create process

        if verbosity == 0:
            cmd = [_AVCONV_PATH + "/" + _AVCONV_APPLICATION, "-nostats", "-loglevel", "0"] + iargs + ['-i', self._filename] + oargs + ['pipe:']
            self._proc = sp.Popen(cmd, stdin=sp.PIPE,
                                  stdout=sp.PIPE, stderr=sp.PIPE)
        else:
            cmd = [_AVCONV_PATH + "/" + _AVCONV_APPLICATION] + iargs + ['-i', self._filename] + oargs + ['pipe:']
            print(cmd)
            self._proc = sp.Popen(cmd, stdin=sp.PIPE,
                                  stdout=sp.PIPE, stderr=None)

    def getShape(self):
        """Returns a tuple (T, M, N, C) 
        
        Returns the video shape in number of frames, height, width, and channels per pixel.
        """
           
        return self.inputframenum, self.inputheight, self.inputwidth, self.inputdepth 

    def close(self):
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
        framesize = self.outputdepth * self.outputwidth * self.outputheight
        assert self._proc is not None

        try:
            # Read framesize bytes
            arr = np.fromstring(self._proc.stdout.read(framesize), dtype=np.uint8)
            assert len(arr) == framesize
        except Exception as err:
            self._terminate()
            err1 = str(err)
            raise RuntimeError("%s" % (err1,))
        return arr

    def _readFrame(self):
        # Read and convert to numpy array
        # t0 = time.time()
        s = self._read_frame_data()
        result = np.fromstring(s, dtype='uint8')
        result = result.reshape((self.outputheight, self.outputwidth, self.outputdepth))
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
        for i in range(self.inputframenum):
            yield self._readFrame()


class LibAVWriter():
    """Writes frames using libav

    Using libav as a backend, this class
    provides sane initializations for the default case.
    """
    def __init__(self, filename, inputdict=None, outputdict=None, verbosity=0):
        """Prepares parameters for avconv
    
        Does not instantiate the avconv subprocess, but simply
        prepares the required parameters.

        Parameters
        ----------
        filename : string
            Video file path

        inputdict : dict
            Input dictionary parameters, i.e. how to interpret the data coming from python.

        outputdict : dict
            Output dictionary parameters, i.e. how to encode the data 
            when writing to file.

        Returns
        -------
        none

        """

        assert _HAS_AVCONV, "Cannot find installation of libav (which comes with avprobe)."

        # complain about the use of avconv :(
        warnings.warn("avconv corrupts video data between reading and writing. Search for \"drift\" in the test script test_vread.py for proof. Please consider using FFMPEG.", UserWarning)

        if not inputdict:
            inputdict = {}

        if not outputdict:
            outputdict = {}

        self._filename = filename
        _, self.extension = os.path.splitext(self._filename)

        # extract extension used (only used for raw outputs)

        self.inputdict = inputdict
        self.outputdict = outputdict

        self.verbosity = verbosity

        if "-f" not in self.inputdict:
            self.inputdict["-f"] = "rawvideo"
        self.warmStarted = 0

        self.rgb2grayhack = 0

    def _warmStart(self, M, N, C):
        self.warmStarted = 1

        if "-pix_fmt" not in self.inputdict:
            # check the number channels to guess 
            if C == 1:
                # unfortunately, 'gray' has a bug for avconv
                # enable gray -> rgb hack
                self.inputdict["-pix_fmt"] = "gray"
                self.inputdict["-pix_fmt"] = "rgb24"
                self.rgb2grayhack = 1
                C = 3
            elif C == 2:
                self.inputdict["-pix_fmt"] = "ya8"
            elif C == 3:
                self.inputdict["-pix_fmt"] = "rgb24"
            elif C == 4:
                self.inputdict["-pix_fmt"] = "rgba"
            else:
                raise NotImplemented

        self.bpp = bpplut[self.inputdict["-pix_fmt"]][1]
        self.inputNumChannels = bpplut[self.inputdict["-pix_fmt"]][0]
        
        assert self.inputNumChannels == C, "Failed to pass the correct number of channels %d for the pixel format %s." % (self.inputNumChannels, self.inputdict["-pix_fmt"])  

        if ("-s" in self.inputdict):
            widthheight = self.inputdict["-s"].split('x')
            self.inputwidth = np.int(widthheight[0])
            self.inputheight = np.int(widthheight[1])
        else: 
            self.inputdict["-s"] = str(N) + "x" + str(M)
            self.inputwidth = N
            self.inputheight = M

        self.outputdict["-sws_flags"] = "bitexact"

        # prepare output parameters, if raw
        if self.extension == ".yuv":
            if "-pix_fmt" not in self.outputdict:
                self.outputdict["-pix_fmt"] = "yuvj444p"
                if self.verbosity != 0:
                    warnings.warn("No output color space provided. Assuming yuvj444p.", UserWarning)

        # Create input args
        iargs = []
        for key in self.inputdict.keys():
            iargs.append(key)
            iargs.append(self.inputdict[key])

        oargs = []
        for key in self.outputdict.keys():
            oargs.append(key)
            oargs.append(self.outputdict[key])

        cmd = [_AVCONV_PATH + "/avconv", "-y"] + iargs + ["-i", "pipe:"] + oargs + [self._filename]
        print(cmd)

        self._cmd = " ".join(cmd)

        # Launch process
        if self.verbosity == 0:
            self._proc = sp.Popen(cmd, stdin=sp.PIPE,
                                  stdout=sp.PIPE, stderr=sp.PIPE)
        else:
            self._proc = sp.Popen(cmd, stdin=sp.PIPE,
                                  stdout=sp.PIPE, stderr=None)


    def close(self):
        """Closes the video and terminates avconv process

        """
        if not self.warmStarted:
            warnings.warn("LibAVWriter: No frames written.")
            return

        if self._proc is None:  # pragma: no cover
            return  # no process
        if self._proc.poll() is not None:
            return  # process already dead
        if self._proc.stdin:
            self._proc.stdin.close()
        self._proc.wait()
        self._proc = None


    def writeFrame(self, im):
        """Sends ndarray frames to avconv

        """
        vid = vshape(im)
        T, M, N, C = vid.shape
        if not self.warmStarted:
            self._warmStart(M, N, C)

        # Ensure that ndarray image is in uint8
        vid[vid > 255] = 255
        vid[vid < 0] = 0
        vid = vid.astype(np.uint8)

        if self.rgb2grayhack:
            # convert grayscale vid to 3 channel
            vid2 = np.zeros((T, M, N, 3), dtype=np.uint8)
            vid2[:, :, :, 0] = vid[:, :, :, 0]
            vid2[:, :, :, 1] = vid[:, :, :, 0]
            vid2[:, :, :, 2] = vid[:, :, :, 0]
            vid = vid2
            T, M, N, C = vid.shape

        # Check size of image
        if M != self.inputheight or N != self.inputwidth:
            raise ValueError('All images in a movie should have same size')
        if C != self.inputNumChannels:
            raise ValueError('All images in a movie should have same '
                             'number of channels')

        assert self._proc is not None  # Check status

        # Write
        try:
            self._proc.stdin.write(vid.tostring())
        except IOError as e:
            # Show the command and stderr from pipe
            msg = '{0:}\n\navconv COMMAND:\n{1:}\n\navconv STDERR ' \
                  'OUTPUT:\n'.format(e, self._cmd)
            raise IOError(msg)
