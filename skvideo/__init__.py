__version__ = "1.1.0"

from .utils import check_output
import os
import warnings

# Run a program-based check to see if all install
# requirements have been met. 
# Sets environment variables based on programs
# found.

def which(program):
    import os
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None

# only ffprobe exists with ffmpeg
_FFMPEG_PATH = os.path.split(which("ffprobe"))[0]

# only avprobe exists with libav
_AVCONV_PATH = os.path.split(which("avprobe"))[0]

_MEDIAINFO_PATH = os.path.split(which("mediainfo"))[0]

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
        version = check_output([_FFMPEG_PATH + "/ffmpeg", "-version"])
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

    try:
        extension_lst = check_output([_FFMPEG_PATH + "/ffmpeg", "-formats"])
        extension_lst = extension_lst.split(b'\n')
        # skip first line
        for item in extension_lst[4:]:
            parts = [x.strip() for x in item.split(b' ') if x]
            if len(parts) < 2:
                continue
            rule = parts[0]
            extension = parts[1]
            if b'D' in rule:
                for item in extension.split(b","):
                    _FFMPEG_SUPPORTED_DECODERS.append(b"." + item)
            if b'E' in rule:
                for item in extension.split(b","):
                    _FFMPEG_SUPPORTED_ENCODERS.append(b"." + item)

    except:
        pass


def scan_libav():
    global _LIBAV_MAJOR_VERSION
    global _LIBAV_MINOR_VERSION
    _LIBAV_MAJOR_VERSION = "0"
    _LIBAV_MINOR_VERSION = "0"
    #try:
    if 1:
        # grab program version string
        version = check_output([_AVCONV_PATH + "/avconv", "-version"])
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
            _LIBAV_MAJOR_VERSION = str(versionparts[0])
            _LIBAV_MINOR_VERSION = str(versionparts[1])
    #except:
    #    pass




if _MEDIAINFO_PATH is not None:
    _HAS_MEDIAINFO = 1


# allow library configuration checking
def getFFmpegPath():
    """ Returns the path to the directory containing both FFmpeg and FFprobe 
    """
    return _FFMPEG_PATH


def getFFmpegVersion():
    """ Returns the version of FFmpeg that currently being used
    """ 
    if _FFMPEG_MAJOR_VERSION[0] == 'N':
        return "%s" % (_FFMPEG_MAJOR_VERSION, )
    else:
        return "%s.%s.%s" % (_FFMPEG_MAJOR_VERSION, _FFMPEG_MINOR_VERSION, _FFMPEG_PATCH_VERSION)


def setFFmpegPath(path):
    """ Sets up the path to the directory containing both FFmpeg and FFprobe

        Use this function for to specify specific system installs of FFmpeg. All
        calls to FFmpeg and FFprobe will use this path as a prefix.

        Parameters
        ----------
        path : string
            Path to directory containing FFmpeg and FFprobe

        Returns
        -------
        none

    """ 
    global _FFMPEG_PATH
    global _HAS_FFMPEG
    _FFMPEG_PATH = path

    # check to see if the executables actually exist on these paths
    if os.path.isfile(_FFMPEG_PATH + "/ffmpeg") and os.path.isfile(_FFMPEG_PATH + "/ffprobe"):
        _HAS_FFMPEG = 1
    else:
        warnings.warn("ffmpeg/ffprobe not found in path: " + str(path), UserWarning)
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
    return _AVCONV_PATH


def getLibAVVersion():
    return "%s.%s" % (_LIBAV_MAJOR_VERSION, _LIBAV_MINOR_VERSION) 


def setLibAVPath(path):
    """ Sets up the path to the directory containing both avconv and avprobe

        Use this function for to specify specific system installs of libav. All
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
    if os.path.isfile(_AVCONV_PATH + "/avconv") and os.path.isfile(_AVCONV_PATH + "/avprobe"):
        _HAS_AVCONV = 1
    else:
        warnings.warn("avconv/avprobe not found in path: " + str(path), UserWarning)
        _HAS_AVCONV = 0
        global _LIBAV_MAJOR_VERSION
        global _LIBAV_MINOR_VERSION
        _LIBAV_MAJOR_VERSION = "0"
        _LIBAV_MINOR_VERSION = "0"
        return

    # reload version from new path
    scan_libav()

if (_FFMPEG_PATH is not None):
    setFFmpegPath(_FFMPEG_PATH)


if (_AVCONV_PATH is not None):
    _HAS_AVCONV = 1
    setLibAVPath(_AVCONV_PATH)


__all__ = [
    getFFmpegPath,
    getFFmpegVersion,
    setFFmpegPath,
    getLibAVPath,
    getLibAVVersion,
    setLibAVPath,
]

