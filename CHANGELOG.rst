1.1.16 (unreleased)
-------------------
NIQE accuracy fix.

- **NIQE now uses the reference pristine model** from the LIVE NIQE Software
  Release (Mittal, Soundararajan, Bovik, 2012), replacing a separately-trained
  model that correlated poorly with human judgement. On the LIVE IQA database,
  NIQE's Spearman correlation (SROCC) with DMOS improves from ~0.54 to ~0.84
  (779 distorted images); Gaussian-blur, which was effectively broken, goes
  from ~0.32 to ~0.93. The model is redistributed under its permissive license
  (see ``skvideo/measure/data/niqe_model_NOTICE.txt``).
- **Feature-extractor corrections** to match the reference NIQE algorithm:
  the diagonal (D1/D2) paired-product sub-bands now use their own right AGGD
  scale parameter instead of duplicating the left one; the MSCN normalization
  uses ``replicate`` border handling; and scale-2 downsampling uses an
  antialiased (PIL bicubic) resize instead of ``cv2`` cubic.
- **BREAKING:** NIQE output values change. Previous values were inaccurate, so
  scores are not comparable across this boundary.
- Measured LIVE SROCC is ~0.84 (was ~0.54), with per-distortion correlations of
  0.87-0.97 and Gaussian blur recovered to ~0.93. This is below the commonly
  cited ~0.91, but that figure reflects the official MATLAB LIVE evaluation
  protocol, not a better implementation: an independent, MATLAB-validated NIQE
  (BasicSR) evaluated on the same LIVE images yields the same ~0.83 SROCC,
  matching skvideo within 0.004 across all distortions. skvideo's NIQE is
  therefore a faithful implementation; the residual vs the published number is
  an evaluation-protocol difference (image/luma handling, DMOS), not a defect.

1.1.15 (2026-06-02)
-------------------
Correctness-completion pass continuing the v1.1.14 hardening:

- Remaining user-facing ``assert`` validation now raises real exceptions
  (survives ``python -O``): backend-availability checks (FFmpeg / libav /
  mediainfo and the libav version) raise ``RuntimeError``; ``mprobe`` XML-parse
  guards and the ``utils.mscn`` / ``utils.image`` input checks raise
  ``ValueError``. Only internal ``self._proc is not None`` invariants remain
  as asserts.
- ``ssim`` now raises ``ValueError`` for frames smaller than its 11x11 window
  instead of silently returning ``NaN``.
- Ported the last Python-2 ``xrange`` (``utils/stpyr.py``) to ``range``.
- Reading an empty or undecodable memory/file source via the count-frames
  fallback now raises a clear ``RuntimeError`` explaining the input is
  unreadable (and how to declare the frame count) instead of leaking a raw
  ``subprocess.CalledProcessError``.
- ``FFmpegReader.close`` now closes its pipe file objects even when ffmpeg has
  already exited (e.g. ``start_frame`` seeks past EOF), removing a spurious
  ``ResourceWarning``.
- Docs: corrected the full-reference metric reference from the removed ``mad``
  to ``mae`` in ``doc/measure.rst`` and the module autosummary.

1.1.14 (2026-06-02)
-------------------
- **Input source decoupling**: ``vread`` / ``vreader`` / ``vwrite`` and the
  ``FFmpegReader`` / ``FFmpegWriter`` constructors now accept three kinds
  of source/destination uniformly — a file path (existing behavior), a URL
  string (``http://``, ``https://``, ``rtsp://``, ``rtmp://``, ``udp://``,
  …), or a file-like object such as ``io.BytesIO``. The wrapper no longer
  blocks ffmpeg with filesystem-only checks (``os.path.getsize``,
  ``os.path.isfile``, ``os.access(W_OK)``) when the source isn't a local
  file. Closes #117, #113, #81 on the reader and writer paths. (Note:
  ``skvideo.io.ffprobe`` itself accepts URLs but not file-like objects;
  wrap to a ``NamedTemporaryFile`` if you need to probe in-memory bytes.)
- ``ffprobe`` is invoked against the URL directly for URL inputs, so probing
  is transparent. Note this incurs network latency on ``FFmpegReader``
  construction proportional to the URL's round-trip time.
- BytesIO / file-like inputs are spooled to a ``NamedTemporaryFile`` at
  construction so the rest of the read path (probe, extension heuristics,
  frame reader, ``start_frame`` seek) operates on a regular path. The
  spool is required for formats like mp4 whose moov atom needs random
  access. The temp file is unlinked in ``close()``.
- BytesIO / file-like outputs are written via ffmpeg's stdout (``pipe:1``)
  and drained by a background thread into the user's buffer. When the
  caller doesn't override ``-f``, the wrapper defaults to ``-f mp4`` with
  ``-movflags frag_keyframe+empty_moov`` so the output is streamable
  (the default mp4 muxer would otherwise seek back to write the moov atom,
  which a pipe can't support). Picking ``-f`` explicitly (webm, matroska,
  mpegts, …) is respected.
- **Protocol detection**: at first URL use, ``skvideo`` runs
  ``ffmpeg -protocols`` (cached for the rest of the session) and emits a
  ``UserWarning`` if the URL's scheme isn't compiled into the local
  ffmpeg build — typical case is an ffmpeg without OpenSSL hitting an
  ``https://`` URL. Warning rather than error; ffmpeg's actual stderr
  (now readable since v1.1.13) still surfaces the underlying problem.
  ``setFFmpegPath`` clears the protocol cache so a different binary
  triggers fresh detection.
- Documentation: I/O guide gains a "Remote and in-memory I/O" section
  covering URL inputs/outputs, BytesIO round-trip, the streaming-mp4
  default for memory destinations, and a note on ffprobe latency.
- Documentation fix: the "Tuning FFmpeg Parameters" writer recipe added in
  v1.1.13 incorrectly placed the output framerate in ``outputdict["-r"]``.
  Because ``FFmpegWriter`` feeds headerless ``rawvideo`` (assumed 25 fps),
  ``-r`` must go in ``inputdict`` to set the written video's framerate;
  ``outputdict["-r"]`` only resamples against the assumed input rate and
  yields the wrong duration. Recipes corrected and a note added explaining
  the input-vs-output ``-r`` asymmetry (and why it differs from
  ``FFmpegReader``). Reopens the documentation concern from #160/#96; see
  #186 (reported by page200).
- Documentation: added an alpha-channel (transparency) writing recipe to
  the I/O guide. Preserving alpha requires both an alpha-capable
  codec/container (FFV1/.mkv, or QTRLE or PNG/.mov; not H.264/.mp4) and
  reading back with ``outputdict={"-pix_fmt": "rgba"}``, since the reader
  defaults to ``rgb24`` and otherwise drops the alpha plane. VP9/.webm
  alpha is also documented with the caveat that the decoder may need to
  be named explicitly on read. Addresses the usage confusion in #143.
- Fixed a file-descriptor leak: ``FFmpegWriter.close()`` returned early
  without closing its ``DEVNULL`` handle when the writer was constructed
  but never warm-started (no frames written), e.g. URL/validation-only
  writers. ``close()`` now releases ``DEVNULL`` on every path.
- Fixed temp-file leaks on the BytesIO/file-like read path: spooling now
  unlinks its ``NamedTemporaryFile`` if the source read fails partway,
  and ``vread`` closes the reader in a ``finally`` so a mid-read error no
  longer leaks the spooled file. A file-like input without a ``read()``
  method is now rejected up front with a clear ``TypeError`` instead of
  failing deep inside the copy.
- Documentation fix: the frame-exact ``select`` recipe (and the
  ``start_frame`` docstring) placed ``-vf`` in ``inputdict``; ``-vf`` is
  an output filter and yields no frames there. Corrected to ``outputdict``
  and added the required ``-vsync 0`` (without it FFmpeg re-pads the
  frames ``select`` drops back to a constant rate, silently undoing the
  selection). Also added a missing ``import numpy as np`` to the reader
  example.
- ``vread`` now trims its result to the number of frames actually
  produced. When an output filter such as ``-vf select`` yields fewer
  frames than ``getShape()`` predicted from ``nb_frames``, the returned
  array previously kept the extra, uninitialized ``np.empty`` rows.
- The readable-input check for file-like sources is stricter: a file
  opened in write mode (``"wb"``) exposes a ``read`` attribute that
  raises when called, so it now fails the ``readable()`` probe and is
  rejected with a clear ``TypeError`` instead of an opaque
  ``io.UnsupportedOperation`` from inside the spool copy.

- **Python-3 correctness pass** (pre-existing defects found in a
  whole-codebase audit; none were introduced by the v1.1.14 work):

  - ``skvideo.measure.Li3DDCT_features`` raised ``NameError: name 'int32'
    is not defined`` on every call (bare ``int32`` instead of
    ``np.int32``) and produced no frame groups when ``T == 4``. Fixed
    both; the function now runs.
  - ``skvideo.utils.canny`` (used by ``globalEdgeMotion`` and scene
    detection) had the same bare ``int32`` ``NameError``. Fixed.
  - ``skvideo.motion.globalEdgeMotion`` was broken on Python 3: the bool
    edge-mask path was not squeezed to 2D, the hausdorff branch compared
    the shifted frame against itself instead of the reference frame, and
    an unknown method raised a misspelled ``Notimplemented``. All fixed;
    both ``hamming`` and ``hausdorff`` now recover a known translation.
  - ``skvideo.motion.blockComp`` dropped every bottom/right macroblock
    because ``_checkBounded`` rejected blocks ending exactly at the frame
    edge (``>=`` should have been ``>``). Motion compensation now covers
    the full frame.
  - ``from skvideo import *`` raised ``TypeError`` because the top-level
    ``__all__`` listed function objects instead of names. Fixed.
  - Library code no longer calls ``exit()`` or raises the ``NotImplemented``
    singleton: ``rgb2gray``, ``niqe`` and ``videobliinds`` helpers now
    raise proper exceptions.
  - Public input validation in the quality metrics (channel / frame-count
    / resolution checks) and in the I/O layer (unknown extension, unwritable
    output directory, channel/pixel-format mismatch) now raises
    ``ValueError`` / ``OSError`` instead of ``assert``, so it is no longer
    stripped under ``python -O``.
  - ``ffprobe`` / ``avprobe`` / ``mprobe`` now emit a ``UserWarning`` with
    the underlying error before returning ``{}`` (the empty-metadata
    fallback that raw video relies on), instead of swallowing failures
    silently.

- **Edge-case hardening** (adversarial input testing; failures that were
  silent or crashed on otherwise-normal input):

  - Full-reference metrics (``mse``/``mae``/``psnr``/``ssim``/``msssim``/
    ``strred``) and ``globalEdgeMotion`` raised a bare ``assert`` on a
    ref/dis shape mismatch, and ``blockMotion`` on frame count; under
    ``python -O`` these vanished and mismatched arrays broadcast to a
    plausible-but-wrong score. Now raise ``ValueError``.
  - ``blockComp`` silently zeroed the bottom/right border for frames whose
    dimensions are not a multiple of ``mbSize`` (e.g. any 1080p frame with
    ``mbSize=16``). The uncovered remainder now passes through unchanged;
    evenly-divisible frames are unaffected.
  - ``blockComp`` no longer crashes on the documented single-frame input.
  - ``globalEdgeMotion`` on edgeless frames returns ``[0, 0]`` instead of a
    meaningless ``(-r, -r)`` or a crash.
  - ``vwrite`` on a zero-frame array now raises ``ValueError`` instead of
    silently writing no file.
  - ``blockComp`` validates the motion-vector grid against the macroblock
    grid (a mismatch raised a cryptic ``IndexError`` or silently ignored
    extra vectors; now ``ValueError``), and its single-frame result is now
    ``(1, M, N, C)`` to match the documented shape.
  - Documented previously-implicit behaviors: ``blockComp`` output dtype
    (``float64``), non-divisible-border passthrough, out-of-bounds-vector
    passthrough; ``globalEdgeMotion``'s ``[0, 0]`` edgeless sentinel; and
    that a low-level ``FFmpegWriter`` closed without frames is an
    intentional no-op (use ``vwrite`` for the guarded 0-frame check).
  - ``blockComp`` validates the full motion-vector shape
    ``(M//mbSize, N//mbSize, 2)`` (a wrong rank or last dimension was a
    cryptic ``IndexError`` or silently accepted).
  - The ``BytesIO`` writer now closes the ffmpeg subprocess pipe objects on
    ``close()``, eliminating a ``ResourceWarning: unclosed file`` per writer
    (no fd leak existed; the warnings were noise).
  - ``setFFmpegPath`` on a non-existent path now also clears the cached
    decoder/encoder lists, so a bad path no longer leaves the module
    half-configured with stale codec data.

1.1.13 (2026-06-01)
-------------------
- ``pathlib.Path`` objects are now accepted everywhere a filename is expected:
  ``skvideo.io.vread``, ``vwrite``, ``vreader``, ``ffprobe``, and the
  ``FFmpegReader`` / ``FFmpegWriter`` constructors. Previously a ``Path`` could
  cause ``ffprobe`` to silently fail and the downstream caller to raise a
  misleading "No way to determine width or height" error. Fixes #148, #163.
- ``FFmpegWriter._proc`` is now initialized to ``None`` in ``__init__`` so that
  calling ``close()`` (or exiting a ``with`` block) before any frames are
  written no longer raises ``AttributeError``. Fixes #139.
- ``FFmpegReader`` no longer leaks an ffmpeg process when ``verbosity > 0``.
  Previously ``_createProcess()`` ran ``subprocess.Popen`` twice — once inside
  an ``if verbosity > 0`` branch and once unconditionally after — causing
  broken-pipe errors for some users. Fixes #174.
- ``VideoReaderAbstract.close()`` now guards against ``self._proc.stderr is
  None``, which is the configured state when ``verbosity > 0``.
- ``FFmpegWriter`` now surfaces FFmpeg's actual error output instead of
  silently producing an empty/corrupt file when encoding fails. ``close()``
  raises ``RuntimeError`` with FFmpeg's stderr if the process exited
  non-zero; the existing ``writeFrame`` ``IOError`` handler now actually
  reads and includes the stderr that the original code template referenced
  but never populated. Non-verbose mode now uses ``stderr=PIPE`` instead of
  routing stderr to ``DEVNULL`` via ``STDOUT``. Fixes #111.
- ``skvideo.measure.videobliinds`` ``temporal_dc_variation_feature_extraction``
  no longer raises ``ValueError: operands could not be broadcast together``
  when a motion vector points outside the reference frame. Out-of-bounds
  blocks are marked NaN and ``nanstd`` / ``nanmean`` aggregate over the
  remainder. Default motion method (N3SS) is unchanged. Fixes #97 (patch
  contributed by amarion35, adapted with corrected bounds checks).
- Documentation: added a "Tuning FFmpeg Parameters" section to the I/O
  guide covering ``inputdict`` / ``outputdict`` semantics, common reading
  and writing recipes (pixel format, resize, codec, bitrate, framerate
  resampling), repeated-flag list values (v1.1.12), fraction framerate
  support (v1.1.13), and ``audiosrc`` muxing (v1.1.12). Fixes #160, #96.
  Also corrected a stale Python 2 ``xrange`` example in the writer code
  snippet.
- ``vread`` / ``vreader`` / ``FFmpegReader`` accept a new ``start_frame``
  argument to skip the first N frames before reading. Combine with
  ``num_frames`` for a windowed read::

      videodata = skvideo.io.vread("clip.mp4", start_frame=1000, num_frames=200)

  Uses FFmpeg's fast keyframe-based ``-ss`` input seek, so the first
  frame returned may snap to the nearest keyframe at or before the
  requested position. Passing both ``start_frame`` and
  ``inputdict['-ss']`` raises ``ValueError``. Fixes #166.
- The "ffmpeg/ffprobe not found in path" and "avconv/avprobe not found in
  path" warnings now explicitly say "binaries" and reference
  ``setFFmpegPath`` / ``setLibAVPath`` so users can recognize the fix.
  Previously the wording was easy to misread as referring to the
  ``skvideo/io/ffmpeg.py`` wrapper module. Fixes #159.
- ``inputdict['-r']`` now accepts FFmpeg fraction strings such as
  ``'30000/1001'`` (as returned by ``ffprobe avg_frame_rate``); previously
  ``int('30000/1001')`` raised ``ValueError``. Fixes #128.
- Documentation: corrected ``skvideo.io.write`` typo to ``skvideo.io.vwrite``
  in the I/O guide. Fixes #158.
- Motion: replaced all 45 instances of removed ``np.int()`` with ``int()`` in
  ``skvideo.motion.block`` for NumPy 2.x compatibility. Cherry-picked the SE3SS
  indexing fix from PR #142 with an additional correction (``cost = costs[dxy
  - 1]``) to avoid an IndexError when ``argmin`` returns the last element.
  Closes #142.

1.1.12 (2026-05-24)
-------------------
- Replaced setup.py / numpy.distutils packaging with pyproject.toml + setuptools.
  Restores ``pip install`` compatibility with Python 3.12+ and NumPy >= 1.26.
- Switched the project license declaration to a PEP 639 SPDX expression
  (``license = "BSD-3-Clause"``) and bumped the build-system setuptools floor
  to ``>= 77``. Eliminates the deprecation warning emitted by recent setuptools.
- Replaced deprecated ``ndarray.tostring()`` with ``tobytes()`` (NumPy 2.x; PR #182).
- Removed vestigial ``scipy.misc`` imports left behind by PR #177; switched
  ``skvideo.utils.stpyr`` to ``scipy.special.factorial`` (SciPy >= 1.3).
- Declared ``opencv-python-headless`` as a hard dependency so
  ``import skvideo.measure`` works on a fresh install. A new
  ``scripts/smoke_clean_install.sh`` verifies this in a fresh venv before
  each release.
- Dropped Python 2.7 and Python <= 3.9 support. Now supports Python 3.10–3.13.
- Migrated tests from nose to pytest.
- Replaced Travis CI / CircleCI configs with a GitHub Actions workflow.
- ``inputdict`` / ``outputdict`` flag values can now be lists/tuples to emit
  the same flag repeatedly (e.g. ``{'-metadata': ['title=foo', 'artist=bar']}``
  becomes ``-metadata title=foo -metadata artist=bar``). Empty list/tuple
  values raise ``ValueError`` instead of silently dropping the flag. Fixes #168.
- ``skvideo.io.ffprobe`` now exposes every stream of each codec type at
  ``info['<type>_streams']`` (e.g. ``info['audio_streams']``) in addition to
  the existing single-stream key. The plural keys are always present —
  files with no audio streams return ``info['audio_streams'] == []`` instead
  of raising ``KeyError``. Fixes #165.
- ``FFmpegWriter`` and ``vwrite`` accept an ``audiosrc`` argument: a path to
  a media file whose first audio stream is muxed into the output via
  ``-c:a copy`` and ``-shortest``, restoring audio across a ``vread`` /
  ``vwrite`` passthrough. To copy all audio streams instead of just the first,
  pass ``outputdict={'-map': ['0:v:0', '1:a']}`` (list form required so ffmpeg
  receives two separate ``-map`` flags; omitting ``0:v:0`` would drop the video
  stream). A missing path or an ``audiosrc`` with no audio stream raises at
  construction time rather than producing a silent videoless output.
  Fixes #173, #176.

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
