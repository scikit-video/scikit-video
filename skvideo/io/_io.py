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


def vread(fname, **plugin_args):
    """Load a video from file entirely into memory.

    Parameters
    ----------
    fname : string
        Video file name, e.g. ``bickbuckbunny.mp4``

    Returns
    -------
    vid_array : ndarray
        ndarray of dimension (T, M, N, 3), where T
        is the number of frames, M is the height, N is
        width, and C is depth.

    Other parameters
    ----------------
    plugin_args : keywords
        Passed to the given plugin.

    """
    global defaultplugin

    if "plugin" in plugin_args:
        defaultplugin = plugin_args["plugin"]

    if defaultplugin == "ffmpeg":
        width = -1
        if "width" in plugin_args:
            width = np.int(plugin_args["width"])

        height = -1
        if "height" in plugin_args:
            height = np.int(plugin_args["height"])

        inputdict = {}
        if ((height != -1) and (width != -1)):
            inputdict['-s'] = str(width) + 'x' + str(height)

        reader = FFmpegReader(fname, inputdict=inputdict)
        T, M, N, C = reader.getShape()

        videodata = np.zeros((T, M, N, C), dtype=np.uint8)
        for idx, frame in enumerate(reader.nextFrame()):
            videodata[idx, :, :, :] = frame 
        return videodata

    else:
        raise NotImplemented

def vreader(fname, **plugin_args):
    """Load a video through the use of a generator. 

    Parameters
    ----------
    fname : string

        Video file name, e.g. ``bickbuckbunny.mp4``.

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

    if "plugin" in plugin_args:
        defaultplugin = plugin_args["plugin"]

    if defaultplugin == "ffmpeg":
        width = 0
        if "width" in plugin_args:
            width = plugin_args["width"]

        height = 0
        if "height" in plugin_args:
            height = plugin_args["height"]

        reader = FFmpegReader(fname)
        for frame in reader.nextFrame():
            yield frame

    else:
        raise NotImplemented
