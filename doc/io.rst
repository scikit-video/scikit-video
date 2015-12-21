.. _input-output:

Reading and Writing Videos
-----------------------

.. currentmodule:: sklearn.io

`sklearn.io` is a module created for using the FFmpeg 
backend to read and write videos. The mediainfo tool is used
for parsing metadata from videos, since it provides a universal 
format. 

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

.. toctree::
    :hidden:
