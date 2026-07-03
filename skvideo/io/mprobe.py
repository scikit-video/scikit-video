import subprocess as sp
import warnings

from ..utils import *
from .. import _HAS_MEDIAINFO
from .. import _MEDIAINFO_APPLICATION


def mprobe(filename):
    """get metadata by using mediainfo

    Checks the output of mediainfo on the desired video
    file. Data is then parsed into a dictionary and
    checked for video data. If no such video data exists,
    an empty dictionary is returned.

    Parameters
    ----------
    filename : string
        Path to the video file

    Returns
    -------
    mediaDict : dict
       Dictionary containing all header-based information 
       about the passed-in source video.

    """
    warnings.warn(
        "mprobe/mediainfo support is deprecated and will be removed in a "
        "future release; nothing inside scikit-video consumes it. Use "
        "skvideo.io.ffprobe instead.", DeprecationWarning, stacklevel=2)
    if not _HAS_MEDIAINFO:
        raise RuntimeError("`mediainfo` not found in path. Is it installed?")

    try:
        # '-f' gets full output, and --Output=XML is xml formatted output
        command = [_MEDIAINFO_APPLICATION, "-f", "--Output=XML", filename]

        # simply get std output
        xml = check_output(command)

        d = xmltodictparser(xml)

        if "Mediainfo" not in d:
            raise ValueError("mediainfo XML missing the 'Mediainfo' root element")
        d = d["Mediainfo"]

        if "File" not in d:
            raise ValueError("mediainfo XML missing the 'File' element")
        d = d["File"]

        if "track" not in d:
            raise ValueError("mediainfo XML missing 'track' elements")
        unorderedtracks = d["track"]

        # tracksbytype normalizes the input by key
        tracksbytype = {}
        if type(unorderedtracks) is list:
            for d in unorderedtracks:
                if "@type" not in d:
                    raise ValueError("mediainfo track missing '@type'")
                # can't have more than 1 key. If this case arises
                # an issue should be made in the tracker for a fix.
                if d["@type"] in tracksbytype:
                    raise ValueError("mediainfo returned duplicate track @type %r" % d["@type"])
                tracksbytype[d["@type"]] = d
        else: # not list
            if "@type" not in unorderedtracks:
                raise ValueError("mediainfo track missing '@type'")
            tracksbytype[unorderedtracks["@type"]] = unorderedtracks

        return tracksbytype
    except Exception as exc:
        warnings.warn(
            "mediainfo could not parse %r (%s); returning empty metadata. "
            "This usually means the file is unreadable or not a recognized "
            "media format." % (filename, exc),
            UserWarning,
        )
        return {}
