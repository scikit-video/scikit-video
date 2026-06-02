""" Plugin that uses ffmpeg to read and write series of images to
a wide range of video formats.

"""

# Heavily inspired from Almar Klein's imageio code
# Copyright (c) 2015, imageio contributors
# distributed under the terms of the BSD License (included in release).

import os
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
            stderr = None
        else:
            cmd = [_FFMPEG_PATH + "/" + _FFMPEG_APPLICATION, "-nostats", "-loglevel", "0"] + iargs + ['-i',
                                                                                                      self._filename] + oargs + [
                      '-']
            stderr = sp.PIPE
        self._proc = sp.Popen(cmd, stdin=sp.PIPE,
                              stdout=sp.PIPE, stderr=stderr)
        self._cmd = " ".join(cmd)

    def _probCountFrames(self):
        # open process, grabbing number of frames using ffprobe
        probecmd = [_FFMPEG_PATH + "/ffprobe"] + ["-v", "error", "-count_frames", "-select_streams", "v:0",
                                                  "-show_entries", "stream=nb_read_frames", "-of",
                                                  "default=nokey=1:noprint_wrappers=1", self._filename]
        return int(check_output(probecmd).decode().split('\n')[0])

    def _probe(self):
        return ffprobe(self._filename)

    def _getSupportedDecoders(self):
        return _FFMPEG_SUPPORTED_DECODERS

class FFmpegWriter(VideoWriterAbstract):
    """Writes frames using FFmpeg

    Using FFmpeg as a backend, this class
    provides sane initializations for the default case.

    Parameters
    ----------
    filename : string
        Video file path for writing.

    inputdict : dict
        How to interpret the frames piped in from Python.

    outputdict : dict
        How to encode the output file.

    audiosrc : string, optional
        Path to a media file whose audio track should be muxed into the
        output. Used to preserve audio across a ``vread`` / ``vwrite``
        round-trip (issues #173, #176). By default the output contains
        the video from the piped-in frames plus the **first** audio
        stream from ``audiosrc`` (equivalent to passing
        ``-map 0:v:0 -map 1:a:0`` to ffmpeg).

        To take full control of stream selection, supply your own
        ``-map`` in ``outputdict``. When ``outputdict`` contains a
        ``-map`` entry, our default ``-map`` arguments yield entirely;
        this is in line with ffmpeg's additive ``-map`` semantics (a
        second ``-map`` adds streams rather than overriding earlier
        ones). Examples (note the list form for multiple ``-map``
        values):

          - Copy all audio streams::

                outputdict={'-map': ['0:v:0', '1:a']}

          - Pick a specific audio stream::

                outputdict={'-map': ['0:v:0', '1:a:5']}

        The audio is stream-copied with ``-c:a copy`` (no re-encoding);
        set ``-c:a`` (or ``-codec:a`` / ``-acodec``) in ``outputdict``
        to override the codec. The output is also trimmed to the shorter
        of video/audio via ``-shortest``, which is the intuitive
        behavior when the video is a subset of the original.

    verbosity : int
        0 (default) for quiet, 1 to print the ffmpeg command.

    Notes
    -----
    The FFmpeg subprocess is launched lazily on the first ``writeFrame``
    call. Constructing a writer and calling ``close()`` without writing any
    frames is a no-op and produces no output file — this keeps cleanup in a
    ``finally`` (or a construct-only validation) from raising. Use the
    high-level ``skvideo.io.vwrite``, which rejects empty (0-frame) input
    with ``ValueError``, if you want that guarded.
    """

    def __init__(self, filename, inputdict=None, outputdict=None,
                 audiosrc=None, verbosity=0):
        assert _HAS_FFMPEG, "Cannot find installation of real FFmpeg (which comes with ffprobe)."
        if audiosrc is not None:
            # Fail fast at construction time rather than letting ffmpeg
            # produce a silent videoless output that the user discovers
            # later. Both the missing-file and no-audio-stream cases would
            # otherwise be invisible.
            if not os.path.isfile(audiosrc):
                raise FileNotFoundError(
                    "audiosrc not found: %r" % audiosrc
                )
            probe = ffprobe(audiosrc)
            if not probe.get("audio_streams"):
                raise ValueError(
                    "audiosrc %r contains no audio stream; cannot mux audio "
                    "from a file without audio. Remove the audiosrc argument "
                    "to write a video-only output." % audiosrc
                )
            # Resolve to an absolute path now. FFmpegWriter's subprocess is
            # launched lazily on the first writeFrame() call; if the user's
            # cwd changes between construction and first write, a relative
            # path would silently resolve against the wrong directory.
            audiosrc = os.path.abspath(audiosrc)
        self._audiosrc = audiosrc
        super(FFmpegWriter, self).__init__(
            filename, inputdict=inputdict, outputdict=outputdict, verbosity=verbosity)

    def _getSupportedEncoders(self):
        return _FFMPEG_SUPPORTED_ENCODERS

    def _createProcess(self, inputdict, outputdict, verbosity):
        iargs = self._dict2Args(inputdict)
        oargs = self._dict2Args(outputdict)

        cmd = [_FFMPEG_PATH + "/" + _FFMPEG_APPLICATION, "-y"] + iargs + ["-i", "-"]

        if self._audiosrc is not None:
            # Mux audio from a separate source. stdin (raw video) is input #0;
            # the audio source becomes input #1.
            cmd += ["-i", self._audiosrc]
            # ffmpeg's -map is ADDITIVE: a second -map adds streams rather than
            # overriding earlier ones. So if the user supplies any -map in
            # outputdict, our defaults must yield entirely — otherwise the user
            # gets unexpected duplicated streams. Default behavior (no user
            # -map): copy video from input 0 and the first audio stream from
            # input 1; we pick :0 over :a to avoid surprise-multiplexing all
            # audio tracks from a multi-language source.
            if "-map" not in outputdict:
                cmd += ["-map", "0:v:0", "-map", "1:a:0"]
            # Only set the default codec/duration policy if the user hasn't
            # already specified their own audio codec.
            user_audio_codec_keys = ("-c:a", "-codec:a", "-acodec")
            if not any(k in outputdict for k in user_audio_codec_keys):
                cmd += ["-c:a", "copy"]
            if "-shortest" not in outputdict:
                cmd += ["-shortest"]

        cmd += oargs + [self._filename]

        self._cmd = " ".join(cmd)

        # Launch process. stderr=PIPE in non-verbose mode so close() and the
        # writeFrame IOError handler can surface FFmpeg's actual error output
        # (issue #111). verbosity>0 leaves stderr unredirected so the user
        # sees FFmpeg's output live and we have no captured stream to read.
        # For memory destinations, stdout MUST be a PIPE (regardless of
        # verbosity) because ffmpeg writes the encoded bytes there and a
        # background thread drains them into the user's buffer (issue #113
        # write-side). Without draining, ffmpeg blocks once stdout's
        # ~64KB pipe buffer fills.
        if self._dest_kind == "memory":
            self._proc = sp.Popen(cmd, stdin=sp.PIPE,
                                  stdout=sp.PIPE, stderr=sp.PIPE)
            self._start_stdout_drain_thread()
        elif self.verbosity > 0:
            print(self._cmd)
            self._proc = sp.Popen(cmd, stdin=sp.PIPE,
                                  stdout=sp.PIPE, stderr=None)
        else:
            self._proc = sp.Popen(cmd, stdin=sp.PIPE,
                                  stdout=self.DEVNULL, stderr=sp.PIPE)

