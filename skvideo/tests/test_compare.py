
import skvideo.io
import skvideo.measure
import skvideo.measure.view_diff
import skvideo.datasets
from PIL import Image, ImageChops
import numpy
import matplotlib.pyplot as plt


def ImageChops_on_ndarrays(distortedFrame, pristineFrame):
    return ImageChops.difference(Image.fromarray(distortedFrame), Image.fromarray(pristineFrame))


def test_compare():
    pristineLoc, distortedLoc = skvideo.datasets.fullreferencepair()
    pristine = skvideo.io.vread(pristineLoc)
    distorted = skvideo.io.vread(distortedLoc)
    return skvideo.measure.view_diff.make_comparison_video(distorted, pristine,
        differenceImgFunc=ImageChops_on_ndarrays, numericalDifferenceFunc=skvideo.measure.mse_rgb)


def predict_no_change(video): return video

def test_predict():
    return skvideo.measure.view_diff.make_prediction_comparison_video(
        skvideo.io.vread(skvideo.datasets.bigbuckbunny()),
        predict_no_change,
        differenceImgFunc=ImageChops_on_ndarrays, numericalDifferenceFunc=skvideo.measure.mse_rgb)


if __name__ == "__main__":
    combined = test_predict()
    skvideo.io.vwrite('test.ogg', combined)
    skvideo.io.vwrite('test.mp4', combined)

