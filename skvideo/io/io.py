import numpy as np
import subprocess
import os
from .ffmpeg import FFmpegReader
from .ffmpeg import FFmpegWriter

defaultplugin = "ffmpeg"

def vwrite(fname, data, **plugin_args):
    """Save a video to file entirely from memory.

    Parameters
    ----------
    fname : string
        Video file name.

    data : ndarray
        ndarray of dimension (T, M, N, C), where T
        is the number of frames, M is the height, N is
        width, and C is depth.

    Returns
    -------
    none

    Other parameters
    ----------------
    plugin_args : keywords
        Passed to the given plugin.

    """
    global defaultplugin

    data = np.array(data)
    # check that the appropriate data size was passed
    if len(data.shape) == 4:
        T, M, N, C = data.shape
        fps = 30

        if "plugin" in plugin_args:
            defaultplugin = plugin_args["plugin"]

        if "fps" in plugin_args:
            fps = plugin_args["fps"]

        if defaultplugin == "ffmpeg":
            writer = FFmpegWriter(fname, (T, M, N, C))
            for t in xrange(T):
                writer.writeFrame(data[t, :, :, :])
            writer.close()
        else:
            raise NotImplemented
    elif len(data.shape) == 3:
        T, M, N = data.shape
        fps = 30

        if "plugin" in plugin_args:
            defaultplugin = plugin_args["plugin"]

        if "fps" in plugin_args:
            fps = plugin_args["fps"]

        if defaultplugin == "ffmpeg":
            writer = FFmpegWriter(fname, (T, M, N), pix_fmt='gray')
            for t in xrange(T):
                writer.writeFrame(data[t, :, :])
            writer.close()
        else:
            raise NotImplemented
    else:
        raise ValueError, "Passed data does not have sensible dimensions..."


def vread(fname, height=0, width=0, num_frames=0, inputdict={}, outputdict={}, backend='ffmpeg'):
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

    Returns
    -------
    vid_array : ndarray
        ndarray of dimension (T, M, N, 3), where T
        is the number of frames, M is the height, N is
        width, and C is depth.

    """
    global defaultplugin

    if backend == "ffmpeg":
        if ((height != 0) and (width != 0)):
            inputdict['-s'] = str(width) + 'x' + str(height)

        if num_frames != 0:
            outputdict['-vframes'] = str(num_frames)

        reader = FFmpegReader(fname, inputdict=inputdict, outputdict=outputdict)
        T, M, N, C = reader.getShape()

        videodata = np.zeros((T, M, N, C), dtype=np.uint8)
        for idx, frame in enumerate(reader.nextFrame()):
            videodata[idx, :, :, :] = frame 
        return videodata

    else:
        raise NotImplemented

def vreader(fname, height=0, width=0, num_frames=0, inputdict={}, outputdict={}, backend='ffmpeg'):
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
    global defaultplugin

    if backend == "ffmpeg":
        if ((height != 0) and (width != 0)):
            inputdict['-s'] = str(width) + 'x' + str(height)

        if num_frames != 0:
            outputdict['-vframes'] = str(num_frames)

        reader = FFmpegReader(fname, inputdict=inputdict, outputdict=outputdict)
        for frame in reader.nextFrame():
            yield frame

    else:
        raise NotImplemented
