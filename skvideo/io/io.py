import os

import numpy as np

from .abstract import _classify_source
from .avconv import LibAVReader
from .avconv import LibAVWriter
from .ffmpeg import FFmpegReader
from .ffmpeg import FFmpegWriter
from .. import _HAS_AVCONV
from .. import _HAS_FFMPEG
from ..utils import *


def _normalize_source(fname):
    """Path-likes go through os.fspath; file-like objects pass through unchanged.

    Callers downstream (the Reader/Writer constructors) handle the BytesIO /
    file-like case via _classify_source + spool_memory_to_tempfile, so we
    must not try to coerce these into strings here.
    """
    if _classify_source(fname) == "memory":
        return fname
    return os.fspath(fname)


def vwrite(fname, videodata, inputdict=None, outputdict=None, backend='ffmpeg', verbosity=0, audiosrc=None):
    """Save a video to file entirely from memory.

    Parameters
    ----------
    fname : string
        Video file name.

    videodata : ndarray
        ndarray of dimension (T, M, N, C), (T, M, N), (M, N, C), or (M, N),
        where T is the number of frames, M is the height, N is width,
        and C is number of channels.

    inputdict : dict
        Input dictionary parameters, i.e. how to interpret the piped datastream
        coming from python to the subprocess.

    outputdict : dict
        Output dictionary parameters, i.e. how to encode the data to
        disk.

    backend : string
        Program to use for handling video data.
        Only 'ffmpeg' and 'libav' are supported at this time.

    verbosity : int
        Setting to 0 (default) disables all debugging output.
        Setting to 1 enables all debugging output.
        Useful to see if the backend is behaving properly.

    audiosrc : string, optional
        Path to a media file whose audio track should be muxed into the
        output, allowing audio to be preserved across a ``vread`` /
        ``vwrite`` round-trip (issues #173, #176). FFmpeg backend only.

    Returns
    -------
    none

    """
    fname = _normalize_source(fname)

    if not inputdict:
        inputdict = {}

    if not outputdict:
        outputdict = {}

    videodata = vshape(videodata)

    # check that the appropriate videodata size was passed
    T, M, N, C = videodata.shape

    if T == 0:
        raise ValueError("Cannot write an empty video: videodata has 0 frames.")

    if backend == "ffmpeg":
        # check if FFMPEG exists in the path
        if not _HAS_FFMPEG:
            raise RuntimeError("Cannot find installation of real FFmpeg (which comes with ffprobe).")

        writer = FFmpegWriter(fname, inputdict=inputdict, outputdict=outputdict,
                              audiosrc=audiosrc, verbosity=verbosity)
        for t in range(T):
            writer.writeFrame(videodata[t])
        writer.close()
    elif backend == "libav":
        if audiosrc is not None:
            raise NotImplementedError("audiosrc passthrough is only supported with backend='ffmpeg'")
        # check if FFMPEG exists in the path
        if not _HAS_AVCONV:
            raise RuntimeError("Cannot find installation of libav.")
        writer = LibAVWriter(fname, inputdict=inputdict, outputdict=outputdict, verbosity=verbosity)
        for t in range(T):
            writer.writeFrame(videodata[t])
        writer.close()
    else:
        raise NotImplemented


def vread(fname, height=0, width=0, num_frames=0, as_grey=False, inputdict=None, outputdict=None, backend='ffmpeg', verbosity=0, start_frame=0):
    """Load a video from file entirely into memory.

    Parameters
    ----------
    fname : string
        Video file name, e.g. ``bickbuckbunny.mp4``

    height : int
        Set the source video height used for decoding.
        Useful for raw inputs when video header does not exist.

    width : int
        Set the source video width used for decoding.
        Useful for raw inputs when video header does not exist.

    num_frames : int
        Only read the first `num_frames` number of frames from video.
        Setting `num_frames` to small numbers can significantly
        speed up video loading times.

    as_grey : bool
        If true, only load the luminance channel of the input video.

    inputdict : dict
        Input dictionary parameters, i.e. how to interpret the input file.

    outputdict : dict
        Output dictionary parameters, i.e. how to encode the data
        when sending back to the python process.

    backend : string
        Program to use for handling video data.
        Only 'ffmpeg' and 'libav' are supported at this time.

    verbosity : int
        Setting to 0 (default) disables all debugging output.
        Setting to 1 enables all debugging output.
        Useful to see if the backend is behaving properly.

    start_frame : int
        Skip the first ``start_frame`` frames before reading (issue #166).
        Combine with ``num_frames`` for a windowed read like
        ``vread(..., start_frame=1000, num_frames=200)``. Uses FFmpeg's
        fast keyframe seek, so the actual first frame returned may snap
        to the nearest keyframe at or before the requested position.

    Returns
    -------
    vid_array : ndarray
        ndarray of dimension (T, M, N, C), where T
        is the number of frames, M is the height, N is
        width, and C is depth.

    """
    fname = _normalize_source(fname)

    if not inputdict:
        inputdict = {}

    if not outputdict:
        outputdict = {}

    if backend == "ffmpeg":
        # check if FFMPEG exists in the path
        if not _HAS_FFMPEG:
            raise RuntimeError("Cannot find installation of real FFmpeg (which comes with ffprobe).")

        if ((height != 0) and (width != 0)):
            inputdict['-s'] = str(width) + 'x' + str(height)

        if num_frames != 0:
            outputdict['-vframes'] = str(num_frames)

        if as_grey:
            outputdict['-pix_fmt'] = 'gray'

        reader = FFmpegReader(fname, inputdict=inputdict, outputdict=outputdict, verbosity=verbosity, start_frame=start_frame)
        try:
            T, M, N, C = reader.getShape()

            videodata = np.empty((T, M, N, C), dtype=reader.dtype)
            count = 0
            for idx, frame in enumerate(reader.nextFrame()):
                videodata[idx, :, :, :] = frame
                count = idx + 1
            # An output filter (e.g. -vf select) can yield fewer frames than
            # getShape() predicted from nb_frames; trim so the caller never
            # sees uninitialized np.empty rows.
            if count < T:
                videodata = videodata[:count]

            if as_grey:
                videodata = vshape(videodata[:, :, :, 0])
        finally:
            # Always close so a spooled temp file (BytesIO input) is unlinked
            # even if reading raises partway through.
            reader.close()

        return videodata
    elif backend == "libav":
        # check if FFMPEG exists in the path
        if not _HAS_AVCONV:
            raise RuntimeError("Cannot find installation of libav.")

        if ((height != 0) and (width != 0)):
            inputdict['-s'] = str(width) + 'x' + str(height)

        if num_frames != 0:
            outputdict['-vframes'] = str(num_frames)

        reader = LibAVReader(fname, inputdict=inputdict, outputdict=outputdict, verbosity=verbosity)
        try:
            T, M, N, C = reader.getShape()

            videodata = np.empty((T, M, N, C), dtype=reader.dtype)
            count = 0
            for idx, frame in enumerate(reader.nextFrame()):
                videodata[idx, :, :, :] = frame
                count = idx + 1
            if count < T:
                videodata = videodata[:count]
        finally:
            reader.close()
        return videodata

    else:
        raise NotImplemented


def vreader(fname, height=0, width=0, num_frames=0, as_grey=False, inputdict=None, outputdict=None, backend='ffmpeg', verbosity=0, start_frame=0):
    """Load a video through the use of a generator.

    Parameters
    ----------
    fname : string
        Video file name, e.g. ``bickbuckbunny.mp4``

    height : int
        Set the source video height used for decoding.
        Useful for raw inputs when video header does not exist.

    width : int
        Set the source video width used for decoding.
        Useful for raw inputs when video header does not exist.

    num_frames : int
        Only read the first `num_frames` number of frames from video.
        Setting `num_frames` to small numbers can significantly speed up video loading times.

    as_grey : bool
        If true, only load the luminance channel of the input video.

    inputdict : dict
        Input dictionary parameters, i.e. how to interpret the input file.

    outputdict : dict
        Output dictionary parameters, i.e. how to encode the data
        between backend and python.

    backend : string
        Program to use for handling video data.
        Only 'ffmpeg' and 'libav' are supported at this time.

    verbosity : int
        Setting to 0 (default) disables all debugging output.
        Setting to 1 enables all debugging output.
        Useful to see if the backend is behaving properly.

    start_frame : int
        Skip the first ``start_frame`` frames before reading (issue #166).
        Uses FFmpeg's fast keyframe seek; the first frame returned may
        snap to the nearest keyframe at or before the requested position.


    Returns
    -------
    vid_gen : generator
        returns ndarrays, shape (M, N, C) where
        M is frame height, N is frame width, and
        C is number of channels per pixel

    ----------------
    plugin_args : keywords
        Passed to the given plugin.

    """
    fname = _normalize_source(fname)

    if not inputdict:
        inputdict = {}

    if not outputdict:
        outputdict = {}

    if backend == "ffmpeg":
        # check if FFMPEG exists in the path
        if not _HAS_FFMPEG:
            raise RuntimeError("Cannot find installation of ffmpeg.")

        if ((height != 0) and (width != 0)):
            inputdict['-s'] = str(width) + 'x' + str(height)

        if num_frames != 0:
            outputdict['-vframes'] = str(num_frames)

        if as_grey:
            outputdict['-pix_fmt'] = 'gray'

        reader = FFmpegReader(fname, inputdict=inputdict, outputdict=outputdict, verbosity=verbosity, start_frame=start_frame)
        try:
            for frame in reader.nextFrame():
                if as_grey:
                    yield vshape(frame[:, :, 0])
                else:
                    yield frame
        finally:
            reader.close()

    elif backend == "libav":
        # check if FFMPEG exists in the path
        if not _HAS_AVCONV:
            raise RuntimeError("Cannot find installation of libav.")

        if ((height != 0) and (width != 0)):
            inputdict['-s'] = str(width) + 'x' + str(height)

        if num_frames != 0:
            outputdict['-vframes'] = str(num_frames)

        reader = LibAVReader(fname, inputdict=inputdict, outputdict=outputdict, verbosity=verbosity)
        try:
            for frame in reader.nextFrame():
                yield frame
        finally:
            reader.close()

    else:
        raise NotImplemented
