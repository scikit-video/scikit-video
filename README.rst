.. -*- mode: rst -*-

|skvideologo|_

|BSD3|_ |Tests|_ |PyPi|_ |PythonVersions|_

.. |BSD3| image:: https://img.shields.io/badge/license-BSD--3--Clause-blue.svg
.. _BSD3: https://opensource.org/licenses/BSD-3-Clause

.. |Tests| image:: https://github.com/scikit-video/scikit-video/actions/workflows/tests.yml/badge.svg
.. _Tests: https://github.com/scikit-video/scikit-video/actions/workflows/tests.yml

.. |PyPi| image:: https://badge.fury.io/py/scikit-video.svg
.. _PyPi: https://badge.fury.io/py/scikit-video

.. |PythonVersions| image:: https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue.svg
.. _PythonVersions: https://pypi.org/project/scikit-video/

.. |skvideologo| image:: doc/images/scikit-video.png
.. _skvideologo: http://www.scikit-video.org


Video Processing SciKit
-----------------------

Borrowing coding styles and conventions from scikit-image and scikit-learn,
scikit-video is a Python module for video processing built on top of
scipy, numpy, and ffmpeg/libav.

This project is distributed under the 3-clause BSD.

Visit the documentation at http://www.scikit-video.org


Dependencies and Installation
-----------------------------

Requirements:

- Either FFmpeg (version >= 2.8) or libav (version 10 or 11) — installed on the system PATH
- Python >= 3.10
- numpy >= 1.22
- scipy >= 1.9
- Pillow >= 9.0
- opencv-python-headless >= 4.5 (required by ``skvideo.measure``)
- mediainfo (optional)

Installation from PyPI::

    pip install scikit-video

Installation from source (GitHub)::

    git clone https://github.com/scikit-video/scikit-video.git
    cd scikit-video
    pip install .

For development (editable install with test dependencies)::

    pip install -e ".[test]"


Known conflicts
---------------

If you installed scikit-video prior to version 1.1.10, you may have an import
conflict with the older ``sk-video`` package. Run the following to fix it::

    pip uninstall sk-video

Then check that ``skvideo`` resolves to the expected location::

    import skvideo
    print(skvideo.__file__)


What's new in 1.1.12
--------------------

This release modernizes scikit-video to work with current Python, NumPy, and
SciPy. There are **no breaking API changes**; existing code that worked with
1.1.11 should continue to work unchanged. Three new opt-in additions are
described below.

Compatibility and packaging
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Replaced ``setup.py`` / ``numpy.distutils`` packaging with a ``pyproject.toml``
  using standard setuptools. This restores ``pip install`` on Python 3.12+ and
  NumPy >= 1.26, which removed ``numpy.distutils``.
- Replaced deprecated ``ndarray.tostring()`` with ``tobytes()`` for NumPy 2.x
  compatibility (issue #181, PR #182).
- Removed vestigial ``scipy.misc`` imports that broke on SciPy >= 1.12, and
  switched ``stpyr`` to ``scipy.special.factorial`` (the long-time successor to
  ``scipy.misc.factorial``).
- Dropped support for Python 2.7 and Python <= 3.9. Supported Python versions
  are now 3.10, 3.11, 3.12, and 3.13.
- ``opencv-python-headless`` is now declared as a hard dependency so that
  ``import skvideo.measure`` works on a fresh install (previously a hidden
  requirement).
- Replaced the dead ``nose`` test runner with ``pytest``.
- Replaced Travis CI / CircleCI configuration with a GitHub Actions workflow
  that runs the test suite on Linux and macOS across Python 3.10–3.13.

New opt-in features
~~~~~~~~~~~~~~~~~~~

- **Audio passthrough in ``vwrite`` / ``FFmpegWriter``** (issues #173, #176).
  Pass ``audiosrc='source.mp4'`` to mux the first audio stream from a source
  file into the output. Default is lossless stream-copy
  (``-c:a copy -shortest``); override with ``outputdict={'-c:a': 'aac'}``
  to re-encode, or ``outputdict={'-map': '1:a'}`` to keep all source audio
  streams instead of just the first. Missing or audio-less ``audiosrc`` paths
  raise at construction time rather than producing a silent videoless output.
- **Multi-stream ``ffprobe`` support** (issue #165). Returned metadata dict
  now always includes ``audio_streams`` and ``video_streams`` lists (empty
  list when none), in addition to the existing single-stream ``audio`` and
  ``video`` keys. Use the plural keys for files with multiple audio or video
  streams.
- **Repeated ffmpeg flags via list values** (issue #168). ``outputdict`` and
  ``inputdict`` accept ``list``/``tuple`` values to emit a flag multiple
  times. Example: ``outputdict={'-metadata': ['title=foo', 'artist=bar']}``
  produces ``-metadata title=foo -metadata artist=bar`` on the ffmpeg command
  line. Empty list values raise ``ValueError`` to surface programmer errors
  early.


TODO/Roadmap
------------
- Spatial-Temporal filtering helper functions
- Speedup routines (using cython and/or opencl)
- More ffmpeg/avconv interfacing
- Add additional algorithms and maintain more comprehensive benchmarks


For Contributors
----------------

See ``CONTRIBUTING.rst`` for setup instructions.


Testing
-------

After installing with the ``[test]`` extra, run the suite with::

    pytest -v skvideo/tests

Tests that require FFmpeg or libav are automatically skipped if the
corresponding binary is not on the system PATH.


Copyright 2015-2025, scikit-video developers (BSD license).
