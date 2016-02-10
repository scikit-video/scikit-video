__version__ = "1.1.1"

from .utils import check_output
import os
import warnings
import numpy as np

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
_FFMPEG_PATH = which("ffprobe")
if _FFMPEG_PATH is not None:
    _FFMPEG_PATH = os.path.split(_FFMPEG_PATH)[0]


# only avprobe exists with libav
_AVCONV_PATH = which("avprobe")
if _AVCONV_PATH is not None:
    _AVCONV_PATH = os.path.split(_AVCONV_PATH)[0]

_MEDIAINFO_PATH = which("mediainfo")
if _MEDIAINFO_PATH is not None:
    _MEDIAINFO_PATH = os.path.split(_MEDIAINFO_PATH)[0]

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
    # here the output of those commands is provided
    _FFMPEG_SUPPORTED_DECODERS = [
        '.264', '.265', '.302', '.3g2', '.3gp', '.722', '.aa', '.aa3', '.aac', '.ac3',
        '.acm', '.adf', '.adp', '.ads', '.adx', '.aea', '.afc', '.aif', '.aifc', '.aiff',
        '.al', '.amr', '.ans', '.ape', '.apl', '.apng', '.aqt', '.art', '.asc', '.asf',
        '.ass', '.ast', '.au', '.avc', '.avi', '.avr', '.bcstm', '.bfstm', '.bin', '.bit',
        '.bmp', '.bmv', '.brstm', '.caf', '.cavs', '.cdata', '.cdg', '.cdxl', '.cgi',
        '.cif', '.daud', '.dif', '.diz', '.dnxhd', '.dpx', '.drc', '.dss', '.dtk', '.dts',
        '.dtshd', '.dv', '.eac3', '.fap', '.ffm', '.ffmeta', '.flac', '.flm', '.flv',
        '.fsb', '.g722', '.g723_1', '.g729', '.genh', '.gif', '.gsm', '.gxf', '.h261',
        '.h263', '.h264', '.h265', '.h26l', '.hevc', '.ice', '.ico', '.idf', '.idx', '.im1',
        '.im24', '.im8', '.ircam', '.ivf', '.ivr', '.j2c', '.j2k', '.jls', '.jp2', '.jpeg',
        '.jpg', '.js', '.jss', '.lbc', '.ljpg', '.lrc', '.lvf', '.m2a', '.m2t', '.m2ts',
        '.m3u8', '.m4a', '.m4v', '.mac', '.mj2', '.mjpeg', '.mjpg', '.mk3d', '.mka', '.mks',
        '.mkv', '.mlp', '.mmf', '.mov', '.mp2', '.mp3', '.mp4', '.mpa', '.mpc', '.mpeg',
        '.mpg', '.mpl2', '.mpo', '.msf', '.mts', '.mvi', '.mxf', '.mxg', '.nfo', '.nist',
        '.nut', '.ogg', '.ogv', '.oma', '.omg', '.paf', '.pam', '.pbm', '.pcx', '.pgm',
        '.pgmyuv', '.pix', '.pjs', '.png', '.ppm', '.pvf', '.qcif', '.ra', '.ras', '.rco',
        '.rcv', '.rgb', '.rm', '.roq', '.rs', '.rsd', '.rso', '.rt', '.sami', '.sb', '.sbg',
        '.sdr2', '.sf', '.sgi', '.shn', '.sln', '.smi', '.son', '.sox', '.spdif', '.sph',
        '.srt', '.ss2', '.ssa', '.stl', '.str', '.sub', '.sun', '.sunras', '.sup', '.svag',
        '.sw', '.swf', '.tak', '.tco', '.tga', '.thd', '.tif', '.tiff', '.ts', '.tta',
        '.txt', '.ub', '.ul', '.uw', '.v', '.v210', '.vag', '.vb', '.vc1', '.viv', '.voc',
        '.vpk', '.vqe', '.vqf', '.vql', '.vt', '.vtt', '.w64', '.wav', '.webm', '.wma',
        '.wmv', '.wtv', '.wv', '.xbm', '.xface', '.xl', '.xml', '.xvag', '.xwd', '.y',
        '.y4m', '.yop', '.yuv', '.yuv10'
    ]

    _FFMPEG_SUPPORTED_ENCODERS = [
        '., A64', '.264', '.265', '.302', '.3g2', '.3gp', '.722', '.a64', '.aa3', '.aac',
        '.ac3', '.adts', '.adx', '.afc', '.aif', '.aifc', '.aiff', '.al', '.amr', '.apng',
        '.asf', '.ass', '.ast', '.au', '.avc', '.avi', '.bit', '.bmp', '.caf', '.cavs',
        '.chk', '.cif', '.daud', '.dif', '.dnxhd', '.dpx', '.drc', '.dts', '.dv', '.dvd',
        '.eac3', '.f4v', '.ffm', '.ffmeta', '.flac', '.flm', '.flv', '.g722', '.g723_1',
        '.gif', '.gxf', '.h261', '.h263', '.h264', '.h265', '.h26l', '.hevc', '.ico',
        '.im1', '.im24', '.im8', '.ircam', '.isma', '.ismv', '.ivf', '.j2c', '.j2k', '.jls',
        '.jp2', '.jpeg', '.jpg', '.js', '.jss', '.latm', '.lbc', '.ljpg', '.loas', '.lrc',
        '.m1v', '.m2a', '.m2t', '.m2ts', '.m2v', '.m3u8', '.m4a', '.m4v', '.mj2', '.mjpeg',
        '.mjpg', '.mk3d', '.mka', '.mks', '.mkv', '.mlp', '.mmf', '.mov', '.mp2', '.mp3',
        '.mp4', '.mpa', '.mpeg', '.mpg', '.mpo', '.mts', '.mxf', '.nut', '.oga', '.ogg',
        '.ogv', '.oma', '.omg', '.opus', '.pam', '.pbm', '.pcx', '.pgm', '.pgmyuv', '.pix',
        '.png', '.ppm', '.psp', '.qcif', '.ra', '.ras', '.rco', '.rcv', '.rgb', '.rm',
        '.roq', '.rs', '.rso', '.sb', '.sf', '.sgi', '.sox', '.spdif', '.spx', '.srt',
        '.ssa', '.sub', '.sun', '.sunras', '.sw', '.swf', '.tco', '.tga', '.thd', '.tif',
        '.tiff', '.ts', '.ub', '.ul', '.uw', '.vc1', '.vob', '.voc', '.vtt', '.w64', '.wav',
        '.webm', '.webp', '.wma', '.wmv', '.wtv', '.wv', '.xbm', '.xface', '.xml', '.xwd',
        '.y', '.y4m', '.yuv'
    ]


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
            _LIBAV_MAJOR_VERSION = str(versionparts[0].decode())
            _LIBAV_MINOR_VERSION = str(versionparts[1].decode())
    #except:
    #    pass




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
