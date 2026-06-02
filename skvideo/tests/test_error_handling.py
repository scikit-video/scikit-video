"""Library code must raise exceptions, not return non-exception singletons
or call exit() (which would kill the host process)."""
import importlib

import numpy as np
import pytest

import skvideo.utils

# The function `niqe` shadows the `niqe` submodule in skvideo.measure's
# namespace, so import the modules explicitly to reach their helpers.
_niqe_mod = importlib.import_module("skvideo.measure.niqe")
_vbliinds_mod = importlib.import_module("skvideo.measure.videobliinds")


def test_rgb2gray_rejects_alpha_with_real_exception():
    # Previously `raise NotImplemented` (the singleton), which itself
    # raises "TypeError: exceptions must derive from BaseException".
    rgba = np.zeros((1, 16, 16, 4), dtype=np.uint8)
    with pytest.raises(NotImplementedError):
        skvideo.utils.rgb2gray(rgba)


def test_niqe_patches_raises_on_small_image_instead_of_exit():
    # _get_patches_generic used exit(0) on an undersized image, terminating
    # the caller's process. It must raise instead.
    tiny = np.zeros((4, 4), dtype=np.float32)
    with pytest.raises(ValueError):
        _niqe_mod._get_patches_generic(tiny, 96, 0, 1)


def test_videobliinds_computequality_raises_on_small_frame_instead_of_exit():
    tiny = np.zeros((4, 4, 1), dtype=np.float32)
    with pytest.raises(ValueError):
        _vbliinds_mod.computequality(tiny, 96, 96, None, None)
