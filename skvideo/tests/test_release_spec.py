"""Spec-driven release tests for scikit-video 1.1.12.

Skipped or external-only coverage requested by the spec:
- Multi-value ffmpeg flag argv ordering: needs command-line argv inspection
  without mocking ffmpeg, so this file verifies artifact behavior instead.
- Section 5 clean-install dependency smoke: the spec says to verify this with
  a separate shell smoke script, not inside this pytest process.
- Full 1.1.11 suite collection/pass check: Phase 2 should run the existing
  suite under pytest directly rather than nesting pytest inside pytest.
"""

import importlib
import os
import subprocess
import sys
import warnings

import numpy as np
import pytest
from numpy.testing import assert_array_almost_equal


FFMPEG_REQUIRED = "FFmpeg required for this release-spec test."


@pytest.fixture
def skvideo_modules():
    import skvideo
    import skvideo.datasets
    import skvideo.io
    import skvideo.measure

    if not skvideo._HAS_FFMPEG:
        pytest.skip(FFMPEG_REQUIRED)

    return skvideo


@pytest.fixture
def bunny_path(skvideo_modules):
    return skvideo_modules.datasets.bigbuckbunny()


@pytest.fixture
def short_rgb_frames(skvideo_modules, bunny_path):
    return skvideo_modules.io.vread(bunny_path, num_frames=10)


def _metadata_tags(info):
    tags = {}

    def visit(value):
        if isinstance(value, dict):
            if "@key" in value and "@value" in value:
                tags[value["@key"]] = value["@value"]
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(info)
    return tags


def _streams(info, codec_type):
    key = codec_type + "_streams"
    if key in info:
        return info[key]
    if codec_type in info:
        return [info[codec_type]]
    return []


def _stream_count(info, codec_type):
    return len(_streams(info, codec_type))


def _duration(stream):
    for key in ("@duration", "duration"):
        if key in stream:
            return float(stream[key])

    if "@nb_frames" in stream and "@r_frame_rate" in stream:
        num, den = stream["@r_frame_rate"].split("/")
        fps = float(num) / float(den)
        if fps:
            return float(stream["@nb_frames"]) / fps

    raise AssertionError("stream has no duration-like field")


def _frame_count(stream):
    for key in ("@nb_frames", "nb_frames", "@nb_read_frames", "nb_read_frames"):
        if key in stream:
            return int(stream[key])
    raise AssertionError("stream has no frame-count field")


def _write_small_mp4(skvideo, path, frames, **kwargs):
    skvideo.io.vwrite(str(path), frames, **kwargs)
    return skvideo.io.ffprobe(str(path))


def _synthetic_rgb_frames():
    y, x = np.indices((32, 32))
    frames = np.empty((4, 32, 32, 3), dtype=np.uint8)
    for t in range(frames.shape[0]):
        frames[t, :, :, 0] = (x * 7 + t * 11) % 256
        frames[t, :, :, 1] = (y * 5 + t * 17) % 256
        frames[t, :, :, 2] = ((x + y) * 3 + t * 23) % 256
    return frames


def _roundtrip_yuv(skvideo, tmp_path, pix_fmt):
    source = _synthetic_rgb_frames()
    raw_path = tmp_path / ("roundtrip_" + pix_fmt + ".yuv")
    skvideo.io.vwrite(str(raw_path), source, outputdict={"-pix_fmt": pix_fmt})
    decoded = skvideo.io.vread(
        str(raw_path),
        width=source.shape[2],
        height=source.shape[1],
        num_frames=source.shape[0],
        inputdict={"-pix_fmt": pix_fmt},
    )
    return source, decoded


def _make_two_audio_clip(skvideo, source, tmp_path):
    out = tmp_path / "two_audio_streams.mp4"
    ffmpeg = os.path.join(skvideo._FFMPEG_PATH, skvideo._FFMPEG_APPLICATION)
    cmd = [
        ffmpeg,
        "-y",
        "-i",
        source,
        "-i",
        source,
        "-map",
        "0:v:0",
        "-map",
        "0:a:0",
        "-map",
        "1:a:0",
        "-c:v",
        "copy",
        "-c:a",
        "copy",
        "-shortest",
        str(out),
    ]
    subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return out


class TestMultiValueMetadata:
    def test_outputdict_metadata_list_writes_each_metadata_value(
        self, skvideo_modules, short_rgb_frames, tmp_path
    ):
        """Spec: "When a list, each element produces a separate --flag value pair on the ffmpeg command line, in list order." """
        output = tmp_path / "metadata_list.mp4"
        info = _write_small_mp4(
            skvideo_modules,
            output,
            short_rgb_frames[:3],
            outputdict={"-metadata": ["title=My Title", "artist=Kathy"]},
        )

        assert {"title": "My Title", "artist": "Kathy"}.items() <= _metadata_tags(info).items()

    def test_single_element_metadata_list_matches_string_form(
        self, skvideo_modules, short_rgb_frames, tmp_path
    ):
        """Spec: "A single-element list outputdict={'-metadata': ['title=foo']} produces the same result as the string form 'title=foo'." """
        list_info = _write_small_mp4(
            skvideo_modules,
            tmp_path / "metadata_list_single.mp4",
            short_rgb_frames[:3],
            outputdict={"-metadata": ["title=foo"]},
        )
        string_info = _write_small_mp4(
            skvideo_modules,
            tmp_path / "metadata_string_single.mp4",
            short_rgb_frames[:3],
            outputdict={"-metadata": "title=foo"},
        )

        assert (_metadata_tags(list_info).get("title"), _metadata_tags(string_info).get("title")) == ("foo", "foo")

    def test_empty_metadata_list_fails_loudly(self, skvideo_modules, short_rgb_frames, tmp_path):
        """Spec: "An empty list is a programmer error, explicit failure is acceptable; silent skip is not." """
        with pytest.raises(Exception):
            skvideo_modules.io.vwrite(
                str(tmp_path / "empty_metadata_list.mp4"),
                short_rgb_frames[:1],
                outputdict={"-metadata": []},
            )

    def test_multivalue_flag_order_needs_argv_level_verification(self):
        """Spec: "Order matters and must be preserved." """
        pytest.skip("needs verification of ffmpeg argv order without mocking ffmpeg")


class TestFFprobeMultiStream:
    def test_single_stream_clip_exposes_audio_streams_list(self, skvideo_modules, bunny_path):
        """Spec: "Probe bigbuckbunny.mp4, single video, single audio, both new lists have length 1." """
        info = skvideo_modules.io.ffprobe(bunny_path)

        assert _stream_count(info, "audio") == 1

    def test_single_stream_clip_exposes_video_streams_list(self, skvideo_modules, bunny_path):
        """Spec: "Probe bigbuckbunny.mp4, single video, single audio, both new lists have length 1." """
        info = skvideo_modules.io.ffprobe(bunny_path)

        assert _stream_count(info, "video") == 1

    def test_single_audio_legacy_key_equals_first_audio_stream(self, skvideo_modules, bunny_path):
        """Spec: "For a single-audio file, info['audio'] == info['audio_streams'][0]." """
        info = skvideo_modules.io.ffprobe(bunny_path)

        assert info["audio"] == info["audio_streams"][0]

    def test_single_video_legacy_key_equals_first_video_stream(self, skvideo_modules, bunny_path):
        """Spec: "info['audio'] and info['video'] MUST still exist with the same shape and keys as in v1.1.11 for single-stream files." """
        info = skvideo_modules.io.ffprobe(bunny_path)

        assert info["video"] == info["video_streams"][0]

    def test_ffprobe_exposes_all_audio_streams_when_multiple_present(
        self, skvideo_modules, bunny_path, tmp_path
    ):
        """Spec: "Probe a synthesized multi-audio file, len(info['audio_streams']) == 2." """
        multi_audio = _make_two_audio_clip(skvideo_modules, bunny_path, tmp_path)
        info = skvideo_modules.io.ffprobe(str(multi_audio))

        assert len(info["audio_streams"]) == 2

    def test_no_audio_file_exposes_empty_audio_streams(
        self, skvideo_modules, short_rgb_frames, tmp_path
    ):
        """Spec: "For a file with no audio streams, info['audio_streams'] is [] (empty list, not missing key, not None)." """
        info = _write_small_mp4(skvideo_modules, tmp_path / "video_only.mp4", short_rgb_frames[:3])

        assert info["audio_streams"] == []


class TestAudioPassthrough:
    def test_vwrite_with_audiosrc_adds_audio_stream(
        self, skvideo_modules, bunny_path, short_rgb_frames, tmp_path
    ):
        """Spec: "vwrite(filename, video, audiosrc=None) accepts a new optional audiosrc argument." """
        info = _write_small_mp4(
            skvideo_modules,
            tmp_path / "vwrite_audio.mp4",
            short_rgb_frames,
            audiosrc=bunny_path,
        )

        assert _stream_count(info, "audio") == 1

    def test_ffmpegwriter_with_audiosrc_adds_audio_stream(
        self, skvideo_modules, bunny_path, short_rgb_frames, tmp_path
    ):
        """Spec: "FFmpegWriter(filename, audiosrc=None, ...) accepts a new optional audiosrc argument." """
        output = tmp_path / "writer_audio.mp4"
        writer = skvideo_modules.io.FFmpegWriter(str(output), audiosrc=bunny_path)
        try:
            for frame in short_rgb_frames:
                writer.writeFrame(frame)
        finally:
            writer.close()

        assert _stream_count(skvideo_modules.io.ffprobe(str(output)), "audio") == 1

    def test_audiosrc_output_video_stream_uses_supplied_frame_count(
        self, skvideo_modules, bunny_path, short_rgb_frames, tmp_path
    ):
        """Spec: "The output file contains a video stream built from the supplied frames." """
        info = _write_small_mp4(
            skvideo_modules,
            tmp_path / "vwrite_audio_frame_count.mp4",
            short_rgb_frames,
            audiosrc=bunny_path,
        )

        assert _frame_count(info["video_streams"][0]) == len(short_rgb_frames)

    def test_audiosrc_output_audio_does_not_outlast_video(
        self, skvideo_modules, bunny_path, short_rgb_frames, tmp_path
    ):
        """Spec: "The output ends when the shorter of the two streams ends, so the audio doesn't extend past the last video frame." """
        info = _write_small_mp4(
            skvideo_modules,
            tmp_path / "vwrite_audio_shortest.mp4",
            short_rgb_frames,
            audiosrc=bunny_path,
        )

        assert _duration(info["audio_streams"][0]) <= _duration(info["video_streams"][0])

    def test_audiosrc_audio_codec_can_be_overridden(
        self, skvideo_modules, bunny_path, short_rgb_frames, tmp_path
    ):
        """Spec: "User can override codec via outputdict={'-c:a': 'aac'}." """
        info = _write_small_mp4(
            skvideo_modules,
            tmp_path / "vwrite_audio_codec.mp4",
            short_rgb_frames,
            audiosrc=bunny_path,
            outputdict={"-c:a": "aac"},
        )

        assert info["audio_streams"][0]["@codec_name"] == "aac"

    def test_vwrite_without_audiosrc_keeps_video_only_default(
        self, skvideo_modules, short_rgb_frames, tmp_path
    ):
        """Spec: "When audiosrc is None (the default), behavior is identical to v1.1.11, no audio stream in output." """
        info = _write_small_mp4(skvideo_modules, tmp_path / "vwrite_default_no_audio.mp4", short_rgb_frames)

        assert info["audio_streams"] == []

    def test_missing_audiosrc_raises(self, skvideo_modules, short_rgb_frames, tmp_path):
        """Spec: "If audiosrc does not exist or contains no audio stream, the call should fail loudly." """
        with pytest.raises(Exception):
            skvideo_modules.io.vwrite(
                str(tmp_path / "missing_audiosrc.mp4"),
                short_rgb_frames[:1],
                audiosrc=str(tmp_path / "does-not-exist.mp4"),
            )


class TestModernStackCompatibility:
    def test_public_submodules_import_without_numpy_or_scipy_warnings(self):
        """Spec: "Every public submodule imports cleanly ... No DeprecationWarning or FutureWarning from numpy/scipy is raised during import." """
        public_modules = [
            "skvideo",
            "skvideo.io",
            "skvideo.motion",
            "skvideo.measure",
            "skvideo.datasets",
            "skvideo.utils",
        ]
        for name in list(sys.modules):
            if name == "skvideo" or name.startswith("skvideo."):
                del sys.modules[name]

        with warnings.catch_warnings():
            warnings.simplefilter("error", DeprecationWarning)
            warnings.simplefilter("error", FutureWarning)
            imported = [importlib.import_module(name).__name__ for name in public_modules]

        assert imported == public_modules

    def test_basic_use_emits_no_numpy_or_scipy_warnings(self, skvideo_modules, bunny_path):
        """Spec: "No DeprecationWarning or FutureWarning from numpy/scipy is raised during import or basic use (read one video, compute one metric)." """
        with warnings.catch_warnings():
            warnings.simplefilter("error", DeprecationWarning)
            warnings.simplefilter("error", FutureWarning)
            frames = skvideo_modules.io.vread(bunny_path, num_frames=2)
            score = skvideo_modules.measure.mse(frames, frames)

        assert np.isfinite(float(np.mean(score)))

    def test_ffmpegreader_returns_uint8_frame_stack(self, skvideo_modules, bunny_path):
        """Spec: "FFmpegReader returns numpy.ndarray of dtype=uint8, shape (frames, H, W, channels)." """
        frames = skvideo_modules.io.vread(bunny_path, num_frames=2)

        assert (frames.dtype, frames.ndim, frames.shape[0], frames.shape[-1]) == (np.dtype("uint8"), 4, 2, 3)


class TestDeclaredDependencies:
    def test_clean_install_measure_import_is_external_smoke_script(self):
        """Spec: "Do not put this in test_release_spec.py." """
        pytest.skip("section 5 requires a separate clean-venv shell smoke script")


class TestRoundTripAndMetricNumerics:
    def test_yuv420p_roundtrip_mse_stays_below_modern_threshold(
        self, skvideo_modules, tmp_path
    ):
        """Spec: "RGB to yuv420p to RGB round-trip: MSE threshold < 2.0." """
        source, decoded = _roundtrip_yuv(skvideo_modules, tmp_path, "yuv420p")

        assert np.mean((source.astype(np.float32) - decoded.astype(np.float32)) ** 2) < 2.0

    def test_yuv444_roundtrip_is_bit_exact(self, skvideo_modules, tmp_path):
        """Spec: "RGB to yuv444 to RGB round-trip: == 0 (bit-exact)." """
        source, decoded = _roundtrip_yuv(skvideo_modules, tmp_path, "yuv444p")

        assert np.mean((source.astype(np.float32) - decoded.astype(np.float32)) ** 2) == 0

    def test_brisque_features_match_pinned_reference(self, skvideo_modules, bunny_path):
        """Spec: "BRISQUE / NIQE / VideoBliinds decimal=2 against pinned reference arrays." """
        dis = skvideo_modules.io.vread(bunny_path, as_grey=True)
        features = skvideo_modules.measure.brisque_features(dis[0, :200, :200])
        expected = np.array([
            2.2890000343, 0.2322334051, 0.8130000234, 0.0714222640,
            0.0303122569, 0.0790375844, 0.7820000052, 0.1253909320,
            0.0196695272, 0.1092280298, 0.8009999990, 0.0333177634,
            0.0419092514, 0.0649642125, 0.8009999990, 0.0416957438,
            0.0396158583, 0.0685468540, 3.1700000763, 0.3377875388,
            0.9840000272, 0.0400288589, 0.0888380781, 0.1259520650,
            0.9520000219, 0.1778325588, 0.0371656679, 0.2002325803,
            0.8489999771, -0.0157390144, 0.1383629888, 0.1215882078,
            0.8629999757, 0.0312444586, 0.1079876497, 0.1403252929,
        ])

        assert_array_almost_equal(features[0], expected, decimal=2)

    def test_niqe_matches_pinned_reference(self, skvideo_modules, bunny_path):
        """Spec: "BRISQUE / NIQE / VideoBliinds decimal=2 against pinned reference arrays." """
        ref = skvideo_modules.io.vread(bunny_path, as_grey=True)[:2]

        assert_array_almost_equal(skvideo_modules.measure.niqe(ref), np.array([11.19, 11.05]), decimal=2)

    def test_videobliinds_features_match_pinned_reference(self, skvideo_modules, bunny_path):
        """Spec: "BRISQUE / NIQE / VideoBliinds decimal=2 against pinned reference arrays." """
        dis = skvideo_modules.io.vread(bunny_path, as_grey=True)[:20, :200, :200]
        expected = np.array([
            2.508800000000, 0.724275349118, 0.886150000000, 0.094900845105,
            0.075270971672, 0.153258614032, 0.832950000000, 0.145853236056,
            0.047469409576, 0.156152160875, 0.858150000000, 0.043908992567,
            0.093810932519, 0.128847087445, 0.857375000000, 0.070210827430,
            0.083866251922, 0.138073680721, 3.172000000000, 0.970150022342,
            1.004175000000, 0.040410359225, 0.212755111969, 0.253072861341,
            0.961000000000, 0.186445182929, 0.124771296044, 0.300422186113,
            0.875400000000, -0.018816730259, 0.206918460682, 0.191991528548,
            0.901925000000, 0.030521899481, 0.192355885179, 0.215250702742,
            9.489535449185, 1.009615778923, 0.250374922528, 0.713554522195,
            0.672277178250, 0.669912498498, 0.692061577463, 0.621884675219,
            0.441264439346, 0.142519297382,
        ])

        assert_array_almost_equal(skvideo_modules.measure.videobliinds_features(dis), expected, decimal=2)


class TestBackwardCompatibilityChecklist:
    def test_vread_preserves_baseline_shape_and_dtype(self, skvideo_modules, bunny_path):
        """Spec: "vread('clip.mp4') returns the same shape/dtype as it did in v1.1.11." """
        frames = skvideo_modules.io.vread(bunny_path)

        assert (frames.shape, frames.dtype) == ((132, 720, 1280, 3), np.dtype("uint8"))

    def test_vwrite_default_has_no_audio_stream(self, skvideo_modules, short_rgb_frames, tmp_path):
        """Spec: "vwrite('out.mp4', frames) with no audiosrc produces a video file with no audio stream." """
        info = _write_small_mp4(skvideo_modules, tmp_path / "compat_no_audio.mp4", short_rgb_frames[:3])

        assert info["audio_streams"] == []

    def test_ffmpegreader_yields_ffprobe_frame_count(self, skvideo_modules, bunny_path):
        """Spec: "FFmpegReader('clip.mp4') iterator yields the documented number of frames (matches ffprobe nb_frames)." """
        info = skvideo_modules.io.ffprobe(bunny_path)
        reader = skvideo_modules.io.FFmpegReader(bunny_path)
        try:
            count = sum(1 for _ in reader)
        finally:
            reader.close()

        assert count == _frame_count(info["video"])

    def test_ffprobe_legacy_video_codec_name_remains_available(self, skvideo_modules, bunny_path):
        """Spec: "ffprobe('clip.mp4')['video']['@codec_name'] still returns the codec string." """
        info = skvideo_modules.io.ffprobe(bunny_path)

        assert info["video"]["@codec_name"] == "h264"

    def test_existing_1_1_11_pytest_suite_must_be_run_by_phase_2(self):
        """Spec: "All 1.1.11 test files under skvideo/tests collect and pass under pytest." """
        pytest.skip("run the existing test suite directly in Phase 2, not recursively from this test")
