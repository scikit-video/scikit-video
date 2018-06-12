""" Plugin that uses Libav to read and write series of images to
a wide range of video formats.

"""

# Heavily inspired from Almar Klein's imageio code
# Copyright (c) 2015, imageio contributors
# distributed under the terms of the BSD License (included in release).

import subprocess as sp

import numpy as np

from .abstract import VideoReaderAbstract, VideoWriterAbstract
from .avprobe import avprobe
from .. import _AVCONV_APPLICATION
from .. import _AVCONV_PATH
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

    def _createProcess(self, inputdict, outputdict, verbosity):
        iargs = self._dict2Args(inputdict)
        oargs = self._dict2Args(outputdict)

        if verbosity == 0:
            cmd = [_AVCONV_PATH + "/" + _AVCONV_APPLICATION, "-nostats", "-loglevel", "0"] + iargs + ['-i',
                                                                                                      self._filename] + oargs + [
                      '-']
            self._proc = sp.Popen(cmd, stdin=sp.PIPE,
                                  stdout=sp.PIPE, stderr=sp.PIPE)
        else:
            cmd = [_AVCONV_PATH + "/" + _AVCONV_APPLICATION] + iargs + ['-i', self._filename] + oargs + ['-']
            print(cmd)
            self._proc = sp.Popen(cmd, stdin=sp.PIPE,
                                  stdout=sp.PIPE, stderr=None)

    def _probCountFrames(self):
        # open process, grabbing number of frames using ffprobe
        probecmd = [_AVCONV_PATH + "/avprobe"] + ["-v", "error", "-count_frames", "-select_streams", "v:0",
                                                  "-show_entries", "stream=nb_read_frames", "-of",
                                                  "default=nokey=1:noprint_wrappers=1", self._filename]
        return np.int(check_output(probecmd).decode().split('\n')[0])

    def _probe(self):
        return avprobe(self._filename)


class LibAVWriter(VideoWriterAbstract):
    """Writes frames using libav

    Using libav as a backend, this class
    provides sane initializations for the default case.
    """

    NEED_RGB2GRAY_HACK = True

    def _createProcess(self, inputdict, outputdict, verbosity):
        iargs = self._dict2Args(inputdict)
        oargs = self._dict2Args(outputdict)

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
