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

from ffprobe import ffprobe
from .._utils import *

# uses FFmpeg to read the given file with parameters
class FFmpegReader():
    """Reads frames using FFmpeg

    Using FFmpeg as a backend, this class
    provides sane initializations meant to
    handle the default case well.

    """

    # dictionary based on pix_fmt keys
    # first element is number of components
    # second element is number of bits per pixel
    bpplut = {}
    bpplut["yuv420p"] = [3, 12]
    bpplut["yuyv422"] = [3, 16]
    bpplut["rgb24"] = [3, 24]
    bpplut["bgr24"] = [3, 24]
    bpplut["yuv422p"] = [3, 16]
    bpplut["yuv444p"] = [3, 24]
    bpplut["yuv410p"] = [3, 9]
    bpplut["yuv411p"] = [3, 12]
    bpplut["gray"] = [1, 8]
    bpplut["monow"] = [1, 1]
    bpplut["monob"] = [1, 1]
    bpplut["pal8"] = [1, 8]
    bpplut["yuvj420p"] = [3, 12]
    bpplut["yuvj422p"] = [3, 16]
    bpplut["yuvj444p"] = [3, 24]
    bpplut["xvmcmc"] = [0, 0]
    bpplut["xvmcidct"] = [0, 0]
    bpplut["uyvy422"] = [3, 16]
    bpplut["uyyvyy411"] = [3, 12]
    bpplut["bgr8"] = [3, 8]
    bpplut["bgr4"] = [3, 4]
    bpplut["bgr4_byte"] = [3, 4]
    bpplut["rgb8"] = [3, 8]
    bpplut["rgb4"] = [3, 4]
    bpplut["rgb4_byte"] = [3, 4]
    bpplut["nv12"] = [3, 12]
    bpplut["nv21"] = [3, 12]
    bpplut["argb"] = [4, 32]
    bpplut["rgba"] = [4, 32]
    bpplut["abgr"] = [4, 32]
    bpplut["bgra"] = [4, 32]
    bpplut["gray16be"] = [1, 16]
    bpplut["gray16le"] = [1, 16]
    bpplut["yuv440p"] = [3, 16]
    bpplut["yuvj440p"] = [3, 16]
    bpplut["yuva420p"] = [4, 20]
    bpplut["vdpau_h264"] = [0, 0]
    bpplut["vdpau_mpeg1"] = [0, 0]
    bpplut["vdpau_mpeg2"] = [0, 0]
    bpplut["vdpau_wmv3"] = [0, 0]
    bpplut["vdpau_vc1"] = [0, 0]
    bpplut["rgb48be"] = [3, 48]
    bpplut["rgb48le"] = [3, 48]
    bpplut["rgb565be"] = [3, 16]
    bpplut["rgb565le"] = [3, 16]
    bpplut["rgb555be"] = [3, 15]
    bpplut["rgb555le"] = [3, 15]
    bpplut["bgr565be"] = [3, 16]
    bpplut["bgr565le"] = [3, 16]
    bpplut["bgr555be"] = [3, 15]
    bpplut["bgr555le"] = [3, 15]
    bpplut["vaapi_moco"] = [0, 0]
    bpplut["vaapi_idct"] = [0, 0]
    bpplut["vaapi_vld"] = [0, 0]
    bpplut["yuv420p16le"] = [3, 24]
    bpplut["yuv420p16be"] = [3, 24]
    bpplut["yuv422p16le"] = [3, 32]
    bpplut["yuv422p16be"] = [3, 32]
    bpplut["yuv444p16le"] = [3, 48]
    bpplut["yuv444p16be"] = [3, 48]
    bpplut["vdpau_mpeg4"] = [0, 0]
    bpplut["dxva2_vld"] = [0, 0]
    bpplut["rgb444le"] = [3, 12]
    bpplut["rgb444be"] = [3, 12]
    bpplut["bgr444le"] = [3, 12]
    bpplut["bgr444be"] = [3, 12]
    bpplut["ya8"] = [2, 16]
    bpplut["bgr48be"] = [3, 48]
    bpplut["bgr48le"] = [3, 48]
    bpplut["yuv420p9be"] = [3, 13]
    bpplut["yuv420p9le"] = [3, 13]
    bpplut["yuv420p10be"] = [3, 15]
    bpplut["yuv420p10le"] = [3, 15]
    bpplut["yuv422p10be"] = [3, 20]
    bpplut["yuv422p10le"] = [3, 20]
    bpplut["yuv444p9be"] = [3, 27]
    bpplut["yuv444p9le"] = [3, 27]
    bpplut["yuv444p10be"] = [3, 30]
    bpplut["yuv444p10le"] = [3, 30]
    bpplut["yuv422p9be"] = [3, 18]
    bpplut["yuv422p9le"] = [3, 18]
    bpplut["vda_vld"] = [0, 0]
    bpplut["gbrp"] = [3, 24]
    bpplut["gbrp9be"] = [3, 27]
    bpplut["gbrp9le"] = [3, 27]
    bpplut["gbrp10be"] = [3, 30]
    bpplut["gbrp10le"] = [3, 30]
    bpplut["gbrp16be"] = [3, 48]
    bpplut["gbrp16le"] = [3, 48]
    bpplut["yuva420p9be"] = [4, 22]
    bpplut["yuva420p9le"] = [4, 22]
    bpplut["yuva422p9be"] = [4, 27]
    bpplut["yuva422p9le"] = [4, 27]
    bpplut["yuva444p9be"] = [4, 36]
    bpplut["yuva444p9le"] = [4, 36]
    bpplut["yuva420p10be"] = [4, 25]
    bpplut["yuva420p10le"] = [4, 25]
    bpplut["yuva422p10be"] = [4, 30]
    bpplut["yuva422p10le"] = [4, 30]
    bpplut["yuva444p10be"] = [4, 40]
    bpplut["yuva444p10le"] = [4, 40]
    bpplut["yuva420p16be"] = [4, 40]
    bpplut["yuva420p16le"] = [4, 40]
    bpplut["yuva422p16be"] = [4, 48]
    bpplut["yuva422p16le"] = [4, 48]
    bpplut["yuva444p16be"] = [4, 64]
    bpplut["yuva444p16le"] = [4, 64]
    bpplut["vdpau"] = [0, 0]
    bpplut["xyz12le"] = [3, 36]
    bpplut["xyz12be"] = [3, 36]
    bpplut["nv16"] = [3, 16]
    bpplut["nv20le"] = [3, 20]
    bpplut["nv20be"] = [3, 20]
    bpplut["yvyu422"] = [3, 16]
    bpplut["vda"] = [0, 0]
    bpplut["ya16be"] = [2, 32]
    bpplut["ya16le"] = [2, 32]
    bpplut["qsv"] = [0, 0]
    bpplut["mmal"] = [0, 0]
    bpplut["d3d11va_vld"] = [0, 0]
    bpplut["rgba64be"] = [4, 64]
    bpplut["rgba64le"] = [4, 64]
    bpplut["bgra64be"] = [4, 64]
    bpplut["bgra64le"] = [4, 64]
    bpplut["0rgb"] = [3, 24]
    bpplut["rgb0"] = [3, 24]
    bpplut["0bgr"] = [3, 24]
    bpplut["bgr0"] = [3, 24]
    bpplut["yuva444p"] = [4, 32]
    bpplut["yuva422p"] = [4, 24]
    bpplut["yuv420p12be"] = [3, 18]
    bpplut["yuv420p12le"] = [3, 18]
    bpplut["yuv420p14be"] = [3, 21]
    bpplut["yuv420p14le"] = [3, 21]
    bpplut["yuv422p12be"] = [3, 24]
    bpplut["yuv422p12le"] = [3, 24]
    bpplut["yuv422p14be"] = [3, 28]
    bpplut["yuv422p14le"] = [3, 28]
    bpplut["yuv444p12be"] = [3, 36]
    bpplut["yuv444p12le"] = [3, 36]
    bpplut["yuv444p14be"] = [3, 42]
    bpplut["yuv444p14le"] = [3, 42]
    bpplut["gbrp12be"] = [3, 36]
    bpplut["gbrp12le"] = [3, 36]
    bpplut["gbrp14be"] = [3, 42]
    bpplut["gbrp14le"] = [3, 42]
    bpplut["gbrap"] = [4, 32]
    bpplut["gbrap16be"] = [4, 64]
    bpplut["gbrap16le"] = [4, 64]
    bpplut["yuvj411p"] = [3, 12]
    bpplut["bayer_bggr8"] = [3, 8]
    bpplut["bayer_rggb8"] = [3, 8]
    bpplut["bayer_gbrg8"] = [3, 8]
    bpplut["bayer_grbg8"] = [3, 8]
    bpplut["bayer_bggr16le"] = [3, 16]
    bpplut["bayer_bggr16be"] = [3, 16]
    bpplut["bayer_rggb16le"] = [3, 16]
    bpplut["bayer_rggb16be"] = [3, 16]
    bpplut["bayer_gbrg16le"] = [3, 16]
    bpplut["bayer_gbrg16be"] = [3, 16]
    bpplut["bayer_grbg16le"] = [3, 16]
    bpplut["bayer_grbg16be"] = [3, 16]
    bpplut["yuv440p10le"] = [3, 20]
    bpplut["yuv440p10be"] = [3, 20]
    bpplut["yuv440p12le"] = [3, 24]
    bpplut["yuv440p12be"] = [3, 24]
    bpplut["ayuv64le"] = [4, 64]
    bpplut["ayuv64be"] = [4, 64]
    bpplut["videotoolbox_vld"] = [0, 0]

    def __init__(self, filename, inputdict={}, outputdict={}, verbosity=0):
        """Initializes FFmpeg in reading mode with the given parameters

        During initialization, additional parameters about the video file
        are parsed using :func:`skvideo.io.ffprobe`. Then FFmpeg is launched
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
        israw = 0

        # check for filters in the inputdict
        # if 
        # self.parsefilters

        # General information
        _, self.extension = os.path.splitext(filename)
        self.size = os.path.getsize(filename)
        self.probeInfo = ffprobe(filename)

        viddict = {}
        if "video" in self.probeInfo:
            viddict = self.probeInfo["video"]

        self.inputfps = -1
        if ("-r" in inputdict):
            self.inputfps = np.int(inputdict["-r"])
        elif "@r_frame_rate" in viddict:
            # check for the slash
            frtxt = viddict["@r_frame_rate"]
            parts = frtxt.split('/') 
            if len(parts) > 1:
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
        elif (("@width" in viddict) and ("@height" in viddict)):
            self.inputwidth = np.int(viddict["@width"])
            self.inputheight = np.int(viddict["@height"])
        else:
            raise ValueError("No way to determine width or height from video. Need `-s` in `inputdict`. Consult documentation on I/O.")

        self.bpp = -1 # bits per pixel
        self.pix_fmt = ""
        # completely unsure of this:
        if ("-pix_fmt" in inputdict):
            self.pix_fmt = inputdict["-pix_fmt"]
        elif ("@pix_fmt" in viddict):
            # parse this bpp
            self.pix_fmt = viddict["@pix_fmt"]
        else:
            self.pix_fmt = "yuv420p"
            warnings.warn("No input color space detected. Assuming yuv420.", UserWarning)

        self.inputdepth = np.int(self.bpplut[self.pix_fmt][0])
        self.bpp = np.int(self.bpplut[self.pix_fmt][1])

        if ("-vframes" in inputdict):
            self.inputframenum = np.int(inputdict["-vframes"])
        elif ("@nb_frames" in viddict):
            self.inputframenum = np.int(viddict["@nb_frames"])
        elif (self.extension == "yuv"):
            israw = 1
            # we can compute it based on the input size and color space
            self.inputframenum = np.int(self.size / (self.inputwidth * self.inputheight * (bpp/8.0)))
        else:
            self.inputframenum = -1
            if verbosity != 0:
                warnings.warn("Cannot determine frame count. Scanning input file, this is slow when repeated many times. Need `-vframes` in inputdict. Consult documentation on I/O.", UserWarning) 

        if israw != 0:
            inputdict['-pix_fmt'] = self.pix_fmt

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
            self.inputframenum = np.int(check_output(probecmd))

        # Create process
        cmd = ["ffmpeg"] + iargs + ['-i', self._filename] + oargs + ['-']
        print cmd

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
