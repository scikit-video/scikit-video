import subprocess as sp

from ..utils import *
from .. import _HAS_AVCONV
import json

def avprobe(filename):
    """get metadata by using avprobe

    Checks the output of avprobe on the desired video
    file. MetaData is then parsed into a dictionary.

    Parameters
    ----------
    filename : string
        Path to the video file

    Returns
    -------
    metaDict : dict
       Dictionary containing all header-based information 
       about the passed-in source video.

    """
    # check if FFMPEG exists in the path
    assert _HAS_AVCONV, "Cannot find installation of avprobe."

    command = ["avprobe", "-v", "error", "-show_streams", "-of", "json", filename]

    # simply get std output
    jsonstr = check_output(command)
    probedict = json.loads(jsonstr)

    d = probedict["streams"]

    # check type
    streamsbytype = {}
    if type(d) is list:
        # go through streams
        for stream in d:
            streamsbytype[stream["codec_type"].lower()] = stream
    else:
        streamsbytype[d["codec_type"].lower()] = d

    return streamsbytype
