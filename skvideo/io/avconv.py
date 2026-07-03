""" Plugin that uses Libav to read and write series of images to
a wide range of video formats.

"""

# Heavily inspired from Almar Klein's imageio code
# Copyright (c) 2015, imageio contributors
# distributed under the terms of the BSD License (included in release).

import subprocess as sp
import warnings

import numpy as np

from .abstract import VideoReaderAbstract, VideoWriterAbstract
from .avprobe import avprobe
from .. import _AVCONV_APPLICATION
import skvideo  # accessed via attributes so setLibAVPath() updates are seen
from ..utils import *


# uses libav to read the given file with parameters
class LibAVReader(VideoReaderAbstract):
    """Reads frames using Libav
        Using libav as a backend, this class
        provides sane initializations meant to
        handle the default case well.
        """

    INFO_AVERAGE_FRAMERATE = "avg_frame_rate"
    INFO_WIDTH = "width"
    INFO_HEIGHT = "height"
    INFO_PIX_FMT = "pix_fmt"
    INFO_DURATION = "duration"
    INFO_NB_FRAMES = "nb_frames"
    OUTPUT_METHOD = "rawvideo"

    def __init__(self, *args, **kwargs):
        warnings.warn(
            "The libav/avconv backend is deprecated and will be removed in "
            "a future release (libav is unmaintained upstream and this "
            "backend is not covered by scikit-video's CI). Use the ffmpeg "
            "backend instead.", DeprecationWarning, stacklevel=2)
        if not skvideo._HAS_AVCONV:
            raise RuntimeError("Cannot find installation of libav (which comes with avprobe).")
        super(LibAVReader,self).__init__(*args, **kwargs)

    def _createProcess(self, inputdict, outputdict, verbosity):
        iargs = self._dict2Args(inputdict)
        oargs = self._dict2Args(outputdict)

        if verbosity == 0:
            cmd = [skvideo._AVCONV_PATH + "/" + _AVCONV_APPLICATION, "-nostats", "-loglevel", "0"] + iargs + ['-i',
                                                                                                      self._filename] + oargs + [
                      '-']
            self._proc = sp.Popen(cmd, stdin=sp.PIPE,
                                  stdout=sp.PIPE, stderr=sp.PIPE)
        else:
            cmd = [skvideo._AVCONV_PATH + "/" + _AVCONV_APPLICATION] + iargs + ['-i', self._filename] + oargs + ['-']
            print(cmd)
            self._proc = sp.Popen(cmd, stdin=sp.PIPE,
                                  stdout=sp.PIPE, stderr=None)

    def _probCountFrames(self):
        # open process, grabbing number of frames using avprobe
        probecmd = [skvideo._AVCONV_PATH + "/avprobe"] + ["-v", "error", "-count_frames", "-select_streams", "v:0",
                                                  "-show_entries", "stream=nb_read_frames", "-of",
                                                  "default=nokey=1:noprint_wrappers=1", self._filename]
        try:
            output = check_output(probecmd).decode().split('\n')[0]
        except sp.CalledProcessError:
            raise RuntimeError(
                "Could not count the frames of %r: avprobe could not read it. "
                "The input is most likely empty, truncated, or not a video "
                "that libav can decode. For raw video pass -s and -pix_fmt "
                "(and ideally -vframes) in inputdict." % self._filename
            )
        try:
            return int(output)
        except ValueError:
            raise RuntimeError(
                "Could not count the frames of %r: avprobe returned no frame "
                "count (%r). Pass -vframes in inputdict to declare the frame "
                "count explicitly." % (self._filename, output)
            )

    def _probe(self):
        return avprobe(self._filename)


class LibAVWriter(VideoWriterAbstract):
    """Writes frames using libav

    Using libav as a backend, this class
    provides sane initializations for the default case.
    """

    def __init__(self, *args, **kwargs):
        warnings.warn(
            "The libav/avconv backend is deprecated and will be removed in "
            "a future release (libav is unmaintained upstream and this "
            "backend is not covered by scikit-video's CI). Use the ffmpeg "
            "backend instead.", DeprecationWarning, stacklevel=2)
        if not skvideo._HAS_AVCONV:
            raise RuntimeError("Cannot find installation of libav (which comes with avprobe).")
        super(LibAVWriter,self).__init__(*args, **kwargs)

    def _createProcess(self, inputdict, outputdict, verbosity):
        iargs = self._dict2Args(inputdict)
        oargs = self._dict2Args(outputdict)

        cmd = [skvideo._AVCONV_PATH + "/avconv", "-y"] + iargs + ["-i", "pipe:"] + oargs + [self._filename]

        self._cmd = " ".join(cmd)

        # Launch process
        if self.verbosity == 0:
            self._proc = sp.Popen(cmd, stdin=sp.PIPE,
                                  stdout=sp.PIPE, stderr=sp.PIPE)
        else:
            print(cmd)
            self._proc = sp.Popen(cmd, stdin=sp.PIPE,
                                  stdout=sp.PIPE, stderr=None)

    def _gray2RGB(self,data):
        # convert grayscale vid to 3 channel
        T,M,N,C = data.shape
        if C < 3: # should always be True
            vid = np.empty((T, M, N, C+2), dtype=data.dtype)
            vid[:, :, :, 0] = data[:, :, :, 0]
            vid[:, :, :, 1] = data[:, :, :, 0]
            vid[:, :, :, 2] = data[:, :, :, 0]
            if C==2:
                vid[:, :, :, 3] = data[:, :, :, 1]
            return vid
        return data

    def _warmStart(self, M, N, C, dtype):
        if (C==2 or C==4) and dtype.itemsize==2 and (('-pix_fmt' not in self.inputdict) or (self.inputdict['-pix_fmt'][0:6]=='rgba64')):
            raise ValueError('libAV doesnt support rgba64 formats')
        if C < 3 and "-pix_fmt" not in self.inputdict: # pix_fmt gray, ya8 and their 16 bit equivalents have a bug in LibAV
            C += 2
            self._prepareData = self._gray2RGB #replace prepareData methode by the gray2RGB hack method
        super(LibAVWriter,self)._warmStart(M, N, C, dtype)
