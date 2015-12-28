import numpy as np
import subprocess
import os
from ..utils import *
from .ffmpeg import FFmpegReader
from .ffmpeg import FFmpegWriter
from .. import _HAS_FFMPEG

def vwrite(fname, videodata, inputdict=None, outputdict=None, backend='ffmpeg', verbosity=0):
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
        Program to use for handling video data. Only 'ffmpeg' is supported at this time.

    verbosity : int
        Setting to 0 (default) disables all debugging output. Setting to 1 enables all debugging output. Useful to see if the backend is behaving properly. 

    Returns
    -------
    none

    """
    if not inputdict:
        inputdict = {}

    if not outputdict:
        outputdict = {}

    videodata = vshape(videodata)

    # check that the appropriate videodata size was passed
    T, M, N, C = videodata.shape

    if backend == "ffmpeg":
        # check if FFMPEG exists in the path
        assert _HAS_FFMPEG, "Cannot find installation of real FFmpeg (which comes with ffprobe)."

        writer = FFmpegWriter(fname, inputdict=inputdict, outputdict=outputdict, verbosity=verbosity)
        for t in xrange(T):
            writer.writeFrame(videodata[t])
        writer.close()
    else:
        raise NotImplemented


def vread(fname, height=0, width=0, num_frames=0, inputdict=None, outputdict=None, backend='ffmpeg', verbosity=0):
    """Load a video from file entirely into memory.

    Parameters
    ----------
    fname : string
        Video file name, e.g. ``bickbuckbunny.mp4``

    height : int
        Set the source video height used for decoding. Useful for raw inputs when video header does not exist.

    width : int
        Set the source video width used for decoding. Useful for raw inputs when video header does not exist.

    num_frames : int
        Only read the first the first `num_frames` number of frames from video. Setting `num_frames` to 
        small numbers can significantly speed up video loading times.

    inputdict : dict
        Input dictionary parameters, i.e. how to interpret the input file.

    outputdict : dict
        Output dictionary parameters, i.e. how to encode the data 
        when sending back to the python process.

    backend : string
        Program to use for handling video data. Only 'ffmpeg' is supported at this time.

    verbosity : int
        Setting to 0 (default) disables all debugging output. Setting to 1 enables all debugging output. Useful to see if the backend is behaving properly. 

    Returns
    -------
    vid_array : ndarray
        ndarray of dimension (T, M, N, 3), where T
        is the number of frames, M is the height, N is
        width, and C is depth.

    """
    if not inputdict:
        inputdict = {}

    if not outputdict:
        outputdict = {}

    if backend == "ffmpeg":
        # check if FFMPEG exists in the path
        assert _HAS_FFMPEG, "Cannot find installation of real FFmpeg (which comes with ffprobe)."

        if ((height != 0) and (width != 0)):
            inputdict['-s'] = str(width) + 'x' + str(height)

        if num_frames != 0:
            outputdict['-vframes'] = str(num_frames)

        reader = FFmpegReader(fname, inputdict=inputdict, outputdict=outputdict, verbosity=verbosity)
        T, M, N, C = reader.getShape()

        videodata = np.zeros((T, M, N, C), dtype=np.uint8)
        for idx, frame in enumerate(reader.nextFrame()):
            videodata[idx, :, :, :] = frame 
        return videodata

    else:
        raise NotImplemented

def vreader(fname, height=0, width=0, num_frames=0, inputdict=None, outputdict=None, backend='ffmpeg', verbosity=0):
    """Load a video through the use of a generator. 

    Parameters
    ----------
    fname : string
        Video file name, e.g. ``bickbuckbunny.mp4``

    height : int
        Set the source video height used for decoding. Useful for raw inputs when video header does not exist.

    width : int
        Set the source video width used for decoding. Useful for raw inputs when video header does not exist.

    num_frames : int
        Only read the first the first `num_frames` number of frames from video. Setting `num_frames` to 
        small numbers can significantly speed up video loading times.

    inputdict : dict
        Input dictionary parameters, i.e. how to interpret the input file.

    outputdict : dict
        Output dictionary parameters, i.e. how to encode the data 
        when sending back to the python process.

    backend : string
        Program to use for handling video data. Only 'ffmpeg' is supported at this time.

    verbosity : int
        Setting to 0 (default) disables all debugging output. Setting to 1 enables all debugging output. Useful to see if the backend is behaving properly. 


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
    if not inputdict:
        inputdict = {}

    if not outputdict:
        outputdict = {}

    if backend == "ffmpeg":
        # check if FFMPEG exists in the path
        assert _HAS_FFMPEG, "Cannot find installation of real FFmpeg (which comes with ffprobe)."

        if ((height != 0) and (width != 0)):
            inputdict['-s'] = str(width) + 'x' + str(height)

        if num_frames != 0:
            outputdict['-vframes'] = str(num_frames)

        reader = FFmpegReader(fname, inputdict=inputdict, outputdict=outputdict, verbosity=verbosity)
        for frame in reader.nextFrame():
            yield frame

    else:
        raise NotImplemented
