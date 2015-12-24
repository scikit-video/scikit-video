sphinxcontrib.youtube
=====================

This module defines a directive, `youtube`.  It takes a single, required
argument, a YouTube video ID::

    ..  youtube:: oHg5SJYRHA0

The referenced video will be embedded into HTML output.  By default, the
embedded video will be sized for 720p content.  To control this, the
parameters "aspect", "width", and "height" may optionally be provided::

    ..  youtube:: oHg5SJYRHA0
        :width: 640
        :height: 480

    ..  youtube:: oHg5SJYRHA0
        :aspect: 4:3

    ..  youtube:: oHg5SJYRHA0
        :width: 100%

    ..  youtube:: oHg5SJYRHA0
        :height: 200px

..  -*- mode: rst; fill-column: 72 -*-
