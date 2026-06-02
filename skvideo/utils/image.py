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
    if interp not in interp_methods:
        raise ValueError("interp must be one of %s; got %r." % (sorted(interp_methods), interp))

    if type(factor) != tuple:
        new_shape = (int(factor * image.shape[0]), int(factor * image.shape[1]))
    else:
        if len(factor) != 2:
            raise ValueError("factor tuple must have length 2; got %d." % len(factor))
        new_shape = factor

    h, w = new_shape
    return np.array(Image.fromarray(image, mode=mode).resize(
        (w, h),
        resample=interp_methods[interp.lower()])
    )
