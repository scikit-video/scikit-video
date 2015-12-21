.. _motion:

===========================
Motion
===========================

.. currentmodule:: sklearn.motion

`sklearn.motion` is a module currently supporting block motion estimation and compensation routines.


Block motion
-----------------------

To estimate a block motion field, simply use :func:`sklearn.motion.blockMotion`

.. code-block:: python

	import skvideo.io
	import skvideo.motion
	import skvideo.datasets

	videodata = skvideo.io.vread(skvideo.datasets.bigbuckbunny())
	
	motion = skvideo.motion.blockMotion(videodata)

	print(videodata.shape)
	print(motion.shape)

Output:

.. code-block:: python

	todo

By default, :func:`sklearn.motion.blockMotion` uses 8x8 pixel macroblocks and the diamond search algorithm.


Block motion compensation
-----------------------

Use :func:`sklearn.motion.blockComp` to use the computed block motion vectors for motion compensation

.. code-block:: python

	import skvideo.io
	import skvideo.motion
	import skvideo.datasets

	# compute vectors from bigbuckbunny
	videodata = skvideo.io.vread(skvideo.datasets.bigbuckbunny())
	motion = skvideo.motion.blockMotion(videodata)

	# compensate the video
	compmotion = skvideo.motion.blockComp(videodata, motion)

Here is bigbuckbunny when each frame is motion compensated


.. toctree::
    :hidden:
