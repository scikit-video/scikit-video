""" Plugin that uses ffmpeg to read and write series of images to
a wide range of video formats.

"""

# Heavily inspired from Almar Klein's imageio code
# Copyright (c) 2015, imageio contributors
# distributed under the terms of the BSD License (included in release).

import time
import subprocess as sp

import numpy as np

from .s3ffprobe import s3ffprobe
from ..utils import *
from .. import _HAS_FFMPEG
from .. import _FFMPEG_PATH

# S3 FFmpeg reader class to get video data from AWS S3 presigned url
class S3FFmpegReader:
    def __init__(self, filename, inputdict=None, outputdict=None, verbosity=0):
        """Initialize FFmpeg reader for video processing.
        
        Args:
            filename (str): Path to video file or URL
            inputdict (dict, optional): FFmpeg input parameters
            outputdict (dict, optional): FFmpeg output parameters
            verbosity (int, optional): Logging verbosity level
        """
        assert _HAS_FFMPEG, "Cannot find FFmpeg installation"
        
        self._filename = filename
        self._proc = None
        self.inputdict = inputdict or {}
        self.outputdict = outputdict or {}
        
        # Configure streaming parameters for URLs
        if filename.startswith(('http://', 'https://')):
            self._configure_streaming_options()
        
        # Get video metadata
        self.probe_info = s3ffprobe(filename)
        if "video" not in self.probe_info:
            raise ValueError("No video stream found in the input")
            
        self.video_info = self.probe_info["video"]
        
        # Initialize video parameters
        self._initialize_parameters()

        self.get_input_height_and_width()
        self.get_output_height_and_width()
        self.get_frame_count()
        if '-pix_fmt' not in self.outputdict:
            self.outputdict['-pix_fmt'] = "rgb24"
        self.outputdepth = np.int(bpplut[self.outputdict['-pix_fmt']][0])
        
        # Start FFmpeg process
        self._start_ffmpeg_process(verbosity)

    def get_frame_count(self):
        probecmd = [_FFMPEG_PATH + "/ffprobe"] + ["-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries", "stream=nb_read_frames", "-of", "default=nokey=1:noprint_wrappers=1", self._filename]
        self.inputframenum = np.int(check_output(probecmd).decode().split('\n')[0])

    def get_input_height_and_width(self):
        if ("-s" in self.inputdict):
            print('rohit if')
            widthheight = self.inputdict["-s"].split('x')
            self.inputwidth = np.int(widthheight[0])
            self.inputheight = np.int(widthheight[1])
        elif (("width" in self.video_info) and ("height" in self.video_info)):
            print('rohit else if')
            self.inputwidth = np.int(self.video_info["width"])
            self.inputheight = np.int(self.video_info["height"])
        else:
            print('rohit else')
            raise ValueError("No way to determine width or height from video. Need `-s` in `inputdict`. Consult documentation on I/O.")

    def get_output_height_and_width(self):
        if '-s' in self.outputdict:
            widthheight = self.outputdict["-s"].split('x')
            self.outputwidth = np.int(widthheight[0])
            self.outputheight = np.int(widthheight[1])
        else:
            self.outputwidth = self.inputwidth
            self.outputheight = self.inputheight

    def getShape(self):
        """Returns a tuple (T, M, N, C) 
        
        Returns the video shape in number of frames, height, width, and channels per pixel.
        """
        print(f'GET Shape {self.inputframenum} {self.outputheight} {self.outputwidth} {self.outputdepth}')
        return self.inputframenum, self.outputheight, self.outputwidth, self.outputdepth

    def _configure_streaming_options(self):
        """Configure FFmpeg options for streaming content."""
        streaming_options = {
            '-reconnect': '1',
            '-reconnect_streamed': '1',
            '-reconnect_delay_max': '5'
        }
        
        for key, value in streaming_options.items():
            if key not in self.inputdict:
                self.inputdict[key] = value

    def _initialize_parameters(self):
        """Initialize video parameters from metadata."""
        # Frame rate
        self.fps = self._get_fps()
        
        # Dimensions
        self.width, self.height = self._get_dimensions()
        
        # Frame count
        self.frame_count = self._get_frame_count()
        
        # Pixel format
        self.pix_fmt = self._get_pixel_format()
        
        # Setup output parameters
        self._setup_output_parameters()

    def _get_fps(self):
        """Get video frame rate."""
        if "-r" in self.inputdict:
            return float(self.inputdict["-r"])
            
        if "@r_frame_rate" in self.video_info:
            fps_str = self.video_info["@r_frame_rate"]
            if '/' in fps_str:
                num, den = map(float, fps_str.split('/'))
                return num / den
            return float(fps_str)
            
        return 25.0  # Default fallback

    def _get_dimensions(self):
        """Get video dimensions."""
        if "-s" in self.inputdict:
            w, h = map(int, self.inputdict["-s"].split('x'))
            return w, h
            
        width = int(self.video_info.get('width') or self.video_info.get('@width', 0))
        height = int(self.video_info.get('height') or self.video_info.get('@height', 0))
        
        if not (width and height):
            raise ValueError("Could not determine video dimensions")
            
        return width, height

    def _get_frame_count(self):
        """Get total frame count."""
        if "@nb_frames" in self.video_info:
            return int(self.video_info["@nb_frames"])
            
        if "@duration" in self.video_info:
            duration = float(self.video_info["@duration"])
            return int(round(self.fps * duration))
            
        return -1  # Unknown frame count

    def _get_pixel_format(self):
        """Get pixel format."""
        return (self.inputdict.get("-pix_fmt") or 
                self.video_info.get("@pix_fmt", "rgb24"))

    def _setup_output_parameters(self):
        """Setup output parameters."""
        if '-f' not in self.outputdict:
            self.outputdict['-f'] = 'rawvideo'
            
        if '-pix_fmt' not in self.outputdict:
            self.outputdict['-pix_fmt'] = 'rgb24'
            
        if '-vcodec' not in self.outputdict:
            self.outputdict['-vcodec'] = 'rawvideo'
        
        self.bytes_per_pixel = 3  # RGB24 format
        self.frame_size = self.width * self.height * self.bytes_per_pixel

    def _start_ffmpeg_process(self, verbosity):
        """Start FFmpeg subprocess."""
        command = self._build_ffmpeg_command(verbosity)
        
        try:
            self._proc = sp.Popen(
                command,
                stdin=sp.PIPE,
                stdout=sp.PIPE,
                stderr=sp.PIPE if verbosity == 0 else None,
                bufsize=10**8
            )
        except sp.SubprocessError as e:
            raise RuntimeError(f"Failed to start FFmpeg: {str(e)}")

    def _build_ffmpeg_command(self, verbosity):
        """Build FFmpeg command for remote video streams."""
        command = ["ffmpeg"]  # Assuming ffmpeg is in PATH
        
        # Set verbosity
        if verbosity == 0:
            command.extend(["-nostats", "-loglevel", "0"])
        
        # Input stream (remote URL)
        command.extend(["-re", "-i", self._filename])  # Add real-time processing and input file
        
        # Output format
        command.extend(["-f", "rawvideo"])
        
        # Pixel format
        command.extend(["-pix_fmt", "rgb24"])
        
        # Video codec
        command.extend(["-vcodec", "rawvideo"])
        
        # Output to pipe
        command.append("-")
        
        return command

    def read_frame(self):
        """Read a single frame from the video stream.
        
        Returns:
            numpy.ndarray: Frame data as RGB24 numpy array
        """
        if not self._proc:
            raise RuntimeError("FFmpeg process not started")
        
        try:
            # Read raw frame data
            raw_frame = self._proc.stdout.read(self.frame_size)
            
            if len(raw_frame) == 0:
                raise EOFError("End of video stream")
                
            if len(raw_frame) != self.frame_size:
                raise RuntimeError(
                    f"Incomplete frame: got {len(raw_frame)} bytes, "
                    f"expected {self.frame_size}"
                )
            
            # Convert to numpy array and reshape
            frame = np.frombuffer(raw_frame, dtype=np.uint8)
            return frame.reshape((self.height, self.width, self.bytes_per_pixel))
            
        except Exception as e:
            self._terminate()
            raise RuntimeError(f"Error reading frame: {str(e)}")

    def nextFrame(self):
        """Generator yielding video frames.
        
        Yields:
            numpy.ndarray: Each frame as RGB24 numpy array
        """
        frame_index = 0
        
        try:
            while frame_index < self.inputframenum:
                try:
                    frame = self.read_frame()
                    yield frame
                    frame_index += 1
                except EOFError:
                    break
                    
        except Exception as e:
            self._terminate()
            raise RuntimeError(f"Error in frame iteration: {str(e)}")
            
        finally:
            self.close()

    def _terminate(self, timeout=1.0):
        """Terminate FFmpeg process."""
        if not self._proc or self._proc.poll() is not None:
            return
            
        self._proc.terminate()
        end_time = time.time() + timeout
        
        while time.time() < end_time:
            if self._proc.poll() is not None:
                break
            time.sleep(0.01)

    def close(self):
        """Clean up resources."""
        if self._proc and self._proc.poll() is None:
            try:
                self._proc.stdin.close()
                self._proc.stdout.close()
                if self._proc.stderr:
                    self._proc.stderr.close()
                self._terminate(0.2)
            except Exception:
                pass  # Ignore errors during cleanup
            finally:
                self._proc = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
