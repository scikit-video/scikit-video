import numpy as np
import subprocess
import os

def _videoreader():
    pass

def _videowriter():
    pass

class vopen:
    def __init__():
        pass


def vsave(fname, data, **plugin_args):
    """Save a video to file entirely from memory.

    Parameters
    ----------
    fname : string
        Video file name.

    data : ndarray
        Numpy data of dimension (T, M, N, C), where T
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
    data = np.array(data)
    # check that the appropriate data size was passed
    if len(data.shape) != 4:
        raise ValueError, "Passed data does not have 4 dimensions"

    T, M, N, C = data.shape
    height = M
    width = N
    fps = 30
    fourcc = "XVID"
    if "fps" in plugin_args:
        fps = plugin_args["fps"]
    if "fourcc" in plugin_args:
        fourcc = plugin_args["XVID"]

    wr = vopen(fname, fourcc, fps, frameSize=(width, height))
    for t in xrange(T):
        wr.write(data[t, :, :, :])
    wr.close()


def vread(fname, **plugin_args):
    """Load a video from file entirely into memory.

    Parameters
    ----------
    fname : string
        Video file name, e.g. ``bickbuckbunny.mp4`` or URL.

    Returns
    -------
    vid_array : ndarray
        A TxMxNx3 matrix representing the entire video.

    Other parameters
    ----------------
    plugin_args : keywords
        Passed to the given plugin.

    """
    rd = 0
    if "width" in plugin_args and "height" in plugin_args:
        rd = _videoreader(fname, width=plugin_args["width"], height=plugin_arg["height"])
    else:
        rd = _videoreader(fname)

    # allocate video memory if possible
    videodata = np.zeros((rd.src_numframes, rd.src_height, rd.src_width, rd.depth), dtype=np.uint8)
    # check on the video data
    rd.open()
    for i in xrange(rd.src_numframes):
        retval, image1 = rd.read()
        assert retval
        videodata[i, :, :, :] = image1
    rd.close()
    return videodata

def vread_generator(fname, **plugin_args):
    """Load a video through the use of a generator. 

    Parameters
    ----------
    fname : string
        Video file name, e.g. ``bickbuckbunny.mp4`` or URL.

    Returns
    -------
    vid_gen: generator
        returns image frames

    Other parameters
    ----------------
    plugin_args : keywords
        Passed to the given plugin.

    """
    rd = 0
    if "width" in plugin_args and "height" in plugin_args:
        rd = _videoreader(fname, width=plugin_args["width"], height=plugin_arg["height"])
    else:
        rd = _videoreader(fname)

    # check on the video data
    rd.open()
    for i in xrange(rd.src_numframes):
        retval, image1 = rd.read()
        assert retval
        yield image1
    rd.close()
