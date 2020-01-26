.. _anomalyexample:

Detecting anomalies
----------------------------------------------

We can train a predictor based on various videos to give us a prediction, for each frame, of the next frame.
By comparing the predicted frames for a video with the actual frames, we can flag anything in the video that is anomalous according to the training.
As a simple example, we can train on a single video and use that video as the basis for prediction --- so the only anomalies flagged will be frames that are anomalous within the video itself.

.. literalinclude:: anomaly_detect.py
   :linenos:

Here we use PredNet by coxlab, but we can substitute any video-prediction engine; you can roll your own using scikit-learn, for example.

Since the video we use in this example contains scene changes, naturally those scene changes are the most unusual frame-transitions in the video, since there are very few scene changes compared to the number of frames in the video. The anomaly detection functions as a crude form of scene detection in this case, although the second scene change does not jump out using this general-purpose method, and the first only barely. A special-purpose scene-detection method naturally works better; see :ref:`sceneexample`.

.. raw:: html 

   <center><video controls width=75% src="../images/anomaly_detection.mpg"></video></center> 
