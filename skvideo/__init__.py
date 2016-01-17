__version__ = "1.0.0"

from .utils import check_output
import os

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

_FFMPEG_PATH = os.path.split(which("ffmpeg"))[0]
_FFPROBE_PATH = os.path.split(which("ffprobe"))[0]
_AVCONV_PATH = os.path.split(which("avconv"))[0]
_AVPROBE_PATH = os.path.split(which("avprobe"))[0]
_MEDIAINFO_PATH = os.path.split(which("mediainfo"))[0]

_HAS_FFMPEG = 0
_HAS_AVCONV = 0
_HAS_MEDIAINFO = 0

_LIBAV_MAJOR_VERSION = 0
_LIBAV_MINOR_VERSION = 0
_LIBAV_PATCH_VERSION = 0
_FFMPEG_MAJOR_VERSION = 0
_FFMPEG_MINOR_VERSION = 0
_FFMPEG_PATCH_VERSION = 0

def scan_ffmpeg():
    global _FFMPEG_MAJOR_VERSION
    global _FFMPEG_MINOR_VERSION
    global _FFMPEG_PATCH_VERSION
    _FFMPEG_MAJOR_VERSION = 0
    _FFMPEG_MINOR_VERSION = 0
    _FFMPEG_PATCH_VERSION = 0
    try:
        # grab program version string
        version = check_output([_FFMPEG_PATH + "/ffmpeg", "-version"])
        # only parse the first line returned
        firstline = version.split('\n')[0]
        # the 3rd element in this line is the version number
        version = firstline.split(' ')[2].strip()
        versionparts = version.split('.')
        _FFMPEG_MAJOR_VERSION = int(versionparts[0])
        _FFMPEG_MINOR_VERSION = int(versionparts[1])
        if len(versionparts) > 2:
            _FFMPEG_PATCH_VERSION = int(versionparts[2])
    except:
        pass

def scan_libav():
    global _LIBAV_MAJOR_VERSION
    global _LIBAV_MINOR_VERSION
    global _LIBAV_PATCH_VERSION
    _LIBAV_MAJOR_VERSION = 0
    _LIBAV_MINOR_VERSION = 0
    _LIBAV_PATCH_VERSION = 0
    try:
        # grab program version string
        version = check_output([_AVCONV_PATH + "/avconv", "-version"])
        # only parse the first line returned
        firstline = version.split('\n')[0]

        firstlineparts = firstline.split(' ')

        # in older versions, the second word is "version", 
        # else the version number starts with "v"
        if firstlineparts[1].strip() == "version":
            version = firstlineparts[2].split('-')[0]
        else:
            version = firstlineparts[1].split('-')[0]
            # check for underscore
            version = version.split('_')[0]
            versionparts = version.split('.')
            if versionparts[0][0] == 'v':
                _LIBAV_MAJOR_VERSION = int(versionparts[0][1:])
            else:
                _LIBAV_MAJOR_VERSION = int(versionparts[0])
                _LIBAV_MINOR_VERSION = int(versionparts[1])
    except:
        pass


if ((_FFMPEG_PATH is not None) and (_FFPROBE_PATH is not None)):
    _HAS_FFMPEG = 1
    scan_ffmpeg()

if ((_AVCONV_PATH is not None) and (_AVPROBE_PATH is not None)):
    _HAS_AVCONV = 1
    scan_libav()


if _MEDIAINFO_PATH is not None:
    _HAS_MEDIAINFO = 1


# allow library configuration checking
def getFFmpegPath():
    return _FFMPEG_PATH


def getFFmpegVersion():
    return "%d.%d.%d" % (_FFMPEG_MAJOR_VERSION, _FFMPEG_MINOR_VERSION, _FFMPEG_PATCH_VERSION)


def setFFmpegPath(path):
    global _FFMPEG_PATH
    global _FFPROBE_PATH
    _FFMPEG_PATH = path
    _FFPROBE_PATH = path

    # reload version from new path
    scan_ffmpeg()


def getLibAVPath():
    return _FFMPEG_PATH


def getLibAVVersion():
    return "%d.%d" % (_LIBAV_MAJOR_VERSION, _LIBAV_MINOR_VERSION) 


def setLibAVPath(path):
    global _AVCONV_PATH
    global _AVPROBE_PATH
    _AVCONV_PATH = path
    _AVPROBE_PATH = path
    scan_libav()


__all__ = [
    getFFmpegPath,
    getFFmpegVersion,
    setFFmpegPath,
    getLibAVPath,
    getLibAVVersion,
    setLibAVPath,
]

