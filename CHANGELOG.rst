1.1.12 (unreleased)
-------------------
- Replaced setup.py / numpy.distutils packaging with pyproject.toml + setuptools.
  Restores ``pip install`` compatibility with Python 3.12+ and NumPy >= 1.26.
- Replaced deprecated ``ndarray.tostring()`` with ``tobytes()`` (NumPy 2.x; PR #182).
- Removed vestigial ``scipy.misc`` imports left behind by PR #177; switched
  ``skvideo.utils.stpyr`` to ``scipy.special.factorial`` (SciPy >= 1.3).
- Declared ``opencv-python-headless`` as a hard dependency so
  ``import skvideo.measure`` works on a fresh install.
- Dropped Python 2.7 and Python <= 3.9 support. Now supports Python 3.10–3.13.
- Migrated tests from nose to pytest.
- Replaced Travis CI / CircleCI configs with a GitHub Actions workflow.
- ``inputdict`` / ``outputdict`` flag values can now be lists/tuples to emit
  the same flag repeatedly (e.g. ``{'-metadata': ['title=foo', 'artist=bar']}``
  becomes ``-metadata title=foo -metadata artist=bar``). Fixes #168.
- ``skvideo.io.ffprobe`` now exposes every stream of each codec type at
  ``info['<type>_streams']`` (e.g. ``info['audio_streams']``) in addition to
  the existing single-stream key. Fixes #165.
- ``FFmpegWriter`` and ``vwrite`` accept an ``audiosrc`` argument: a path to
  a media file whose audio is muxed into the output via ``-c:a copy`` and
  ``-shortest``. This restores audio across a ``vread`` / ``vwrite``
  passthrough. Fixes #173, #176.

1.1.11
------
- Year revision and product->prod naming cleanup; int8 -> int32 in motion estimation.

1.1.10
-----
- Adding BSD license file

1.1.9
-----
- Dropping ffmpeg 2.1 support
- removed libav warning when ffmpeg is already installed
- scene detector uses less memory

1.1.8
-----
- Added Video Bliinds and BRISQUE quality feature extractors
- Added ST-RRED, MS-SSIM, SSIM, NIQE, Video Oracle quality metrics
- Added initial windows support
- Added supporting unit tests
- Python3 compatibility patches
- Fixed assortment of bugs
- Fixed file descriptor deadlock when using too much data

1.1.7
-----
- Added scene detection, motion estimation, and miscellaneous examples
- Fixed bug of not closing FFmpeg when using vread/vreader
- Fixed bugs with scene detector and motion estimation

1.1.6
-----

- Added scene cut detection functions
- Added global motion estimation
- Added edge extraction, but only canny edge detection for now
- Added more examples to the documentation

1.1.5
1.1.4
-----

- Fixed issues with pypi

1.1.3
-----

- Fixed I/O bug with vreader and greyscale frames 
- Migrated markdown files to rst files

1.1.2
-----

- No longer testing git master of LibAV, since it presented instabilities 
- Updating index and FAQ pages in scikit-video docs
- Initial publishing to pypi under the name sk-video
- Initial changelog created
