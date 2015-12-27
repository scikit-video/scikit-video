.. _input-output:

===========================
Reading and Writing Videos
===========================

.. currentmodule:: skvideo.io

:mod:`skvideo.io` is a module created for using the FFmpeg 
backend to read and write videos. The mediainfo tool is used
for parsing metadata from videos, since it provides a universal 
format. In time, other backends are planned, but for now only FFmpeg
is officially supported.


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
	videogen = skvideo.io.vread_generator(skvideo.datasets.bigbuckbunny())
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

	writer = skvideo.io.FFmpegWriter("outputvideo.mp4", (5, 480, 640, 3))
	for i in xrange(5):
		writer.writeFrame(outputdata[i, :, :, :])
	writer.close()


Probing
-----------------------

Use :func:`skvideo.io.mprobe` to probe videos about their metadata. As below:

.. code-block:: python

	import skvideo.io
	import skvideo.datasets
	import json
	metadata = skvideo.io.mprobe(skvideo.datasets.bigbuckbunny())
	print(metadata.keys())
	print(json.parse(metadata["Video"], indent=4))

:func:`skvideo.io.mprobe` returns a dictionary, which can be passed into json.parse for pretty printing. See the below output:

.. code-block:: python

	[u'Audio', u'Video', u'General']
	{
	    "@type": "Video", 
	    "Count": "323", 
	    "Count_of_stream_of_this_kind": "1", 
	    "Kind_of_stream": [
		"Video", 
		"Video"
	    ], 
	    "Stream_identifier": "0", 
	    "StreamOrder": "0", 
	    "ID": [
		"1", 
		"1"
	    ], 
	    "Format": "AVC", 
	    "Format_Info": "Advanced Video Codec", 
	    "Format_Url": "http://developers.videolan.org/x264.html", 
	    "Commercial_name": "AVC", 
	    "Format_profile": "Main@L3.1", 
	    "Format_settings": "CABAC / 1 Ref Frames", 
	    "Format_settings__CABAC": [
		"Yes", 
		"Yes"
	    ], 
	    "Format_settings__ReFrames": [
		"1", 
		"1 frame"
	    ], 
	    "Internet_media_type": "video/H264", 
	    "Codec_ID": "avc1", 
	    "Codec_ID_Info": "Advanced Video Coding", 
	    "Codec_ID_Url": "http://www.apple.com/quicktime/download/standalone.html", 
	    "Codec": [
		"AVC", 
		"AVC"
	    ], 
	    "Codec_Family": "AVC", 
	    "Codec_Info": "Advanced Video Codec", 
	    "Codec_Url": "http://developers.videolan.org/x264.html", 
	    "Codec_CC": "avc1", 
	    "Codec_profile": "Main@L3.1", 
	    "Codec_settings": "CABAC / 1 Ref Frames", 
	    "Codec_settings__CABAC": "Yes", 
	    "Codec_Settings_RefFrames": "1", 
	    "Duration": [
		"5280", 
		"5s 280ms", 
		"5s 280ms", 
		"5s 280ms", 
		"00:00:05.280", 
		"00:00:05:07", 
		"00:00:05.280 (00:00:05:07)"
	    ], 
	    "Bit_rate": [
		"1205959", 
		"1 206 Kbps"
	    ], 
	    "Width": [
		"1280", 
		"1 280 pixels"
	    ], 
	    "Height": [
		"720", 
		"720 pixels"
	    ], 
	    "Sampled_Width": "1280", 
	    "Sampled_Height": "720", 
	    "Pixel_aspect_ratio": "1.000", 
	    "Display_aspect_ratio": [
		"1.778", 
		"16:9"
	    ], 
	    "Rotation": "0.000", 
	    "Frame_rate_mode": [
		"CFR", 
		"Constant"
	    ], 
	    "FrameRate_Mode_Original": "VFR", 
	    "Frame_rate": [
		"25.000", 
		"25.000 fps"
	    ], 
	    "Frame_count": "132", 
	    "Resolution": [
		"8", 
		"8 bits"
	    ], 
	    "Colorimetry": "4:2:0", 
	    "Color_space": "YUV", 
	    "Chroma_subsampling": "4:2:0", 
	    "Bit_depth": [
		"8", 
		"8 bits"
	    ], 
	    "Scan_type": [
		"Progressive", 
		"Progressive"
	    ], 
	    "Interlacement": [
		"PPF", 
		"Progressive"
	    ], 
	    "Bits__Pixel_Frame_": "0.052", 
	    "Stream_size": [
		"795933", 
		"777 KiB (75%)", 
		"777 KiB", 
		"777 KiB", 
		"777 KiB", 
		"777.3 KiB", 
		"777 KiB (75%)"
	    ], 
	    "Proportion_of_this_stream": "0.75391", 
	    "Encoded_date": "UTC 1970-01-01 00:00:00", 
	    "Tagged_date": "UTC 1970-01-01 00:00:00"
	}

.. toctree::
    :hidden:
