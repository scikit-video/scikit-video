
import typing

import numpy as np
import matplotlib.pyplot as plt

import skvideo.utils.image



# https://github.com/stoyanovgeorge/ffmpeg/wiki/How-to-Compare-Video
# https://www.pyimagesearch.com/2017/06/19/image-difference-with-opencv-and-python/
# http://www.blog.pythonlibrary.org/2016/10/11/how-to-create-a-diff-of-an-image-in-python/
#     diff = ImageChops.difference(image_one, image_two)
# https://stackoverflow.com/questions/28935851/how-to-compare-a-video-with-a-reference-video-using-opencv-and-python/30507468
# https://stackoverflow.com/questions/25774996/how-to-compare-show-the-difference-between-2-videos-in-ffmpeg
# http://www.scikit-video.org/stable/measure.html
# Full-Reference Quality Assessment
# Use skvideo.measure.scenedet to find frames that start scene boundaries. Check the documentation on selecting the specific detection algorithm.




# If possible, we would probably prefer to encapsulate matplotlib away from the user, in case we find a better way.
# That means no raw access to axes.
def make_comparison_image(image: np.ndarray, referenceImage: np.ndarray,
                          differenceImgFunc: typing.Callable[[np.ndarray, np.ndarray], np.ndarray],
                          numericalDifferenceVector: np.ndarray = None,
                          frameIndex: int = None,
                          showReferenceImage: bool = False) -> np.ndarray:
    """Constructs a faceted composite image showing an image alongside its diff from a reference image.

    This image is intended to be a single frame of a video; if available, a plot of the differences in over time is shown below, with the current frame labeled.

    Parameters
    ----------
    image : ndarray
        Image to display, ndarray of dimension (M, N, C), or (M, N),
        where M is the height, N is width,
        and C is number of channels.

    referenceImage : ndarray
        Reference image, ndarray of dimension (M, N, C), or (M, N),
        where M is the height, N is width,
        and C is number of channels.

    numericalDifferenceVector : ndarray
        Single number measuring the difference for each frame of a video, ndarray of dimension (T,),
        where T is the number of frames.
        This does not make sense for all measurements, such as ST-RRED.

    Returns
    -------
    composite_array : ndarray
        The comparison frame, ndarray of dimension (M, N, C) or (M, N),
        where M is the height, N is width,
        and C is number of channels.
        If the current frame is highlighted with a red dot, then C will be 3 even if the original images are grayscale.
    """
    # https://matplotlib.org/tutorials/intermediate/gridspec.html
    figure = plt.figure(constrained_layout=True)
    gridspec = figure.add_gridspec(1 if numericalDifferenceVector is None else 2, 3 if showReferenceImage else 2)
    upperLeftAx = figure.add_subplot(gridspec[0,0])
    upperLeftAx.margins(0)
    # upperLeftAx.set_title('pristine')
    upperLeftAx.imshow(image)
    if showReferenceImage:
        upperRightAx = figure.add_subplot(gridspec[0,-1])
        upperRightAx.margins(0)
        # upperRightAx.set_title('distorted')
        upperRightAx.imshow(referenceImage)
    upperMiddleAx = figure.add_subplot(gridspec[0,1])
    upperMiddleAx.margins(0)
    # upperMiddleAx.set_title('difference')
    upperMiddleAx.imshow(differenceImgFunc(image, referenceImage))
    if numericalDifferenceVector is not None:
        bottomAx = figure.add_subplot(gridspec[1,:])
        bottomAx.margins(0)
        # bottomAx.set_title('difference')
        bottomAx.plot(numericalDifferenceVector)
        if frameIndex is not None:
            bottomAx.plot(frameIndex, numericalDifferenceVector[frameIndex], 'ro')
    data = skvideo.utils.image.fig2data_alt(figure)
    plt.close(figure)
    return data


def combined_frame_shape(image: np.ndarray, referenceImage: np.ndarray,
                         differenceImgFunc: typing.Callable[[np.ndarray, np.ndarray], np.ndarray],
                         numericalDifferenceVector: np.ndarray = None,
                         frameIndex: int = None,
                         showReferenceImage: bool = False) -> typing.Tuple[int]:
    """There's probably a better way to do this, but this tells us what shape we'll need for the combined video.
    """
    return make_comparison_image(image, referenceImage, differenceImgFunc, numericalDifferenceVector, frameIndex, showReferenceImage).shape


def make_comparison_video(video: np.ndarray, referenceVideo: np.ndarray,
                          differenceImgFunc: typing.Callable[[np.ndarray, np.ndarray], np.ndarray],
                          numericalDifferenceFunc: typing.Callable[[np.ndarray, np.ndarray], np.ndarray] = None,
                          showReferenceImage: bool = False) -> np.ndarray:
    assert video.shape == referenceVideo.shape
    differenceVector = numericalDifferenceFunc(referenceVideo, video)
    assert len(differenceVector.shape) == 1
    assert differenceVector.shape[0] == video.shape[0]
    numberOfFrames = video.shape[0]
    compositeVideo = np.empty((numberOfFrames,) + skvideo.measure.view_diff.combined_frame_shape(video[0], referenceVideo[0], differenceImgFunc, differenceVector, 0))
    for frameIndex, (pristineFrame, distortedFrame) in enumerate(zip(referenceVideo, video)):
        compositeVideo[frameIndex, :] = skvideo.measure.view_diff.make_comparison_image(distortedFrame, pristineFrame, differenceImgFunc, differenceVector, frameIndex)
    return compositeVideo



