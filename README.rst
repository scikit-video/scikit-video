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
scipy, numpy, and FFmpeg.

This project is distributed under the 3-clause BSD.

Visit the documentation at http://www.scikit-video.org


Dependencies and Installation
-----------------------------

Requirements:

- FFmpeg >= 2.8 on the system PATH (primary tested backend). The libav/avconv
  backend is retained in the codebase for compatibility but is not validated
  by the test suite.
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


What's new in 1.1.14
--------------------

scikit-video is actively maintained again. The 1.1.12–1.1.14 line modernizes
the package for current Python (3.10–3.13), NumPy 2.x, and SciPy, with **no
breaking API changes** — code that worked with 1.1.11 should continue to work
unchanged. Highlights of 1.1.14:

- **Non-local I/O.** ``vread`` / ``vreader`` / ``vwrite`` and the
  ``FFmpegReader`` / ``FFmpegWriter`` constructors now accept file paths, URL
  strings (``http://``, ``https://``, ``rtsp://``, ...), and file-like objects
  (``io.BytesIO``) interchangeably (issues #117, #113, #81). A ``UserWarning``
  is emitted if a URL scheme isn't compiled into the local FFmpeg build.
- **Python-3 correctness pass.** Fixed several public functions that crashed on
  modern Python (e.g. ``measure.Li3DDCT_features``, ``utils.canny``,
  ``motion.globalEdgeMotion``, ``from skvideo import *``), replaced
  ``assert``-based input validation with real exceptions (so it survives
  ``python -O``), and made probe failures warn instead of silently returning
  empty metadata.
- **Earlier in the 1.1.12–1.1.13 line:** ``pyproject.toml`` packaging (restores
  ``pip install`` on modern Python/NumPy), ``pathlib.Path`` support everywhere,
  audio passthrough (``audiosrc=``) and multi-stream ``ffprobe`` in the writer,
  repeated-flag dict values, and a windowed-read ``start_frame`` argument.

See ``CHANGELOG.rst`` for the complete per-version history.


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


Copyright 2015-2026, scikit-video developers (BSD license).
