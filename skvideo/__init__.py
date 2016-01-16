__version__ = "1.0.0"

from .utils import check_output

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

_HAS_FFMPEG = 0
_HAS_AVCONV = 0
_HAS_MEDIAINFO = 0

_LIBAV_MAJOR_VERSION = 0
_LIBAV_MINOR_VERSION = 0
_LIBAV_PATCH_VERSION = 0
_FFMPEG_MAJOR_VERSION = 0
_FFMPEG_MINOR_VERSION = 0
_FFMPEG_PATCH_VERSION = 0


if ((which("ffmpeg") != None) and (which("ffprobe") != None)):
    _HAS_FFMPEG = 1
    # grab program version string
    version = check_output(["ffmpeg",  "-version"])
    # only parse the first line returned
    firstline = version.split('\n')[0]
    # the 3rd element in this line is the version number
    version = firstline.split(' ')[2].strip()
    versionparts = version.split('.')
    _FFMPEG_MAJOR_VERSION = int(versionparts[0])
    _FFMPEG_MINOR_VERSION = int(versionparts[1])
    _FFMPEG_PATCH_VERSION = int(versionparts[2])

if ((which("avconv") != None) and (which("avprobe") != None)):
    _HAS_AVCONV = 1
    # grab program version string
    version = check_output(["avconv",  "-version"])
    print version
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

if which("mediainfo") != None:
    _HAS_MEDIAINFO = 1
