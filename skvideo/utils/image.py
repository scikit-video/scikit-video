import PIL
from PIL import Image

def imresize(image, factor, interp=PIL.Image.NEAREST, mode=None):
    """
    resize an image with a specified resizing factor, this factor can also be
    the target shape of the resized image specified as tuple.
    """
    if type(factor) != tuple:
        new_shape = (int(factor * image.shape[0]), int(factor * full_scale.shape[1]))
    else:
        assert(len(tuple) == 2)
        new_shape = factor
    return np.array(Image.fromarray(image, mode=mode).resize(
        new_shape,
        resample=PIL.Image.BICUBIC)
    )