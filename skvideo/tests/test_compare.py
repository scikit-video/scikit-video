
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
    combined = skvideo.measure.view_diff.make_comparison_video(distorted, pristine, ImageChops_on_ndarrays, skvideo.measure.mse_rgb)
    skvideo.io.vwrite('test.ogg', combined)
    skvideo.io.vwrite('test.mp4', combined)

if __name__ == "__main__":
    test_compare()

