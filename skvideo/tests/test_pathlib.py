"""Tests for pathlib.Path support across the I/O entry points (issues #148, #163)."""
from pathlib import Path

import numpy as np
import pytest

import skvideo.io
import skvideo.datasets


@pytest.fixture
def bunny_path():
    return Path(skvideo.datasets.bigbuckbunny())


def test_ffprobe_accepts_pathlib(bunny_path):
    info = skvideo.io.ffprobe(bunny_path)
    assert info != {}, "ffprobe returned empty dict for a valid Path input"
    assert "video" in info


def test_vread_accepts_pathlib(bunny_path):
    videodata = skvideo.io.vread(bunny_path, num_frames=2)
    assert videodata.shape == (2, 720, 1280, 3)


def test_vreader_accepts_pathlib(bunny_path):
    reader = skvideo.io.vreader(bunny_path, num_frames=2)
    frames = list(reader)
    assert len(frames) == 2
    assert frames[0].shape == (720, 1280, 3)


def test_vwrite_accepts_pathlib(tmp_path):
    out_path = tmp_path / "out.mp4"
    data = np.zeros((3, 64, 64, 3), dtype=np.uint8)
    skvideo.io.vwrite(out_path, data)
    assert out_path.exists()
    assert out_path.stat().st_size > 0


def test_ffmpeg_reader_accepts_pathlib(bunny_path):
    reader = skvideo.io.FFmpegReader(bunny_path)
    assert reader.getShape() == (132, 720, 1280, 3)
    reader.close()


def test_ffmpeg_writer_accepts_pathlib(tmp_path):
    out_path = tmp_path / "out.mp4"
    writer = skvideo.io.FFmpegWriter(out_path)
    frame = np.zeros((64, 64, 3), dtype=np.uint8)
    writer.writeFrame(frame)
    writer.close()
    assert out_path.exists()
