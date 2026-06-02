import os
import subprocess as sp
import warnings

from ..utils import *
from .. import _HAS_FFMPEG
from .. import _FFMPEG_PATH
from .. import _FFPROBE_APPLICATION

def ffprobe(filename):
    """get metadata by using ffprobe

    Checks the output of ffprobe on the desired video
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

       For each codec type present in the file (e.g. ``video``, ``audio``,
       ``subtitle``), the dictionary contains two entries:

       - ``<type>`` — the first stream of that type (backward-compatible
         with the pre-#165 single-stream behavior).
       - ``<type>_streams`` — a list of *all* streams of that type, in the
         order ffprobe reported them. Use this when the file contains
         multiple streams of the same codec type (issue #165).

       Example for a file with one video stream and two audio streams::

           info = ffprobe("foo.mkv")
           info["video"]            # first (and only) video stream
           info["audio"]            # first audio stream
           info["audio_streams"]    # list of both audio streams

    """
    # check if FFMPEG exists in the path
    assert _HAS_FFMPEG, "Cannot find installation of real FFmpeg (which comes with ffprobe)."

    filename = os.fspath(filename)

    try:
        command = [_FFMPEG_PATH + "/" + _FFPROBE_APPLICATION, "-v", "error", "-show_streams", "-print_format", "xml", filename]

        xml = check_output(command)
        d = xmltodictparser(xml)["ffprobe"]["streams"]

        # ffprobe's XML output produces either a single "stream" dict or a list of them
        # depending on stream count. Normalize to a list.
        streams = d["stream"]
        if not isinstance(streams, list):
            streams = [streams]

        # Seed the well-known plural keys so callers can iterate without
        # defensive `info.get('audio_streams', [])` — empty list is the
        # documented "no streams of this type" signal (issue #165).
        result = {"audio_streams": [], "video_streams": []}
        for stream in streams:
            codec_type = stream["@codec_type"].lower()
            # First stream of each type lives at the unindexed key (backward-compat)
            if codec_type not in result:
                result[codec_type] = stream
            # All streams of each type live at the plural key (issue #165)
            result.setdefault(codec_type + "_streams", []).append(stream)

        return result
    except Exception as exc:
        # Returning {} is load-bearing: raw/headerless video (e.g. .yuv) has
        # no probeable streams and the reader falls back to inputdict's
        # -s / -pix_fmt. But silently swallowing every failure also hides a
        # genuinely unreadable/corrupt file behind a later "No way to
        # determine width or height" error. Warn with the cause so the real
        # reason is visible, then preserve the {} fallback.
        warnings.warn(
            "ffprobe could not parse %r (%s); returning empty metadata. "
            "Expected for raw video (supply -s and -pix_fmt via inputdict); "
            "for a normal media file this usually means it is unreadable or "
            "not a recognized format." % (filename, exc),
            UserWarning,
        )
        return {}
