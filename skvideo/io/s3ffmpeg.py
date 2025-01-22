import subprocess as sp
import numpy as np
import re

class S3FFmpegReader:
    def __init__(self, url):
        """Simple FFmpeg reader for getting BGR frames from video URLs.
        
        Args:
            url: Video URL (http/https)
        """
        if not url.startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")
            
        self._url = url
        self._proc = None
        
        # Get dimensions first
        self.width, self.height = self._get_dimensions()
        self.frame_size = self.width * self.height * 3  # BGR = 3 channels
        
        # Start main FFmpeg process
        self._start_process()

    def _get_dimensions(self):
        """Get video dimensions from FFmpeg."""
        cmd = [
            'ffmpeg',
            '-i', self._url
        ]
        
        try:
            # FFmpeg prints video info to stderr
            process = sp.Popen(cmd, stderr=sp.PIPE)
            _, stderr = process.communicate()
            stderr = stderr.decode('utf-8')
            
            # Look for video stream info
            match = re.search(r'Stream.*Video.* (\d+)x(\d+)', stderr)
            if match:
                width = int(match.group(1))
                height = int(match.group(2))
                return width, height
            raise RuntimeError("Could not determine video dimensions")
            
        except Exception as e:
            raise RuntimeError(f"Error getting video dimensions: {str(e)}")

    def _start_process(self):
        """Start FFmpeg process configured for BGR output."""
        cmd = [
            'ffmpeg',
            '-nostats', 
            '-loglevel', 'error',
            
            # Streaming options
            '-reconnect', '1',
            '-reconnect_streamed', '1',
            '-reconnect_delay_max', '5',
            
            # Input
            '-i', self._url,
            
            # Output options - direct to BGR
            '-f', 'rawvideo',
            '-pix_fmt', 'bgr24',
            '-vcodec', 'rawvideo',
            '-'
        ]
        
        try:
            self._proc = sp.Popen(
                cmd,
                stdout=sp.PIPE,
                stderr=sp.PIPE,
                bufsize=10**8
            )
        except sp.SubprocessError as e:
            raise RuntimeError(f"Failed to start FFmpeg: {str(e)}")

    def read_frames(self):
        """Read all frames into a numpy array."""
        if not self._proc:
            raise RuntimeError("FFmpeg process not started")
            
        try:
            raw_data = self._proc.stdout.read()
            
            if len(raw_data) == 0:
                raise RuntimeError("No frames read from video")
                
            # Convert to numpy array
            frames = np.frombuffer(raw_data, dtype=np.uint8)
            
            # Calculate number of frames from total size
            num_frames = len(frames) // self.frame_size
            
            # Reshape using known dimensions
            return frames.reshape((num_frames, self.height, self.width, 3))
            
        except Exception as e:
            raise RuntimeError(f"Error reading frames: {str(e)}")
        finally:
            self.close()

    def close(self):
        """Clean up resources."""
        if self._proc:
            try:
                self._proc.terminate()
                self._proc.wait(timeout=1)
            except:
                pass
            finally:
                self._proc = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()