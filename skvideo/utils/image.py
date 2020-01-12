"""
Replaces scipy.imresize because it is now deprecated

Steve Goring 2019
"""
import matplotlib.pyplot as plt
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


# http://www.icare.univ-lille1.fr/tutorials/convert_a_matplotlib_figure
def fig2data ( fig ):
    """
    @brief Convert a Matplotlib figure to a 4D numpy array with RGBA channels and return it
    @param fig a matplotlib figure
    @return a numpy 3D array of RGBA values
    """
    # draw the renderer
    fig.canvas.draw ( )
 
    # Get the RGBA buffer from the figure
    w,h = fig.canvas.get_width_height()
    buf = numpy.fromstring ( fig.canvas.tostring_argb(), dtype=numpy.uint8 )
    buf.shape = ( w, h,4 )
 
    # canvas.tostring_argb give pixmap in ARGB mode. Roll the ALPHA channel to have it in RGBA mode
    buf = numpy.roll ( buf, 3, axis = 2 )
    return buf

def fig2data_alt(figure):
    # https://stackoverflow.com/questions/35355930/matplotlib-figure-to-image-as-a-numpy-array
    figure.canvas.draw()
    width, height = figure.canvas.get_width_height()
    return np.frombuffer(figure.canvas.tostring_rgb(), dtype=np.uint8).reshape(height, width, 3)

# https://stackoverflow.com/questions/7821518/matplotlib-save-plot-to-numpy-array
# improved resolution?
# define a function which returns an image as numpy array from figure
def get_img_from_fig(fig, dpi=180):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=180)
    buf.seek(0)
    img_arr = np.frombuffer(buf.getvalue(), dtype=np.uint8)
    buf.close()
    img = cv2.imdecode(img_arr, 1)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    return img

# https://matplotlib.org/gallery/misc/agg_buffer_to_array.html
# fig.canvas.draw()
# grab the pixel buffer and dump it into a numpy array
# X = np.array(fig.canvas.renderer.buffer_rgba())


