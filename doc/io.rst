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

To write an ndarray to a video file, use :func:`skvideo.io.write`

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
	for i in xrange(5):
		writer.writeFrame(outputdata[i, :, :, :])
	writer.close()


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
