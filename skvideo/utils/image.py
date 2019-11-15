"""
Replaces scipy.imresize because it is now deprecated

Steve Goring 2019
"""
import numpy as np
import PIL
from PIL import Image

def imresize(image, factor, interp="nearest", mode=None):
    """
    resize an image with a specified resizing factor, this factor can also be
    the target shape of the resized image specified as tuple.
    """
    interp_methods = {
        "nearest": PIL.Image.NEAREST,
        "bicubic": PIL.Image.BICUBIC,
        "bilinear": PIL.Image.BILINEAR
    }
    assert(interp in interp_methods)

    if type(factor) != tuple:
        new_shape = (int(factor * image.shape[0]), int(factor * image.shape[1]))
    else:
        assert(len(factor) == 2)
        new_shape = factor

    h, w = new_shape
    return np.array(Image.fromarray(image, mode=mode).resize(
        (w, h),
        resample=interp_methods[interp.lower()])
    )
