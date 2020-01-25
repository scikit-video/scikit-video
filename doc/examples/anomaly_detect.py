
import prednet.evaluate
import skvideo.datasets
import skvideo.io
import skvideo.measure


def ImageChops_on_ndarrays(distortedFrame, pristineFrame):
    return ImageChops.difference(Image.fromarray(distortedFrame), Image.fromarray(pristineFrame))


def test_anomaly_detection():
    predicted = prednet.evaluate.save_predicted_frames_for_single_video(skvideo.datasets.bikes(),
            nt=None)
    combined = skvideo.measure.view_diff.make_comparison_video(skvideo.io.vread(skvideo.datasets.bikes()), predicted,
            ImageChops_on_ndarrays, skvideo.measure.mse_rgb)
    skvideo.io.vwrite('test.ogg', combined)
    skvideo.io.vwrite('test.mp4', combined)


if __name__ == "__main__":
    test_anomaly_detection()
