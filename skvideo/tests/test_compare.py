
import skvideo.io
import skvideo.datasets
import numpy
import matplotlib.pyplot as plt

# https://github.com/stoyanovgeorge/ffmpeg/wiki/How-to-Compare-Video
# https://www.pyimagesearch.com/2017/06/19/image-difference-with-opencv-and-python/
# https://stackoverflow.com/questions/28935851/how-to-compare-a-video-with-a-reference-video-using-opencv-and-python/30507468
# https://stackoverflow.com/questions/25774996/how-to-compare-show-the-difference-between-2-videos-in-ffmpeg
# http://www.scikit-video.org/stable/measure.html
# Full-Reference Quality Assessment
# Use skvideo.measure.scenedet to find frames that start scene boundaries. Check the documentation on selecting the specific detection algorithm.

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
    return numpy.frombuffer(figure.canvas.tostring_rgb(), dtype=numpy.uint8).reshape(height, width, 3)

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

def test_compare():
    pristineLoc, distortedLoc = skvideo.datasets.fullreferencepair()
    pristine = skvideo.io.vread(pristineLoc)
    skvideo.io.vwrite('test_pristine.ogg', pristine)
    distorted = skvideo.io.vread(distortedLoc)
    assert pristine.shape == distorted.shape
    combined = numpy.empty((pristine.shape[0], 480, 640, 3)) # need to figure out what size will be
    for frameIndex, (pristineFrame, distortedFrame) in enumerate(zip(pristine, distorted)):
        # https://matplotlib.org/tutorials/intermediate/gridspec.html
        figure = plt.figure(constrained_layout=True)
        gridspec = figure.add_gridspec(2, 3)
        upperLeftAx = figure.add_subplot(gridspec[0,0])
        upperLeftAx.margins(0)
        upperLeftAx.set_title('pristine')
        upperLeftAx.imshow(pristineFrame)
        upperRightAx = figure.add_subplot(gridspec[0,-1])
        upperRightAx.margins(0)
        upperRightAx.set_title('distorted')
        upperRightAx.imshow(distortedFrame)
        bottomAx = figure.add_subplot(gridspec[1,:])
        bottomAx.margins(0)
        bottomAx.set_title('difference')
        #plt.show()
        data = fig2data_alt(figure)
        combined[frameIndex, :] = data
        plt.close(figure)
    skvideo.io.vwrite('test.ogg', combined)

if __name__ == "__main__":
    test_compare()

