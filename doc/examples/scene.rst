.. _sceneexample:

Detecting scene boundaries
----------------------------------------------

For this example, the luminance and edge-based scene detection algorithms are compared.

.. literalinclude:: scene_parse.py
   :linenos:

Video output shows that the luminance scene detector captures all the scene changes in this particular video:

.. raw:: html 

   <center><video controls width=75% src="../_static/scene_cuts.mp4"></video></center>
