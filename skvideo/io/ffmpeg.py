""" Plugin that uses ffmpeg to read and write series of images to
a wide range of video formats.

"""

# Heavily inspired from Almar Klein's imageio code
# Copyright (c) 2015, imageio contributors
# distributed under the terms of the BSD License (included in release).

import subprocess as sp

import numpy as np

from .abstract import VideoReaderAbstract, VideoWriterAbstract
from .ffprobe import ffprobe
from .. import _FFMPEG_APPLICATION
from .. import _FFMPEG_PATH
from .. import _FFMPEG_SUPPORTED_DECODERS
from .. import _FFMPEG_SUPPORTED_ENCODERS
from .. import _HAS_FFMPEG
from ..utils import *


# uses FFmpeg to read the given file with parameters
class FFmpegReader(VideoReaderAbstract):
    """Reads frames using FFmpeg

    Using FFmpeg as a backend, this class
    provides sane initializations meant to
    handle the default case well.

    """

    INFO_AVERAGE_FRAMERATE = "@r_frame_rate"
    INFO_WIDTH = "@width"
    INFO_HEIGHT = "@height"
    INFO_PIX_FMT = "@pix_fmt"
    INFO_DURATION = "@duration"
    INFO_NB_FRAMES = "@nb_frames"
    OUTPUT_METHOD = "image2pipe"

    def __init__(self, *args, **kwargs):
        assert _HAS_FFMPEG, "Cannot find installation of real FFmpeg (which comes with ffprobe)."
        super(FFmpegReader,self).__init__(*args, **kwargs)

    def _createProcess(self, inputdict, outputdict, verbosity):
        if '-vcodec' not in outputdict:
            outputdict['-vcodec'] = "rawvideo"

        iargs = self._dict2Args(inputdict)
        oargs = self._dict2Args(outputdict)

        if verbosity > 0:
            cmd = [_FFMPEG_PATH + "/" + _FFMPEG_APPLICATION] + iargs + ['-i', self._filename] + oargs + ['-']
            print(cmd)
            self._proc = sp.Popen(cmd, stdin=sp.PIPE,
                                  stdout=sp.PIPE, stderr=None)
        else:
            cmd = [_FFMPEG_PATH + "/" + _FFMPEG_APPLICATION, "-nostats", "-loglevel", "0"] + iargs + ['-i',
                                                                                                      self._filename] + oargs + [
                      '-']
        self._proc = sp.Popen(cmd, stdin=sp.PIPE,
                              stdout=sp.PIPE, stderr=sp.PIPE)
        self._cmd = " ".join(cmd)

    def _probCountFrames(self):
        # open process, grabbing number of frames using ffprobe
        probecmd = [_FFMPEG_PATH + "/ffprobe"] + ["-v", "error", "-count_frames", "-select_streams", "v:0",
                                                  "-show_entries", "stream=nb_read_frames", "-of",
                                                  "default=nokey=1:noprint_wrappers=1", self._filename]
        return np.int(check_output(probecmd).decode().split('\n')[0])

    def _probe(self):
        return ffprobe(self._filename)

    def _getSupportedDecoders(self):
        return _FFMPEG_SUPPORTED_DECODERS

class FFmpegWriter(VideoWriterAbstract):
    """Writes frames using FFmpeg

    Using FFmpeg as a backend, this class
    provides sane initializations for the default case.
    """

    def __init__(self, *args, **kwargs):
        assert _HAS_FFMPEG, "Cannot find installation of real FFmpeg (which comes with ffprobe)."
        super(FFmpegWriter,self).__init__(*args, **kwargs)

    def _getSupportedEncoders(self):
        return _FFMPEG_SUPPORTED_ENCODERS

    def _createProcess(self, inputdict, outputdict, verbosity):
        iargs = self._dict2Args(inputdict)
        oargs = self._dict2Args(outputdict)

        cmd = [_FFMPEG_PATH + "/" + _FFMPEG_APPLICATION, "-y"] + iargs + ["-i", "-"] + oargs + [self._filename]

        self._cmd = " ".join(cmd)

        # Launch process
        if self.verbosity > 0:
            print(self._cmd)
            self._proc = sp.Popen(cmd, stdin=sp.PIPE,
                                  stdout=sp.PIPE, stderr=None)
        else:
            self._proc = sp.Popen(cmd, stdin=sp.PIPE,
                                  stdout=self.DEVNULL, stderr=sp.STDOUT)

