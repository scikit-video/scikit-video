#!/bin/bash
# This script is meant to be called by the "script" step defined in
# .travis.yml. See http://docs.travis-ci.com/ for more details.
# The behavior of the script is controlled by environment variabled defined
# in the .travis.yml in the top level folder of the project.

# License: 3-clause BSD

# setup ffmpeg dir
export PATH="$HOME/ffmpeg_install:$HOME/ffmpeg_install/bin:$PATH"
export LD_LIBRARY_PATH="$HOME/ffmpeg_install/libavcodec:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="$HOME/ffmpeg_install/libavdevice:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="$HOME/ffmpeg_install/libavfilter:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="$HOME/ffmpeg_install/libavformat:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="$HOME/ffmpeg_install/libavresample:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="$HOME/ffmpeg_install/libavutil:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="$HOME/ffmpeg_install/libpostproc:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="$HOME/ffmpeg_install/libswresample:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="$HOME/ffmpeg_install/libswscale:$LD_LIBRARY_PATH"

echo "which ffmpeg is used:"
which ffmpeg

set -e

# Get into a temp directory to run test from the installed scikit learn and
# check if we do not leave artifacts
mkdir -p /tmp/skvideo_tmp
cd /tmp/skvideo_tmp

python --version
python -c "import numpy; print('numpy %s' % numpy.__version__)"
python -c "import scipy; print('scipy %s' % scipy.__version__)"

if [[ "$COVERAGE" == "true" ]]; then
    nosetests -v --with-coverage skvideo
else
    nosetests -v skvideo
fi

# Is directory still empty ?
ls

# Test doc
cd $HOME/skvideo_build_$NAME/scikit-video
make test-doc test-sphinxext
