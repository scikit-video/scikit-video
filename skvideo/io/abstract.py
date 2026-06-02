import io
import os
import re
import tempfile
import threading
import time
import warnings

import numpy as np

from .. import _HAS_FFMPEG
from .. import _warn_if_unsupported_protocol
from ..utils import *


# Matches URL schemes ffmpeg supports for input/output (http, https, rtsp, rtmp,
# rtmps, udp, tcp, ftp, sftp, srt, unix, file, pipe, concat, async, hls, ...).
# We classify any string that looks like `<scheme>://<...>` as a URL and let
# ffmpeg validate the specific protocol.
_URL_SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.\-]*://")


def _classify_source(source):
    """Classify an input/output source into one of three kinds.

    Returns one of ``"file"``, ``"url"``, ``"memory"``. Used by the reader and
    writer to dispatch around filesystem-only operations like ``os.path.getsize``,
    ``os.path.isfile``, and ``os.access(..., os.W_OK)`` (issue #117, #113, #81).

    - ``str`` or ``Path`` matching ``<scheme>://...`` → ``"url"``
    - ``BytesIO`` or any object with a ``read`` / ``write`` method → ``"memory"``
    - everything else → ``"file"`` (the existing behavior)

    A pure string filename like ``"video.mp4"`` is classified as ``"file"``; the
    URL check is intentionally strict (``://`` required) so Windows drive
    letters and oddly-named local files don't false-positive.
    """
    # File-like / BytesIO objects expose read or write
    if hasattr(source, "read") or hasattr(source, "write"):
        return "memory"
    # os.fspath() turns Path into str without changing strings
    try:
        source_str = os.fspath(source)
    except TypeError:
        return "file"  # fallback; downstream will surface the real error
    if _URL_SCHEME_RE.match(source_str):
        return "url"
    return "file"


def _spool_memory_to_tempfile(source):
    """Copy a file-like ``source`` into a NamedTemporaryFile and return its path.

    Called when the reader's input is a BytesIO or other file-like (issue
    #113). Container formats like mp4 need random access to read header
    atoms that live at the end of the file, which subprocess stdin can't
    reliably provide. Spooling to disk lets the rest of the read path
    treat the source uniformly with a regular filename.

    The temp file is created with ``delete=False``; the caller (typically
    ``VideoReaderAbstract.close``) is responsible for unlinking it. If the
    source has a ``.name`` attribute with a recognizable extension, that
    extension is preserved on the temp file; otherwise ``.mp4`` is used
    as a sensible default (ffmpeg always content-detects format regardless
    of extension, but our wrapper's extension-based decoder-allowlist check
    needs *some* valid extension).
    """
    if hasattr(source, "seek"):
        source.seek(0)
    suffix = ".mp4"
    name = getattr(source, "name", None)
    if isinstance(name, str):
        _, ext = os.path.splitext(name)
        if ext:
            suffix = ext
    tf = tempfile.NamedTemporaryFile(
        prefix="skvideo_in_", suffix=suffix, delete=False
    )
    try:
        # Stream-copy in chunks so we don't materialize huge buffers.
        while True:
            chunk = source.read(1024 * 1024)
            if not chunk:
                break
            tf.write(chunk)
    finally:
        tf.close()
    return tf.name


class VideoReaderAbstract(object):
    """Reads frames
    """

    INFO_AVERAGE_FRAMERATE = None  # "avg_frame_rate"
    INFO_WIDTH = None  # "width"
    INFO_HEIGHT = None  # "height"
    INFO_PIX_FMT = None  # "pix_fmt"
    INFO_DURATION = None  # "duration"
    INFO_NB_FRAMES = None  # "nb_frames"
    DEFAULT_FRAMERATE = 25.
    DEFAULT_INPUT_PIX_FMT = "yuvj444p"
    OUTPUT_METHOD = None  # "rawvideo"

    def __init__(self, filename, inputdict=None, outputdict=None, verbosity=0, start_frame=0):
        """Initializes FFmpeg in reading mode with the given parameters

        During initialization, additional parameters about the video file
        are parsed using :func:`skvideo.io.ffprobe`. Then FFmpeg is launched
        as a subprocess. Parameters passed into inputdict are parsed and
        used to set as internal variables about the video. If the parameter,
        such as "Height" is not found in the inputdict, it is found through
        scanning the file's header information. If not in the header, ffprobe
        is used to decode the file to determine the information. In the case
        that the information is not supplied and connot be inferred from the
        input file, a ValueError exception is thrown.

        Parameters
        ----------
        filename : string
            Video file path

        inputdict : dict
            Input dictionary parameters, i.e. how to interpret the input file.

        outputdict : dict
            Output dictionary parameters, i.e. how to encode the data
            when sending back to the python process.

        start_frame : int
            Skip the first ``start_frame`` frames of the input (issue #166).
            Uses FFmpeg's fast keyframe-based ``-ss`` seek (input seeking),
            so the actual first frame returned may snap to the nearest
            keyframe at or before the requested position. Combine with
            ``num_frames`` for a windowed read. For frame-exact extraction,
            pass ``inputdict={"-vf": "select='gte(n\\\\,N)'"}`` instead;
            that is slower because it decodes from the start of the file.

        Returns
        -------
        none

        """
        # check if FFMPEG exists in the path
        assert _HAS_FFMPEG, "Cannot find installation of real FFmpeg (which comes with ffprobe)."

        self._source_kind = _classify_source(filename)
        # Track temp files spooled from memory sources so close() can clean
        # them up. None for file / url sources.
        self._temp_input_path = None
        # Memory sources (BytesIO, file-like): spool to a temp file so the
        # rest of __init__ — ffprobe, extension heuristics, frame reading —
        # can operate on a regular path. mp4's moov atom in particular
        # needs random access that subprocess stdin can't provide reliably.
        # After spooling, treat as a file for all downstream branching.
        if self._source_kind == "memory":
            self._temp_input_path = _spool_memory_to_tempfile(filename)
            filename = self._temp_input_path
            self._source_kind = "file"
        elif self._source_kind == "url":
            # Warn early if the installed ffmpeg lacks support for this
            # URL scheme (e.g. https on a build without OpenSSL). The
            # warning makes ffmpeg's eventual error obvious; we don't
            # raise because protocol detection is best-effort.
            _warn_if_unsupported_protocol(filename, "input")
        filename = os.fspath(filename)

        # Wrap the rest of __init__ so that any failure (bad ffprobe,
        # missing width/height, decoder mismatch) unlinks the spooled temp
        # file before re-raising. Without this, callers never get a
        # reference to the half-constructed reader, so close() is
        # unreachable and the temp file leaks (Codex round 1 finding).
        try:
            self._finish_init(filename, inputdict, outputdict, verbosity, start_frame)
        except Exception:
            if self._temp_input_path is not None:
                try:
                    os.unlink(self._temp_input_path)
                except OSError:
                    pass
                self._temp_input_path = None
            raise

    def _finish_init(self, filename, inputdict, outputdict, verbosity, start_frame):
        """The rest of __init__, wrapped so spool failure cleanup can apply.

        Extracted purely for the try/except boundary; semantics are
        unchanged from doing this work inline (Codex round 1: temp-leak fix).
        """
        self._filename = filename
        self.verbosity = verbosity

        if not inputdict:
            inputdict = {}

        if not outputdict:
            outputdict = {}

        # General information. URLs skip filesystem ops entirely; memory
        # sources reach here as "file" because we already spooled them to
        # a real temp path above. ffmpeg/ffprobe handle URLs natively
        # (note: probing a remote URL incurs network latency on
        # FFmpegReader construction).
        if self._source_kind == "file":
            _, self.extension = os.path.splitext(filename)
            self.size = os.path.getsize(filename)
        else:
            # URL: no meaningful filesystem extension; use empty so downstream
            # checks (which mostly gate on .yuv / .raw) skip cleanly.
            self.extension = ""
            self.size = 0
        self.probeInfo = self._probe()

        # smartphone video data is weird
        self.rotationAngle = '0'  # specific FFMPEG

        viddict = {}
        if "video" in self.probeInfo:
            viddict = self.probeInfo["video"]

        self.inputfps = -1
        if ("-r" in inputdict):
            r_val = str(inputdict["-r"])
            parts = r_val.split('/')
            if len(parts) > 1:
                self.inputfps = float(parts[0]) / float(parts[1])
            else:
                self.inputfps = float(r_val)
        elif self.INFO_AVERAGE_FRAMERATE in viddict:
            # check for the slash
            frtxt = viddict[self.INFO_AVERAGE_FRAMERATE]
            parts = frtxt.split('/')
            if len(parts) > 1:
                if float(parts[1]) == 0.:
                    self.inputfps = self.DEFAULT_FRAMERATE
                else:
                    self.inputfps = float(parts[0]) / float(parts[1])
            else:
                self.inputfps = float(frtxt)
        else:
            self.inputfps = self.DEFAULT_FRAMERATE

        # Frame-range seek (issue #166). start_frame is converted to a
        # seconds-based -ss before -i so FFmpeg performs a fast keyframe
        # seek. Refuse to silently mix this with a user-supplied -ss.
        if start_frame > 0:
            if "-ss" in inputdict:
                raise ValueError(
                    "Cannot use both start_frame and inputdict['-ss']; "
                    "choose one."
                )
            if not self.inputfps or float(self.inputfps) <= 0:
                raise ValueError(
                    "Cannot use start_frame without a positive input "
                    "framerate (got %r). Drop start_frame or supply a "
                    "valid inputdict['-r']." % self.inputfps
                )
            inputdict["-ss"] = str(start_frame / float(self.inputfps))
        self._start_frame = start_frame

        # check for transposition tag
        if ('tag' in viddict):
            tagdata = viddict['tag']
            if not isinstance(tagdata, list):
                tagdata = [tagdata]

            for tags in tagdata:
                if tags['@key'] == 'rotate':
                    self.rotationAngle = tags['@value']

        # if we don't have width or height at all, raise exception
        if ("-s" in inputdict):
            widthheight = inputdict["-s"].split('x')
            self.inputwidth = int(widthheight[0])
            self.inputheight = int(widthheight[1])
        elif ((self.INFO_WIDTH in viddict) and (self.INFO_HEIGHT in viddict)):
            self.inputwidth = int(viddict[self.INFO_WIDTH])
            self.inputheight = int(viddict[self.INFO_HEIGHT])
        else:
            raise ValueError(
                "No way to determine width or height from video. Need `-s` in `inputdict`. Consult documentation on I/O.")

        # smartphone recordings seem to store data about rotations
        # in tag format. Just swap the width and height
        if self.rotationAngle == '90' or self.rotationAngle == '270':
            self.inputwidth, self.inputheight = self.inputheight, self.inputwidth

        self.bpp = -1  # bits per pixel
        self.pix_fmt = ""
        # completely unsure of this:
        if ("-pix_fmt" in inputdict):
            self.pix_fmt = inputdict["-pix_fmt"]
        elif (self.INFO_PIX_FMT in viddict):
            # parse this bpp
            self.pix_fmt = viddict[self.INFO_PIX_FMT]
        else:
            self.pix_fmt = self.DEFAULT_INPUT_PIX_FMT
            if verbosity != 0:
                warnings.warn("No input color space detected. Assuming {}.".format(self.DEFAULT_INPUT_PIX_FMT),
                              UserWarning)

        self.inputdepth = int(bpplut[self.pix_fmt][0])
        self.bpp = int(bpplut[self.pix_fmt][1])

        israw = str.encode(self.extension) in [b".raw", b".yuv"]
        # iswebcam covers cases where input has no finite frame count (live
        # device, streaming URL). The os.path.isfile heuristic still routes
        # /dev/video* and similar to this branch. Memory sources have
        # already been spooled to a temp file path above, so they take the
        # file branch with isfile==True. URLs need explicit handling.
        if self._source_kind == "file":
            iswebcam = not os.path.isfile(filename)
        else:
            # URL: treat as a stream unless the metadata gave us a frame
            # count (e.g. mp4 over http reports nb_frames).
            iswebcam = self.INFO_NB_FRAMES not in viddict

        if ("-vframes" in outputdict):
            self.inputframenum = int(outputdict["-vframes"])
        elif ("-r" in outputdict):
            inputfps = int(outputdict["-r"])
            inputduration = float(viddict[self.INFO_DURATION])

            self.inputframenum = int(round(inputfps * inputduration) + 1)
        elif (self.INFO_NB_FRAMES in viddict):
            self.inputframenum = int(viddict[self.INFO_NB_FRAMES])
        elif israw:
            # we can compute it based on the input size and color space
            self.inputframenum = int(self.size / (self.inputwidth * self.inputheight * (self.bpp / 8.0)))
        elif iswebcam:
            # webcam (or live URL) can stream frames endlessly, lets use the
            # special default value of 0 to indicate that
            self.inputframenum = 0
        else:
            self.inputframenum = self._probCountFrames()
            if verbosity != 0:
                warnings.warn(
                    "Cannot determine frame count. Scanning input file, this is slow when repeated many times. Need `-vframes` in inputdict. Consult documentation on I/O.",
                    UserWarning)

        # Adjust the expected frame count for start_frame seek so getShape()
        # reports what nextFrame() will actually yield. If the user also
        # passed -vframes, that already governs the output count.
        if start_frame > 0 and "-vframes" not in outputdict and self.inputframenum > 0:
            self.inputframenum = max(0, self.inputframenum - start_frame)

        if israw or iswebcam:
            inputdict['-pix_fmt'] = self.pix_fmt
        elif self._source_kind != "file":
            # URL: ffprobe already validated the codec; the wrapper's
            # extension-based sanity check has no extension to check
            # against. Trust ffmpeg to surface a decode error if it can't
            # handle the input. (Memory inputs reach here as "file" via
            # the temp-spool path, so they DO get the assert below.)
            pass
        else:
            decoders = self._getSupportedDecoders()
            if decoders != NotImplemented:
                # check that the extension makes sense
                assert str.encode(
                    self.extension).lower() in decoders, "Unknown decoder extension: " + self.extension.lower()

        if '-f' not in outputdict:
            outputdict['-f'] = self.OUTPUT_METHOD

        if '-pix_fmt' not in outputdict:
            outputdict['-pix_fmt'] = "rgb24"
        self.output_pix_fmt = outputdict['-pix_fmt']

        if '-s' in outputdict:
            widthheight = outputdict["-s"].split('x')
            self.outputwidth = int(widthheight[0])
            self.outputheight = int(widthheight[1])
        else:
            self.outputwidth = self.inputwidth
            self.outputheight = self.inputheight

        self.outputdepth = int(bpplut[outputdict['-pix_fmt']][0])
        self.outputbpp = int(bpplut[outputdict['-pix_fmt']][1])
        bitpercomponent = self.outputbpp // self.outputdepth
        if bitpercomponent == 8:
            self.dtype = np.dtype('u1')  # np.uint8
        elif bitpercomponent == 16:
            suffix = outputdict['-pix_fmt'][-2:]
            if suffix == 'le':
                self.dtype = np.dtype('<u2')
            elif suffix == 'be':
                self.dtype = np.dtype('>u2')
        else:
            raise ValueError(outputdict['-pix_fmt'] + 'is not a valid pix_fmt for numpy conversion')

        self._createProcess(inputdict, outputdict, verbosity)

    def __next__(self):
        return next(self.nextFrame())

    def __iter__(self):
        for frame in self.nextFrame():
            yield frame
    
    def _createProcess(self, inputdict, outputdict, verbosity):
        pass

    def _probCountFrames(self):
        return NotImplemented

    def _probe(self):
        pass

    def _getSupportedDecoders(self):
        return NotImplemented

    def _dict2Args(self, dict):
        # Flatten {key: value} into [key, value, ...].
        # If value is a list/tuple, repeat the key for each entry — this is
        # how ffmpeg flags like `-metadata key1=val1 -metadata key2=val2`
        # are expressed (issue #168).
        args = []
        for key, value in dict.items():
            if isinstance(value, (list, tuple)):
                if len(value) == 0:
                    raise ValueError(
                        "Empty list/tuple for flag %r in ffmpeg dict — "
                        "silently dropping the flag would hide a programmer "
                        "error. Pass at least one value, or omit the key." % key
                    )
                for v in value:
                    args.append(key)
                    args.append(v)
            else:
                args.append(key)
                args.append(value)
        return args

    def getShape(self):
        """Returns a tuple (T, M, N, C)

        Returns the video shape in number of frames, height, width, and channels per pixel.
        """

        return self.inputframenum, self.outputheight, self.outputwidth, self.outputdepth

    def close(self):
        if self._proc is not None and self._proc.poll() is None:
            self._proc.stdin.close()
            self._proc.stdout.close()
            if self._proc.stderr is not None:
                self._proc.stderr.close()
            self._terminate(0.2)
        self._proc = None
        # Clean up the spooled temp file for memory sources (issue #113).
        # Best-effort: ignore if already removed or unreachable.
        if self._temp_input_path is not None:
            try:
                os.unlink(self._temp_input_path)
            except OSError:
                pass
            self._temp_input_path = None

    def _terminate(self, timeout=1.0):
        """ Terminate the sub process.
        """
        # Check
        if self._proc is None:  # pragma: no cover
            return  # no process
        if self._proc.poll() is not None:
            return  # process already dead
        # Terminate process
        self._proc.terminate()
        # Wait for it to close (but do not get stuck)
        etime = time.time() + timeout
        while time.time() < etime:
            time.sleep(0.01)
            if self._proc.poll() is not None:
                break

    def _read_frame_data(self):
        # Init and check
        framesize = self.outputdepth * self.outputwidth * self.outputheight
        assert self._proc is not None

        try:
            # Read framesize bytes
            arr = np.frombuffer(self._proc.stdout.read(framesize * self.dtype.itemsize), dtype=self.dtype)
            if len(arr) != framesize:
                return np.array([])
            # assert len(arr) == framesize
        except Exception as err:
            self._terminate()
            err1 = str(err)
            raise RuntimeError("%s" % (err1,))
        return arr

    def _readFrame(self):
        # Read and convert to numpy array
        frame = self._read_frame_data()
        if len(frame) == 0:
            return frame

        if self.output_pix_fmt == 'rgb24':
            self._lastread = frame.reshape((self.outputheight, self.outputwidth, self.outputdepth))
        elif self.output_pix_fmt.startswith('yuv444p') or self.output_pix_fmt.startswith(
                'yuvj444p') or self.output_pix_fmt.startswith('yuva444p'):
            self._lastread = frame.reshape((self.outputdepth, self.outputheight, self.outputwidth)).transpose((1, 2, 0))
        else:
            if self.verbosity > 0:
                warnings.warn(
                    'Unsupported reshaping from raw buffer to images frames  for format {:}. Assuming HEIGHTxWIDTHxCOLOR'.format(
                        self.output_pix_fmt), UserWarning)
            self._lastread = frame.reshape((self.outputheight, self.outputwidth, self.outputdepth))

        return self._lastread

    def nextFrame(self):
        """Yields frames using a generator

        Returns T ndarrays of size (M, N, C), where T is number of frames,
        M is height, N is width, and C is number of channels per pixel.

        """
        if self.inputframenum == 0:
            while True:
                frame = self._readFrame()
                if len(frame) == 0:
                    break
                yield frame
        else:
            for i in range(self.inputframenum):
                frame = self._readFrame()
                if len(frame) == 0:
                    break
                yield frame

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class VideoWriterAbstract(object):
    """Writes frames

    this class provides sane initializations for the default case.
    """
    NEED_RGB2GRAY_HACK = False
    DEFAULT_OUTPUT_PIX_FMT = "yuvj444p"

    def __init__(self, filename, inputdict=None, outputdict=None, verbosity=0):
        """Prepares parameters

        Does not instantiate the an FFmpeg subprocess, but simply
        prepares the required parameters.

        Parameters
        ----------
        filename : string
            Video file path for writing

        inputdict : dict
            Input dictionary parameters, i.e. how to interpret the data coming from python.

        outputdict : dict
            Output dictionary parameters, i.e. how to encode the data
            when writing to file.

        Returns
        -------
        none

        """
        self.DEVNULL = open(os.devnull, 'wb')

        # Classify the output destination so we can skip filesystem-only
        # operations (os.path.abspath, os.access W_OK) for URL outputs like
        # rtmp:// or http:// PUT targets. ffmpeg handles the network side
        # natively; the wrapper just needs to get out of its way (issue #117
        # write-side, related #81).
        self._dest_kind = _classify_source(filename)
        # Always-defined fields; the memory branch below may overwrite.
        self._memory_dest = None
        self._stdout_drain_thread = None
        self._stdout_drain_error = None

        if self._dest_kind == "file":
            filename = os.path.abspath(os.fspath(filename))
            _, self.extension = os.path.splitext(filename)
            # check that the extension makes sense
            encoders = self._getSupportedEncoders()
            if encoders != NotImplemented:
                assert str.encode(
                    self.extension).lower() in encoders, "Unknown encoder extension: " + self.extension.lower()

            self._filename = filename
            basepath, _ = os.path.split(filename)

            # check to see if filename is a valid file location
            assert os.access(basepath, os.W_OK), "Cannot write to directory: " + basepath
        elif self._dest_kind == "url":
            # URL output: ffmpeg picks the format from the URL itself
            # (e.g. rtmp://... → FLV) or from -f in outputdict. Skip the
            # extension allowlist and the writable-directory check.
            _warn_if_unsupported_protocol(filename, "output")
            self.extension = ""
            self._filename = filename
        else:
            # Memory destination (BytesIO/file-like with .write). ffmpeg
            # writes encoded bytes to stdout (pipe:1); a background thread
            # drains stdout into the user's buffer so ffmpeg never blocks on
            # a full pipe (issue #113 write-side).
            if not hasattr(filename, "write"):
                raise TypeError(
                    "Memory destination must be a file-like object with a "
                    "write() method (e.g. io.BytesIO()); got %r" % type(filename)
                )
            self._memory_dest = filename
            self._stdout_drain_thread = None
            self._stdout_drain_error = None
            self.extension = ""
            self._filename = "pipe:1"  # ffmpeg writes encoded bytes to stdout

        if not inputdict:
            inputdict = {}

        if not outputdict:
            outputdict = {}

        self.inputdict = inputdict
        self.outputdict = outputdict
        self.verbosity = verbosity

        if "-f" not in self.inputdict:
            self.inputdict["-f"] = "rawvideo"

        # For memory destinations, ffmpeg writes to stdout which is not
        # seekable. Apply streaming-friendly defaults if the caller didn't
        # already specify them (issue #113 write-side):
        #   -f mp4: pick a container; without this, ffmpeg can't infer
        #     format from the "pipe:1" pseudo-filename
        #   -movflags frag_keyframe+empty_moov: write a fragmented mp4 so
        #     the moov atom appears up-front instead of requiring a seek
        #     back to the start at end-of-encode (which would fail on a pipe).
        # If the caller chose a different format (webm, matroska, mpegts, …),
        # we trust them to know it's streamable.
        if self._dest_kind == "memory":
            if "-f" not in self.outputdict:
                self.outputdict["-f"] = "mp4"
            if self.outputdict.get("-f") == "mp4" and "-movflags" not in self.outputdict:
                self.outputdict["-movflags"] = "frag_keyframe+empty_moov"

        self.warmStarted = False
        self._proc = None

    def _warmStart(self, M, N, C, dtype):
        self.warmStarted = True

        if "-pix_fmt" not in self.inputdict:
            # check the number channels to guess
            if dtype.kind == 'u' and dtype.itemsize == 2:
                suffix = 'le' if dtype.byteorder else 'be'
                if C == 1:
                    if self.NEED_RGB2GRAY_HACK:
                        self.inputdict["-pix_fmt"] = "rgb48" + suffix
                        self.rgb2grayhack = True
                        C = 3
                    else:
                        self.inputdict["-pix_fmt"] = "gray16" + suffix
                elif C == 2:
                    self.inputdict["-pix_fmt"] = "ya16" + suffix
                elif C == 3:
                    self.inputdict["-pix_fmt"] = "rgb48" + suffix
                elif C == 4:
                    self.inputdict["-pix_fmt"] = "rgba64" + suffix
                else:
                    raise NotImplemented
            else:
                if C == 1:
                    if self.NEED_RGB2GRAY_HACK:
                        self.inputdict["-pix_fmt"] = "rgb24"
                        self.rgb2grayhack = True
                        C = 3
                    else:
                        self.inputdict["-pix_fmt"] = "gray"
                elif C == 2:
                    self.inputdict["-pix_fmt"] = "ya8"
                elif C == 3:
                    self.inputdict["-pix_fmt"] = "rgb24"
                elif C == 4:
                    self.inputdict["-pix_fmt"] = "rgba"
                else:
                    raise NotImplemented

        self.bpp = bpplut[self.inputdict["-pix_fmt"]][1]
        self.inputNumChannels = bpplut[self.inputdict["-pix_fmt"]][0]
        bitpercomponent = self.bpp // self.inputNumChannels
        if bitpercomponent == 8:
            self.dtype = np.dtype('u1')  # np.uint8
        elif bitpercomponent == 16:
            suffix = self.inputdict['-pix_fmt'][-2:]
            if suffix == 'le':
                self.dtype = np.dtype('<u2')
            elif suffix == 'be':
                self.dtype = np.dtype('>u2')
        else:
            raise ValueError(self.inputdict['-pix_fmt'] + 'is not a valid pix_fmt for numpy conversion')

        assert self.inputNumChannels == C, "Failed to pass the correct number of channels %d for the pixel format %s." % (
            self.inputNumChannels, self.inputdict["-pix_fmt"])

        if ("-s" in self.inputdict):
            widthheight = self.inputdict["-s"].split('x')
            self.inputwidth = int(widthheight[0])
            self.inputheight = int(widthheight[1])
        else:
            self.inputdict["-s"] = str(N) + "x" + str(M)
            self.inputwidth = N
            self.inputheight = M

        # prepare output parameters, if raw
        if self.extension == ".yuv":
            if "-pix_fmt" not in self.outputdict:
                self.outputdict["-pix_fmt"] = self.DEFAULT_OUTPUT_PIX_FMT
                if self.verbosity > 0:
                    warnings.warn("No output color space provided. Assuming {}.".format(self.DEFAULT_OUTPUT_PIX_FMT),
                                  UserWarning)

        self._createProcess(self.inputdict, self.outputdict, self.verbosity)

    def _createProcess(self, inputdict, outputdict, verbosity):
        pass

    def _prepareData(self, data):
        return data  # general case : do nothing

    def _start_stdout_drain_thread(self):
        """Drain ffmpeg stdout into ``self._memory_dest`` in a background thread.

        Used only for memory destinations (issue #113 write-side). The
        thread reads stdout in 64KB chunks until EOF, copies each chunk
        into the user's buffer, and stores any exception in
        ``self._stdout_drain_error`` so ``close()`` can re-raise it from
        the main thread.

        Without continuous draining, ffmpeg would block once stdout's
        ~64KB pipe buffer filled — deadlocking the writer.
        """
        stdout = self._proc.stdout
        dest = self._memory_dest

        def _drain():
            try:
                while True:
                    chunk = stdout.read(64 * 1024)
                    if not chunk:
                        break
                    dest.write(chunk)
            except Exception as exc:
                self._stdout_drain_error = exc

        self._stdout_drain_thread = threading.Thread(
            target=_drain, daemon=True, name="skvideo-stdout-drain"
        )
        self._stdout_drain_thread.start()

    def close(self):
        """Closes the video and terminates FFmpeg process

        Raises ``RuntimeError`` if FFmpeg exited with a non-zero return
        code, including its stderr output in the exception message (issue
        #111). Previously a failing encode produced a silent empty/corrupt
        output file with no indication of what went wrong.
        """
        if self._proc is None:  # pragma: no cover
            return  # no process
        if self._proc.poll() is not None:
            return  # process already dead

        if self._dest_kind == "memory":
            # Memory destination: stdout is owned by the drain thread. We
            # close stdin to tell ffmpeg "no more frames", wait for ffmpeg
            # to flush + exit, then join the drain thread to be sure the
            # last bytes landed in the user's buffer. communicate() can't
            # be used here because it would also try to read stdout.
            if self._proc.stdin and not self._proc.stdin.closed:
                self._proc.stdin.close()
            self._proc.wait()
            if self._stdout_drain_thread is not None:
                self._stdout_drain_thread.join(timeout=30)
            stderr_data = b""
            if self._proc.stderr is not None:
                try:
                    stderr_data = self._proc.stderr.read() or b""
                except Exception:
                    pass
            returncode = self._proc.returncode
            self._proc = None
            self.DEVNULL.close()
            if self._stdout_drain_error is not None:
                # The drain thread crashed; surface that ahead of the
                # ffmpeg exit code, which is likely a side effect.
                raise RuntimeError(
                    "BytesIO destination write failed: %r" % self._stdout_drain_error
                )
            if returncode != 0:
                msg = "FFmpeg exited with code %d" % returncode
                if stderr_data:
                    msg += ":\n" + stderr_data.decode(errors='replace')
                raise RuntimeError(msg)
            return

        # File / URL destination: communicate() closes stdin, then drains
        # stdout/stderr while waiting — this avoids the deadlock that
        # wait() would hit if FFmpeg's stderr pipe filled. When stderr is
        # None (verbosity>0), the second tuple element is None and we have
        # nothing to surface. Don't call stdin.close() ourselves first:
        # communicate() flushes stdin and raises ValueError if it's
        # already closed.
        _, stderr_data = self._proc.communicate()
        returncode = self._proc.returncode
        self._proc = None
        self.DEVNULL.close()
        if returncode != 0:
            msg = "FFmpeg exited with code %d" % returncode
            if stderr_data:
                msg += ":\n" + stderr_data.decode(errors='replace')
            raise RuntimeError(msg)

    def writeFrame(self, im):
        """Sends ndarray frames to FFmpeg

        """
        vid = vshape(im)
        T, M, N, C = vid.shape
        if not self.warmStarted:
            self._warmStart(M, N, C, im.dtype)

        vid = vid.clip(0, (1 << (self.dtype.itemsize << 3)) - 1).astype(self.dtype)
        vid = self._prepareData(vid)
        T, M, N, C = vid.shape  # in case of hack ine prepareData to change the image shape (gray2RGB in libAV for exemple)

        # check if we need to do some bit-plane swapping
        # for the raw data format
        if self.inputdict["-pix_fmt"].startswith('yuv444p') or self.inputdict["-pix_fmt"].startswith('yuvj444p') or \
                self.inputdict["-pix_fmt"].startswith('yuva444p'):
            vid = vid.transpose((0, 3, 1, 2))

        # Check size of image
        if M != self.inputheight or N != self.inputwidth:
            raise ValueError('All images in a movie should have same size')
        if C != self.inputNumChannels:
            raise ValueError('All images in a movie should have same '
                             'number of channels')

        assert self._proc is not None  # Check status

        # Write
        try:
            self._proc.stdin.write(vid.tobytes())
        except IOError as e:
            # Surface FFmpeg's stderr alongside the broken-pipe error so the
            # user sees what FFmpeg actually rejected (e.g. bad codec, bad
            # pixel format), not just "Broken pipe" (issue #111).
            stderr_data = b''
            if self._proc.stderr is not None:
                try:
                    stderr_data = self._proc.stderr.read() or b''
                except Exception:
                    pass
            msg = '{0:}\n\nFFMPEG COMMAND:\n{1:}'.format(e, self._cmd)
            if stderr_data:
                msg += '\n\nFFMPEG STDERR OUTPUT:\n' + stderr_data.decode(errors='replace')
            raise IOError(msg)

    def _getSupportedEncoders(self):
        return NotImplemented

    def _dict2Args(self, dict):
        # Flatten {key: value} into [key, value, ...].
        # If value is a list/tuple, repeat the key for each entry — this is
        # how ffmpeg flags like `-metadata key1=val1 -metadata key2=val2`
        # are expressed (issue #168).
        args = []
        for key, value in dict.items():
            if isinstance(value, (list, tuple)):
                if len(value) == 0:
                    raise ValueError(
                        "Empty list/tuple for flag %r in ffmpeg dict — "
                        "silently dropping the flag would hide a programmer "
                        "error. Pass at least one value, or omit the key." % key
                    )
                for v in value:
                    args.append(key)
                    args.append(v)
            else:
                args.append(key)
                args.append(value)
        return args

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
