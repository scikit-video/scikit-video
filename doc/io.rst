.. _input-output:

===========================
Reading and Writing Videos
===========================

.. currentmodule:: skvideo.io

:mod:`skvideo.io` is a module created for using a FFmpeg/LibAV 
backend to read and write videos. Depending on the available backend, the 
appropriate probing tool (ffprobe, avprobe, or even mediainfo) will be
used to parse metadata from videos.

Reading
-----------------------

Use :func:`skvideo.io.vread` to load any video (here `bigbuckbunny`) into memory as a single ndarray. Note that this function assumes you have enough memory to do so, and should only be used for small videos.

.. code-block:: python

	import skvideo.io
	import skvideo.datasets
	videodata = skvideo.io.vread(skvideo.datasets.bigbuckbunny())
	print(videodata.shape)

Running this code prints:

.. code-block:: python

	(132, 720, 1280, 3)

Use :func:`skvideo.io.vreader` to load any video (here `bigbuckbunny`) frame-by-frame. This is the function to be used for larger files, and is actually faster than loading a video as 1 ndarray. However, it requires handling each frame as it is loaded. An example snippet:

.. code-block:: python

	import skvideo.io
	import skvideo.datasets
	videogen = skvideo.io.vreader(skvideo.datasets.bigbuckbunny())
	for frame in videogen:
		print(frame.shape)

The output:

.. code-block:: python

	(720, 1280, 3)
	(720, 1280, 3)
	     ...
	     ...
	     ...
	(720, 1280, 3)

Sometimes, particular use cases require fine tuning FFmpeg's reading parameters. For this, you can use :class:`skvideo.io.FFmpegReader`  

.. code-block:: python

	import numpy as np
	import skvideo.io
	import skvideo.datasets

	# here you can set keys and values for parameters in ffmpeg
	inputparameters = {}
	outputparameters = {}
	reader = skvideo.io.FFmpegReader(skvideo.datasets.bigbuckbunny(), 
			inputdict=inputparameters,
			outputdict=outputparameters)

	# iterate through the frames
	accumulation = 0
	for frame in reader.nextFrame():
		# do something with the ndarray frame
		accumulation += np.sum(frame)

For example, FFmpegReader will by default return an RGB representation of a video file, but you may want some other color space that FFmpeg supports, by setting appropriate key/values in outputparameters. Since FFmpeg output is piped into stdin, all FFmpeg commands can be used here.

inputparameters may be useful for raw video which has no header information. Then you should FFmpeg exactly how to interpret your data.


Writing
-----------------------

To write an ndarray to a video file, use :func:`skvideo.io.vwrite`

.. code-block:: python

	import skvideo.io	
	import numpy as np

	outputdata = np.random.random(size=(5, 480, 680, 3)) * 255
	outputdata = outputdata.astype(np.uint8)

	skvideo.io.vwrite("outputvideo.mp4", outputdata)

Often, writing videos requires fine tuning FFmpeg's writing parameters to select encoders, framerates, bitrates, etc. For this, you can use :class:`skvideo.io.FFmpegWriter`

.. code-block:: python

	import skvideo.io	
	import numpy as np

	outputdata = np.random.random(size=(5, 480, 680, 3)) * 255
	outputdata = outputdata.astype(np.uint8)

	writer = skvideo.io.FFmpegWriter("outputvideo.mp4")
	for i in range(5):
		writer.writeFrame(outputdata[i, :, :, :])
	writer.close()


Tuning FFmpeg Parameters
------------------------

``inputdict`` and ``outputdict`` are plain Python dicts whose keys are
FFmpeg command-line flags (including the leading ``-``) and whose values
are the argument FFmpeg expects after that flag. Both keys and values are
strings; scikit-video passes them through verbatim to ``ffmpeg``. The
complete reference for valid flags is FFmpeg's own documentation:
https://ffmpeg.org/ffmpeg.html.

``inputdict`` parameters are placed *before* the input file on the FFmpeg
command line (they describe how to interpret the input), and ``outputdict``
parameters are placed *after* (they describe what to do on the way out).

.. note::

   ``FFmpegWriter`` feeds your NumPy frames to FFmpeg as headerless
   ``rawvideo`` over a pipe, so the stream carries no framerate of its
   own (FFmpeg assumes 25 fps unless told otherwise). To set the
   framerate of the written video, put ``-r`` in **inputdict**, not
   ``outputdict``. ``-r`` before ``-i`` declares the framerate of the
   incoming frames; ``-r`` after ``-i`` (i.e. in ``outputdict``) is a
   *resampler* that drops or duplicates frames relative to the input
   rate. Setting only ``outputdict["-r"]`` resamples against the
   assumed 25 fps and produces the wrong duration. (This is the reverse
   of ``FFmpegReader``, whose input is a real container with its own
   framerate header, so resampling on the output side is the natural
   knob there.)

**Common reading recipes**

Force a different output pixel format (default is ``rgb24``):

.. code-block:: python

    reader = skvideo.io.FFmpegReader(
        "in.mp4",
        outputdict={"-pix_fmt": "gray"},
    )

Resize during decoding (FFmpeg handles the scaling, faster than NumPy):

.. code-block:: python

    reader = skvideo.io.FFmpegReader(
        "in.mp4",
        outputdict={"-s": "640x360"},
    )

Read a raw YUV file with no header (size and format must be supplied):

.. code-block:: python

    reader = skvideo.io.FFmpegReader(
        "in.yuv",
        inputdict={"-pix_fmt": "yuv420p", "-s": "1280x720"},
    )

**Common writing recipes**

Pick a specific codec, bitrate, and framerate. Note ``-r`` (the
framerate of the frames you write) goes in ``inputdict``; see the note
above:

.. code-block:: python

    writer = skvideo.io.FFmpegWriter(
        "out.mp4",
        inputdict={"-r": "30"},      # framerate of the written video
        outputdict={
            "-vcodec": "libx264",
            "-b:v": "2000k",
        },
    )

Resample to a different framerate, i.e. write at a different rate than the
frames are produced (FFmpeg drops or duplicates frames as needed). Here
``inputdict["-r"]`` sets the source rate and ``outputdict["-r"]`` is the
resampler:

.. code-block:: python

    writer = skvideo.io.FFmpegWriter(
        "out.mp4",
        inputdict={"-r": "60"},      # rate of the frames you write
        outputdict={"-r": "30"},     # resample to this rate on output
    )

Write a high-quality H.264 with a constant rate factor:

.. code-block:: python

    writer = skvideo.io.FFmpegWriter(
        "out.mp4",
        outputdict={"-vcodec": "libx264", "-crf": "18", "-pix_fmt": "yuv420p"},
    )

Preserve an alpha (transparency) channel. Two things are required:
the codec/container must support alpha (H.264/``.mp4`` does **not**;
use FFV1 in ``.mkv``, or QTRLE or PNG in ``.mov``), and the output
``-pix_fmt`` must keep the alpha plane (e.g. ``rgba``):

.. code-block:: python

    # frames is an (T, H, W, 4) uint8 array
    writer = skvideo.io.FFmpegWriter(
        "out.mkv",
        inputdict={"-r": "10"},
        outputdict={"-vcodec": "ffv1", "-pix_fmt": "rgba"},
    )

When reading the file back, you must also ask for a 4-channel pixel
format — the reader defaults to ``rgb24`` and would otherwise silently
drop the alpha plane:

.. code-block:: python

    vid = skvideo.io.vread("out.mkv", outputdict={"-pix_fmt": "rgba"})
    # vid.shape == (T, H, W, 4)

VP9 in ``.webm`` can also carry alpha, but FFmpeg does not always
auto-select the alpha-aware decoder on read, so a plain ``rgba`` read may
come back fully opaque. Name the decoder explicitly to recover the alpha
plane: ``vread("out.webm", inputdict={"-vcodec": "libvpx-vp9"},
outputdict={"-pix_fmt": "rgba"})``.

**Repeating the same flag** (e.g. multiple ``-metadata`` or ``-map``
entries) is done with a list value — scikit-video emits the flag once per
list element:

.. code-block:: python

    writer = skvideo.io.FFmpegWriter(
        "out.mp4",
        outputdict={"-metadata": ["title=My Video", "artist=Me"]},
    )

**Fraction framerates** (such as NTSC ``30000/1001``) are accepted in
``inputdict["-r"]`` as of v1.1.13.

**Reading a frame window** (added in v1.1.13): to extract a slice of a
long video without loading the whole file, pass ``start_frame`` and
``num_frames`` to ``vread`` or ``vreader``:

.. code-block:: python

    # Frames 1000–1199 of a long clip, as a (200, H, W, 3) ndarray
    videodata = skvideo.io.vread("clip.mp4", start_frame=1000, num_frames=200)

This uses FFmpeg's fast keyframe-based ``-ss`` seek, so the first frame
returned may snap to the nearest keyframe at or before frame 1000. For
frame-exact extraction, drop ``start_frame`` and use a ``select`` filter
instead — slower because FFmpeg decodes from the start of the file:

.. code-block:: python

    skvideo.io.vread(
        "clip.mp4",
        outputdict={"-vf": "select='gte(n\\,1000)'", "-vsync": "0"},
        num_frames=200,
    )

Two details matter here. ``select`` is an *output* filter, so it goes in
``outputdict`` (after ``-i``); placing ``-vf`` in ``inputdict`` yields no
frames. And ``-vsync 0`` is required: ``select`` drops frames, and without
it FFmpeg re-pads the gaps back to a constant frame rate by duplicating
frames, which silently undoes the selection. With ``-vsync 0`` each
surviving frame is emitted exactly once. (On FFmpeg 5.1 and newer,
``-vsync 0`` is a deprecated alias for ``-fps_mode passthrough`` and may
print a deprecation notice; ``-vsync 0`` is used here because it works
across the FFmpeg versions scikit-video supports. On a recent-only
FFmpeg you can use ``"-fps_mode": "passthrough"`` instead.)

**Muxing audio from a separate source** (added in v1.1.12) uses the
``audiosrc`` constructor argument rather than ``inputdict``:

.. code-block:: python

    writer = skvideo.io.FFmpegWriter("out.mp4", audiosrc="source_with_audio.mp4")

See the :class:`skvideo.io.FFmpegWriter` API reference for the full
``audiosrc`` / ``-map`` interaction.


Remote and in-memory I/O
------------------------

As of v1.1.14, the I/O entry points accept three kinds of source/destination:

* a **file path** — string or ``pathlib.Path`` (existing behavior).
* a **URL string** — anything matching ``<scheme>://...``, such as
  ``http://``, ``https://``, ``rtsp://``, ``rtmp://``, ``udp://``,
  ``ftp://``, etc. FFmpeg's own protocol handlers take it from there.
* a **file-like object** — ``io.BytesIO``, an open file handle, anything
  with a ``.read()`` (for input) or ``.write()`` (for output) method.

Specifically:

* :func:`skvideo.io.vread`, :func:`skvideo.io.vreader`, and
  :class:`skvideo.io.FFmpegReader` accept all three on input.
* :func:`skvideo.io.vwrite` and :class:`skvideo.io.FFmpegWriter` accept
  all three on output.
* :func:`skvideo.io.ffprobe` accepts a file path or a URL string. It does
  **not** accept a file-like object — wrap the bytes in a
  ``NamedTemporaryFile`` and call ``ffprobe`` on the resulting path if
  you need metadata from in-memory bytes.

**Read from a URL:**

.. code-block:: python

    videodata = skvideo.io.vread("https://example.com/clip.mp4", num_frames=10)

``ffprobe`` is invoked against the URL directly to read metadata, which
adds network round-trip latency to ``FFmpegReader`` construction. For
high-volume use, consider downloading first or caching the probe result.

**Read from a BytesIO:**

.. code-block:: python

    import io
    raw_bytes = open("clip.mp4", "rb").read()
    buf = io.BytesIO(raw_bytes)
    videodata = skvideo.io.vread(buf, num_frames=10)

Memory inputs are spooled to a temporary file at construction so the rest
of the read path can operate on a regular filename (container formats
like mp4 need random access to read their header atoms, which subprocess
stdin can't reliably provide). The temp file is unlinked on
``reader.close()`` / when ``vread`` returns.

**Write to a URL** (e.g. RTMP push to a streaming server):

.. code-block:: python

    writer = skvideo.io.FFmpegWriter(
        "rtmp://live.example.com/stream/key",
        outputdict={"-f": "flv", "-vcodec": "libx264", "-preset": "ultrafast"},
    )
    for frame in frames:
        writer.writeFrame(frame)
    writer.close()

**Write to a BytesIO:**

.. code-block:: python

    import io
    out = io.BytesIO()
    skvideo.io.vwrite(out, videodata)
    out.seek(0)
    # `out` now contains a streamable fragmented-mp4 file

When writing to a memory destination and the caller doesn't override
``-f``, the wrapper defaults to ``-f mp4`` with
``-movflags frag_keyframe+empty_moov`` so the bytes can stream as they're
produced (the default mp4 muxer would seek back to rewrite the moov atom
at end-of-encode, which a pipe can't support). To pick a different
streamable container, set ``-f`` explicitly:

.. code-block:: python

    out = io.BytesIO()
    writer = skvideo.io.FFmpegWriter(
        out,
        outputdict={"-f": "webm", "-vcodec": "libvpx-vp9", "-b:v": "1M"},
    )

**Protocol detection.** On first URL use, ``skvideo`` runs
``ffmpeg -protocols`` and caches the result. If the URL's scheme isn't in
the local ffmpeg's supported list (most commonly: an ffmpeg built without
OpenSSL hitting an ``https://`` URL), a ``UserWarning`` is emitted so the
underlying problem is obvious. FFmpeg's actual stderr (now surfaced via
``RuntimeError`` since v1.1.13) still reports the real failure if you
proceed.


Reading Video Metadata
-----------------------

Use :func:`skvideo.io.ffprobe` to find video metadata. As below:

.. code-block:: python

	import skvideo.io
	import skvideo.datasets
	import json
	metadata = skvideo.io.ffprobe(skvideo.datasets.bigbuckbunny())
	print(metadata.keys())
	print(json.dumps(metadata["video"], indent=4))

:func:`skvideo.io.ffprobe` returns a dictionary, which can be passed into json.dumps for pretty printing. See the below output:

.. code-block:: python

    [u'audio', u'video']
    {
        "@index": "0", 
        "@codec_name": "h264", 
        "@codec_long_name": "H.264 / AVC / MPEG-4 AVC / MPEG-4 part 10", 
        "@profile": "Main", 
        "@codec_type": "video", 
        "@codec_time_base": "1/50", 
        "@codec_tag_string": "avc1", 
        "@codec_tag": "0x31637661", 
        "@width": "1280", 
        "@height": "720", 
        "@coded_width": "1280", 
        "@coded_height": "720", 
        "@has_b_frames": "0", 
        "@sample_aspect_ratio": "1:1", 
        "@display_aspect_ratio": "16:9", 
        "@pix_fmt": "yuv420p", 
        "@level": "31", 
        "@chroma_location": "left", 
        "@refs": "1", 
        "@is_avc": "1", 
        "@nal_length_size": "4", 
        "@r_frame_rate": "25/1", 
        "@avg_frame_rate": "25/1", 
        "@time_base": "1/12800", 
        "@start_pts": "0", 
        "@start_time": "0.000000", 
        "@duration_ts": "67584", 
        "@duration": "5.280000", 
        "@bit_rate": "1205959", 
        "@bits_per_raw_sample": "8", 
        "@nb_frames": "132", 
        "disposition": {
            "@default": "1", 
            "@dub": "0", 
            "@original": "0", 
            "@comment": "0", 
            "@lyrics": "0", 
            "@karaoke": "0", 
            "@forced": "0", 
            "@hearing_impaired": "0", 
            "@visual_impaired": "0", 
            "@clean_effects": "0", 
            "@attached_pic": "0"
        }, 
        "tag": [
            {
                "@key": "creation_time", 
                "@value": "1970-01-01 00:00:00"
            }, 
            {
                "@key": "language", 
                "@value": "und"
            }, 
            {
                "@key": "handler_name", 
                "@value": "VideoHandler"
            }
        ]
    }

.. toctree::
    :hidden:
