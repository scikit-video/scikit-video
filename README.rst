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


What's new in 1.2
-----------------

scikit-video is actively maintained again.

- **Metric accuracy overhaul (1.2.0).** The NIQE, BRISQUE, VIIDEO, and
  Video-BLIINDS implementations were validated against their reference
  MATLAB implementations and fixed where they diverged (reference NIQE
  model, antialiased half-scale resize, faithful VIIDEO port, motion
  tie-breaking). **Breaking: these four metrics return different --
  more accurate -- values than 1.1.x.** Scores and features are not
  comparable across the 1.1.x/1.2.x boundary. Function signatures are
  unchanged. MSE/PSNR/SSIM/MS-SSIM and ST-RRED were validated as already
  correct and are unchanged.
- **Maintenance (1.2.1).** NumPy 2.5 compatibility (``linalg.eig`` now
  always returns complex; symmetric eigendecompositions use ``eigh``),
  the unused ``opencv-python-headless`` dependency removed, FFmpeg
  version/binary detection fixes, and clearer errors on bad ``backend=``
  names and unsupported channel counts.
- **The 1.1.12–1.1.15 line** modernized the package for current Python
  (3.10+), NumPy 2.x, and SciPy with no breaking API changes: modern
  ``pyproject.toml`` packaging, non-local I/O (URLs and file-like
  objects), ``pathlib.Path`` support, audio passthrough (``audiosrc=``),
  a Python-3 correctness pass, and exception-based input validation.

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
