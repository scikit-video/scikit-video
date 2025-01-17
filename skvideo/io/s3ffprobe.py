import subprocess as sp
from ..utils import *
from .. import _HAS_FFMPEG
from .. import _FFMPEG_PATH
from .. import _FFPROBE_APPLICATION
import json

def s3ffprobe(filename):
    """Get metadata by using ffprobe

    Checks the output of ffprobe on the desired video
    file or URL. MetaData is then parsed into a dictionary.

    Parameters
    ----------
    filename : string
        Path to the video file or URL (e.g., presigned S3 URL)

    Returns
    -------
    metaDict : dict
       Dictionary containing all header-based information 
       about the passed-in source video.

    """
    # Check if FFmpeg exists in the path
    assert _HAS_FFMPEG, "Cannot find installation of real FFmpeg (which comes with ffprobe)."

    try:
        # Build the ffprobe command
        command = [
            _FFMPEG_PATH + "/" + _FFPROBE_APPLICATION,
            "-v", "error",  # Suppress output except errors
            "-show_streams",  # Extract stream-specific metadata
            "-print_format", "json",  # Use JSON for easy parsing
        ]

        # Add input filename (can be a local path or URL)
        command.append(filename)

        # Run the ffprobe command
        result = sp.run(command, stdout=sp.PIPE, stderr=sp.PIPE, text=True, check=True)
        metadata = result.stdout

        # Parse metadata (assumes json format for better compatibility)
        streamsbytype = {}
        parsed_data = json.loads(metadata).get("streams", [])
        for stream in parsed_data:
            codec_type = stream.get("codec_type", "").lower()
            if codec_type:
                streamsbytype[codec_type] = stream

        return streamsbytype

    except sp.CalledProcessError as err:
        print("FFprobe error occurred:", err.stderr)
        return {}
    except Exception as err:
        print("Unexpected error:", err)
        return {}
