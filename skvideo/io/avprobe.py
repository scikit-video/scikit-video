import warnings

from ..utils import *
import skvideo  # accessed via attributes so setLibAVPath() updates are seen
from .. import _AVPROBE_APPLICATION
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
    if not skvideo._HAS_AVCONV:
        raise RuntimeError("Cannot find installation of avprobe.")
    if int(skvideo._LIBAV_MAJOR_VERSION) < 10:
        raise RuntimeError("Version of libav (" + str(skvideo._LIBAV_MAJOR_VERSION) + ") is too old (need >= 10). Please update libav or use ffmpeg.")

    try:
        command = [skvideo._AVCONV_PATH + "/" + _AVPROBE_APPLICATION, "-v", "error", "-show_streams", "-of", "json", filename]

        # simply get std output
        jsonstr = check_output(command)
        probedict = json.loads(jsonstr.decode())

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
    except Exception as exc:
        warnings.warn(
            "avprobe could not parse %r (%s); returning empty metadata. "
            "Expected for raw video (supply stream parameters via inputdict); "
            "for a normal media file this usually means it is unreadable or "
            "not a recognized format." % (filename, exc),
            UserWarning,
        )
        return {}
