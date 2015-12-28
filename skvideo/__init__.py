__version__ = "1.0.0"

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

if ((which("ffmpeg") != None) and (which("ffprobe") != None)):
    _HAS_FFMPEG = 1

if ((which("avconv") != None) and (which("avprobe") != None)):
    _HAS_AVCONV = 1

if which("mediainfo") != None:
    _HAS_MEDIAINFO = 1
