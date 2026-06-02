__version__ = "1.1.14.dev0"

from .utils import check_output, where
import os
import warnings
import numpy as np

# Run a program-based check to see if all install
# requirements have been met.
# Sets environment variables based on programs
# found.

def which(command):
  candidates = where(command)
  if len(candidates) > 0:
    return os.path.split(candidates[0])[0]
  else:
    return ""


# only ffprobe exists with ffmpeg
_FFMPEG_PATH = which("ffprobe")

# only avprobe exists with libav
_AVCONV_PATH = which("avprobe")

_MEDIAINFO_PATH = which("mediainfo")

_HAS_FFMPEG = 0
_HAS_AVCONV = 0
_HAS_MEDIAINFO = 0

_LIBAV_MAJOR_VERSION = "0"
_LIBAV_MINOR_VERSION = "0"
_FFMPEG_MAJOR_VERSION = "0"
_FFMPEG_MINOR_VERSION = "0"
_FFMPEG_PATCH_VERSION = "0"

_FFMPEG_SUPPORTED_DECODERS = []
_FFMPEG_SUPPORTED_ENCODERS = []
_LIBAV_SUPPORTED_EXT = []

# Lazy cache of `ffmpeg -protocols` output (issue #117, v1.1.14 protocol
# detection). Stored as a single tuple ``(input_list, output_list)`` and
# published in one assignment, so a reader that races past the cache
# check sees either None or a fully populated tuple, never a half-filled
# pair. This is not a lock: a concurrent setFFmpegPath() reset can still
# race a populate, in which case detection simply runs again; the cost
# is a redundant `ffmpeg -protocols` call, not corruption. Reset to None
# by setFFmpegPath so a different ffmpeg binary triggers fresh detection.
_FFMPEG_PROTOCOLS = None

_FFPROBE_APPLICATION = "ffprobe"
_FFMPEG_APPLICATION = "ffmpeg"
_AVPROBE_APPLICATION = "avprobe"
_AVCONV_APPLICATION = "avconv"
_MEDIAINFO_APPLICATION = "mediainfo"

# Windows compat
if os.name == "nt":
    _FFPROBE_APPLICATION += ".exe"
    _FFMPEG_APPLICATION += ".exe"
    _AVPROBE_APPLICATION += ".exe"
    _AVCONV_APPLICATION += ".exe"
    _MEDIAINFO_APPLICATION += ".exe"

def scan_ffmpeg():
    global _FFMPEG_MAJOR_VERSION
    global _FFMPEG_MINOR_VERSION
    global _FFMPEG_PATCH_VERSION
    global _FFMPEG_SUPPORTED_DECODERS
    global _FFMPEG_SUPPORTED_ENCODERS
    _FFMPEG_MAJOR_VERSION = "0"
    _FFMPEG_MINOR_VERSION = "0"
    _FFMPEG_PATCH_VERSION = "0"
    _FFMPEG_SUPPORTED_DECODERS = []
    _FFMPEG_SUPPORTED_ENCODERS = []
    try:
        # grab program version string
        version = check_output([os.path.join(_FFMPEG_PATH, _FFMPEG_APPLICATION), "-version"])
        # only parse the first line returned
        firstline = version.split(b'\n')[0]

        # the 3rd element in this line is the version number
        version = firstline.split(b' ')[2].strip()
        versionparts = version.split(b'.')
        if version[0] == b'N':
            # this is the 'git' version of FFmpeg
            _FFMPEG_MAJOR_VERSION = version
        else:
            _FFMPEG_MAJOR_VERSION = versionparts[0]
            _FFMPEG_MINOR_VERSION = versionparts[1]
            if len(versionparts) > 2:
                _FFMPEG_PATCH_VERSION = versionparts[2]
    except:
        pass

    # decoders = []
    # encoders = []

    # try:
    #     extension_lst = check_output([_FFMPEG_PATH + "/ffmpeg", "-formats"])
    #     extension_lst = extension_lst.split(b'\n')
    #     # skip first line
    #     for item in extension_lst[4:]:
    #         parts = [x.strip() for x in item.split(b' ') if x]
    #         if len(parts) < 2:
    #             continue
    #         rule = parts[0]
    #         extension = parts[1]
    #         if b'D' in rule:
    #             for item in extension.split(b","):
    #                 decoders.append(item)
    #         if b'E' in rule:
    #             for item in extension.split(b","):
    #                 encoders.append(item)
    # except:
    #     pass

    # try:
    #     for enc in encoders:
    #         extension_lst = check_output([_FFMPEG_PATH + "/ffmpeg", "-v", "1", "-h", "muxer="+str(enc)])
    #         csvstring = ""
    #         for line in extension_lst.split('\n'):
    #             if "Common extensions:" in line:
    #                 csvstring = line.replace("Common extensions:", "").replace(".", "").strip()
    #                 break
    #         if csvstring == "":
    #             continue
    #         csvlist = csvstring.split(',')
    #         for listitem in csvlist:
    #             _FFMPEG_SUPPORTED_ENCODERS.append(b"." + listitem)
    #     for enc in encoders:
    #         extension_lst = check_output([_FFMPEG_PATH + "/ffmpeg", "-v", "1", "-h", "demuxer="+str(enc)])
    #         csvstring = ""
    #         for line in extension_lst.split('\n'):
    #             if "Common extensions:" in line:
    #                 csvstring = line.replace("Common extensions:", "").replace(".", "").strip()
    #                 break
    #         if csvstring == "":
    #             continue
    #         csvlist = csvstring.split(',')
    #         for listitem in csvlist:
    #             _FFMPEG_SUPPORTED_ENCODERS.append(b"." + listitem)

    #     _FFMPEG_SUPPORTED_ENCODERS = np.unique(_FFMPEG_SUPPORTED_ENCODERS)
    # except:
    #     pass

    # try:
    #     for dec in decoders:
    #         extension_lst = check_output([_FFMPEG_PATH + "/ffmpeg", "-v", "1", "-h", "muxer="+str(dec)])
    #         csvstring = ""
    #         for line in extension_lst.split('\n'):
    #             if "Common extensions:" in line:
    #                 csvstring = line.replace("Common extensions:", "").replace(".", "").strip()
    #                 break
    #         if csvstring == "":
    #             continue
    #         csvlist = csvstring.split(',')
    #         for listitem in csvlist:
    #             _FFMPEG_SUPPORTED_DECODERS.append(b"." + listitem)
    #     for dec in decoders:
    #         extension_lst = check_output([_FFMPEG_PATH + "/ffmpeg", "-v", "1", "-h", "demuxer="+str(dec)])
    #         csvstring = ""
    #         for line in extension_lst.split('\n'):
    #             if "Common extensions:" in line:
    #                 csvstring = line.replace("Common extensions:", "").replace(".", "").strip()
    #                 break
    #         if csvstring == "":
    #             continue
    #         csvlist = csvstring.split(',')
    #         for listitem in csvlist:
    #             _FFMPEG_SUPPORTED_DECODERS.append(b"." + listitem)

    #     _FFMPEG_SUPPORTED_DECODERS = np.unique(_FFMPEG_SUPPORTED_DECODERS)
    # except:
    #     pass

    # by running the above code block, the bottom arrays are populated
    # output staticly provided for speed concerns
    _FFMPEG_SUPPORTED_DECODERS = [
        b'.264', b'.265', b'.302', b'.3g2', b'.3gp', b'.722', b'.aa', b'.aa3', b'.aac', b'.ac3',
        b'.acm', b'.adf', b'.adp', b'.ads', b'.adx', b'.aea', b'.afc', b'.aif', b'.aifc', b'.aiff',
        b'.al', b'.amr', b'.ans', b'.ape', b'.apl', b'.apng', b'.aqt', b'.art', b'.asc', b'.asf',
        b'.ass', b'.ast', b'.au', b'.avc', b'.avi', b'.avr', b'.bcstm', b'.bfstm', b'.bin', b'.bit',
        b'.bmp', b'.bmv', b'.brstm', b'.caf', b'.cavs', b'.cdata', b'.cdg', b'.cdxl', b'.cgi',
        b'.cif', b'.daud', b'.dav', b'.dif', b'.diz', b'.dnxhd', b'.dpx', b'.drc', b'.dss', b'.dtk', b'.dts',
        b'.dtshd', b'.dv', b'.eac3', b'.fap', b'.ffm', b'.ffmeta', b'.flac', b'.flm', b'.flv',
        b'.fsb', b'.g722', b'.g723_1', b'.g729', b'.genh', b'.gif', b'.gsm', b'.gxf', b'.h261',
        b'.h263', b'.h264', b'.h265', b'.h26l', b'.hevc', b'.ice', b'.ico', b'.idf', b'.idx', b'.im1',
        b'.im24', b'.im8', b'.ircam', b'.ivf', b'.ivr', b'.j2c', b'.j2k', b'.jls', b'.jp2', b'.jpeg',
        b'.jpg', b'.js', b'.jss', b'.lbc', b'.ljpg', b'.lrc', b'.lvf', b'.m2a', b'.m2t', b'.m2ts',
        b'.m3u8', b'.m4a', b'.m4v', b'.mac', b'.mj2', b'.mjpeg', b'.mjpg', b'.mk3d', b'.mka', b'.mks',
        b'.mkv', b'.mlp', b'.mmf', b'.mov', b'.mp2', b'.mp3', b'.mp4', b'.mpa', b'.mpc', b'.mpeg',
        b'.mpg', b'.mpl2', b'.mpo', b'.msf', b'.mts', b'.mvi', b'.mxf', b'.mxg', b'.nfo', b'.nist',
        b'.nut', b'.ogg', b'.ogv', b'.oma', b'.omg', b'.paf', b'.pam', b'.pbm', b'.pcx', b'.pgm',
        b'.pgmyuv', b'.pix', b'.pjs', b'.png', b'.ppm', b'.pvf', b'.qcif', b'.ra', b'.ras', b'.rco',
        b'.rcv', b'.rgb', b'.rm', b'.roq', b'.rs', b'.rsd', b'.rso', b'.rt', b'.sami', b'.sb', b'.sbg',
        b'.sdr2', b'.sf', b'.sgi', b'.shn', b'.sln', b'.smi', b'.son', b'.sox', b'.spdif', b'.sph',
        b'.srt', b'.ss2', b'.ssa', b'.stl', b'.str', b'.sub', b'.sun', b'.sunras', b'.sup', b'.svag',
        b'.sw', b'.swf', b'.tak', b'.tco', b'.tga', b'.thd', b'.tif', b'.tiff', b'.ts', b'.tta',
        b'.txt', b'.ub', b'.ul', b'.uw', b'.v', b'.v210', b'.vag', b'.vb', b'.vc1', b'.viv', b'.voc',
        b'.vpk', b'.vqe', b'.vqf', b'.vql', b'.vt', b'.vtt', b'.w64', b'.wav', b'.webm', b'.wma',
        b'.wmv', b'.wtv', b'.wv', b'.xbm', b'.xface', b'.xl', b'.xml', b'.xvag', b'.xwd', b'.y',
        b'.y4m', b'.yop', b'.yuv', b'.yuv10',

        # extra extensions that are known container formats
        b'.raw',
        b'.iso'
    ]

    _FFMPEG_SUPPORTED_ENCODERS = [
        b'., A64', b'.264', b'.265', b'.302', b'.3g2', b'.3gp', b'.722', b'.a64', b'.aa3', b'.aac',
        b'.ac3', b'.adts', b'.adx', b'.afc', b'.aif', b'.aifc', b'.aiff', b'.al', b'.amr', b'.apng',
        b'.asf', b'.ass', b'.ast', b'.au', b'.avc', b'.avi', b'.bit', b'.bmp', b'.caf', b'.cavs',
        b'.chk', b'.cif', b'.daud', b'.dav', b'.dif', b'.dnxhd', b'.dpx', b'.drc', b'.dts', b'.dv', b'.dvd',
        b'.eac3', b'.f4v', b'.ffm', b'.ffmeta', b'.flac', b'.flm', b'.flv', b'.g722', b'.g723_1',
        b'.gif', b'.gxf', b'.h261', b'.h263', b'.h264', b'.h265', b'.h26l', b'.hevc', b'.ico',
        b'.im1', b'.im24', b'.im8', b'.ircam', b'.isma', b'.ismv', b'.ivf', b'.j2c', b'.j2k', b'.jls',
        b'.jp2', b'.jpeg', b'.jpg', b'.js', b'.jss', b'.latm', b'.lbc', b'.ljpg', b'.loas', b'.lrc',
        b'.m1v', b'.m2a', b'.m2t', b'.m2ts', b'.m2v', b'.m3u8', b'.m4a', b'.m4v', b'.mj2', b'.mjpeg',
        b'.mjpg', b'.mk3d', b'.mka', b'.mks', b'.mkv', b'.mlp', b'.mmf', b'.mov', b'.mp2', b'.mp3',
        b'.mp4', b'.mpa', b'.mpeg', b'.mpg', b'.mpo', b'.mts', b'.mxf', b'.nut', b'.oga', b'.ogg',
        b'.ogv', b'.oma', b'.omg', b'.opus', b'.pam', b'.pbm', b'.pcx', b'.pgm', b'.pgmyuv', b'.pix',
        b'.png', b'.ppm', b'.psp', b'.qcif', b'.ra', b'.ras', b'.rco', b'.rcv', b'.rgb', b'.rm',
        b'.roq', b'.rs', b'.rso', b'.sb', b'.sf', b'.sgi', b'.sox', b'.spdif', b'.spx', b'.srt',
        b'.ssa', b'.sub', b'.sun', b'.sunras', b'.sw', b'.swf', b'.tco', b'.tga', b'.thd', b'.tif',
        b'.tiff', b'.ts', b'.ub', b'.ul', b'.uw', b'.vc1', b'.vob', b'.voc', b'.vtt', b'.w64', b'.wav',
        b'.webm', b'.webp', b'.wma', b'.wmv', b'.wtv', b'.wv', b'.xbm', b'.xface', b'.xml', b'.xwd',
        b'.y', b'.y4m', b'.yuv',

        # extra extensions that are known container formats
        b'.raw'
    ]


def _get_ffmpeg_protocols():
    """Return (input_protocols, output_protocols) supported by the installed ffmpeg.

    Lazily caches the result so the subprocess call only runs once per
    interpreter (or until ``setFFmpegPath`` is called, which resets the
    cache). Each return value is a list of bare scheme names like
    ``["file", "http", "https", "pipe", "rtsp", ...]``.

    Used by ``_warn_if_unsupported_protocol`` to give users a useful
    heads-up when their URL scheme isn't compiled into their ffmpeg
    build (e.g. an ffmpeg without HTTPS support hitting an https://
    URL). Returns empty lists on detection failure — callers fall back
    to letting ffmpeg surface its own error.
    """
    global _FFMPEG_PROTOCOLS
    # Read once into a local so concurrent setFFmpegPath() can't null
    # this out from under us mid-function.
    cached = _FFMPEG_PROTOCOLS
    if cached is not None:
        return cached

    inputs, outputs = [], []
    if not _HAS_FFMPEG:
        _FFMPEG_PROTOCOLS = (inputs, outputs)
        return _FFMPEG_PROTOCOLS

    try:
        raw = check_output(
            [os.path.join(_FFMPEG_PATH, _FFMPEG_APPLICATION), "-hide_banner", "-protocols"]
        ).decode(errors="replace")
        # ffmpeg -protocols layout:
        #   Input:
        #     file
        #     http
        #     ...
        #   Output:
        #     file
        #     md5
        #     ...
        section = None
        for line in raw.splitlines():
            stripped = line.strip()
            if stripped.lower().startswith("input"):
                section = "input"
                continue
            if stripped.lower().startswith("output"):
                section = "output"
                continue
            if not stripped or ":" in stripped:
                continue
            if section == "input":
                inputs.append(stripped)
            elif section == "output":
                outputs.append(stripped)
    except Exception:
        # Detection is best-effort; ffmpeg will surface its own error if
        # the protocol really isn't supported.
        pass

    # Single atomic publish so concurrent readers see a fully populated
    # cache or nothing — no half-state with inputs set but outputs None.
    _FFMPEG_PROTOCOLS = (inputs, outputs)
    return _FFMPEG_PROTOCOLS


def _warn_if_unsupported_protocol(url, direction):
    """Emit a UserWarning if ``url``'s scheme isn't in ffmpeg's protocol list.

    ``direction`` is either ``"input"`` (reader) or ``"output"`` (writer).
    Silent no-op for non-URL strings, for ffmpeg builds whose protocol list
    we couldn't detect (empty list), or for protocols that are present.

    We warn rather than raise so the user gets ffmpeg's own (now-readable)
    stderr if they choose to proceed — the warning just makes the root
    cause obvious. Typical case: an ffmpeg compiled without OpenSSL
    support refusing to handle https:// URLs.
    """
    import re as _re
    import warnings as _warnings

    m = _re.match(r"^([a-zA-Z][a-zA-Z0-9+.\-]*)://", str(url))
    if not m:
        return
    scheme = m.group(1).lower()
    inputs, outputs = _get_ffmpeg_protocols()
    available = inputs if direction == "input" else outputs
    if not available:
        return  # detection failed; don't preempt ffmpeg's own error
    if scheme not in available:
        _warnings.warn(
            "ffmpeg at %s does not list %r as a supported %s protocol "
            "(available: %s). ffmpeg may still try and fail with its own "
            "error message; if you see a connection-refused or "
            "protocol-not-found error, rebuild or reinstall ffmpeg with "
            "support for %r." % (
                _FFMPEG_PATH, scheme, direction,
                ", ".join(sorted(available)[:20]) +
                ("..." if len(available) > 20 else ""),
                scheme,
            ),
            UserWarning,
        )


def scan_libav():
    global _LIBAV_MAJOR_VERSION
    global _LIBAV_MINOR_VERSION
    _LIBAV_MAJOR_VERSION = "0"
    _LIBAV_MINOR_VERSION = "0"
    try:
        # grab program version string
        version = check_output([os.path.join(_AVCONV_PATH, _AVCONV_APPLICATION), "-version"])
        # only parse the first line returned
        firstline = version.split(b'\n')[0]

        firstlineparts = firstline.split(b' ')

        # in older versions, the second word is "version",
        # else the version number starts with "v"
        version = ""
        if firstlineparts[1].strip() == b"version":
            version = firstlineparts[2].split('.')[0]
        else:
            version = firstlineparts[1].split(b'-')[0]

        # check for underscore
        version = version.split(b'_')[0]
        versionparts = version.split(b'.')
        if versionparts[0].decode()[0] == 'v':
            _LIBAV_MAJOR_VERSION = versionparts[0].decode()[1:]
        else:
            _LIBAV_MAJOR_VERSION = str(versionparts[0].decode())
            _LIBAV_MINOR_VERSION = str(versionparts[1].decode())
    except:
        pass



if _MEDIAINFO_PATH is not None:
    _HAS_MEDIAINFO = 1


# allow library configuration checking
def getFFmpegPath():
    """ Returns the path to the directory containing both ffmpeg and ffprobe
    """
    return _FFMPEG_PATH


def getFFmpegVersion():
    """ Returns the version of FFmpeg that is currently being used
    """
    if _FFMPEG_MAJOR_VERSION[0] == 'N':
        return "%s" % (_FFMPEG_MAJOR_VERSION, )
    else:
        return "%s.%s.%s" % (_FFMPEG_MAJOR_VERSION, _FFMPEG_MINOR_VERSION, _FFMPEG_PATCH_VERSION)


def setFFmpegPath(path):
    """ Sets up the path to the directory containing both ffmpeg and ffprobe

        Use this function for to specify specific system installs of FFmpeg. All
        calls to ffmpeg and ffprobe will use this path as a prefix.

        Parameters
        ----------
        path : string
            Path to directory containing ffmpeg and ffprobe

        Returns
        -------
        none

    """
    global _FFMPEG_PATH
    global _HAS_FFMPEG
    global _FFMPEG_PROTOCOLS
    _FFMPEG_PATH = path
    # New binary may have different compiled-in protocol support; clear
    # the cache so the next URL use re-detects (issue #117 protocol check).
    _FFMPEG_PROTOCOLS = None

    # check to see if the executables actually exist on these paths
    if os.path.isfile(os.path.join(_FFMPEG_PATH, _FFMPEG_APPLICATION)) and os.path.isfile(os.path.join(_FFMPEG_PATH, _FFPROBE_APPLICATION)):
        _HAS_FFMPEG = 1
    else:
        # Be explicit that we're looking for the ffmpeg/ffprobe BINARIES,
        # not Python modules. Issue #159: the old wording made users think
        # the warning was about skvideo/io/ffmpeg.py (the wrapper module).
        warnings.warn(
            "ffmpeg/ffprobe binaries not found at %s. Install FFmpeg and "
            "make sure %s and %s exist there, or call "
            "skvideo.setFFmpegPath() to point at a different directory." % (
                str(path), _FFMPEG_APPLICATION, _FFPROBE_APPLICATION,
            ),
            UserWarning,
        )
        _HAS_FFMPEG = 0
        global _FFMPEG_MAJOR_VERSION
        global _FFMPEG_MINOR_VERSION
        global _FFMPEG_PATCH_VERSION
        _FFMPEG_MAJOR_VERSION = "0"
        _FFMPEG_MINOR_VERSION = "0"
        _FFMPEG_PATCH_VERSION = "0"
        return

    # reload version from new path
    scan_ffmpeg()


def getLibAVPath():
    """ Returns the path to the directory containing both avconv and avprobe
    """
    return _AVCONV_PATH


def getLibAVVersion():
    """ Returns the version of LibAV that is currently being used
    """
    return "%s.%s" % (_LIBAV_MAJOR_VERSION, _LIBAV_MINOR_VERSION)


def setLibAVPath(path):
    """ Sets up the path to the directory containing both avconv and avprobe

        Use this function for to specify specific system installs of LibAV. All
        calls to avconv and avprobe will use this path as a prefix.

        Parameters
        ----------
        path : string
            Path to directory containing avconv and avprobe

        Returns
        -------
        none

    """
    global _AVCONV_PATH
    global _HAS_AVCONV
    _AVCONV_PATH = path

    # check to see if the executables actually exist on these paths
    if os.path.isfile(os.path.join(_AVCONV_PATH, _AVCONV_APPLICATION)) and os.path.isfile(os.path.join(_AVCONV_PATH, _AVPROBE_APPLICATION)):
        _HAS_AVCONV = 1
    else:
        warnings.warn(
            "avconv/avprobe binaries not found at %s. Install libav and "
            "make sure %s and %s exist there, or call "
            "skvideo.setLibAVPath() to point at a different directory." % (
                str(path), _AVCONV_APPLICATION, _AVPROBE_APPLICATION,
            ),
            UserWarning,
        )
        _HAS_AVCONV = 0
        global _LIBAV_MAJOR_VERSION
        global _LIBAV_MINOR_VERSION
        _LIBAV_MAJOR_VERSION = "0"
        _LIBAV_MINOR_VERSION = "0"
        return

    # reload version from new path
    scan_libav()

if (len(_FFMPEG_PATH) > 0):
    setFFmpegPath(_FFMPEG_PATH)


if (len(_AVCONV_PATH) > 0):
    setLibAVPath(_AVCONV_PATH)


__all__ = [
    "getFFmpegPath",
    "getFFmpegVersion",
    "setFFmpegPath",
    "getLibAVPath",
    "getLibAVVersion",
    "setLibAVPath",
]
