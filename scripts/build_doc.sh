#!/usr/bin/env bash


echo "Running Doc build script..."

sudo -E apt-get -yq update
sudo apt-get install libav-tools

#sudo apt-get install build-essential python-dev python-setuptools
#- sudo apt-get install python-numpy python-scipy python-dev python-matplotlib
#- sudo apt-get install python-nose python-coverage
#- sudo apt-get install python-sphinx
#- sudo apt-get remove python-pip
#- sudo pip install -U --ignore-installed setuptools virtualenv

# deactivate circleci virtualenv and setup a miniconda env instead
if [[ `type -t deactivate` ]]; then
  deactivate
fi

# Install dependencies with miniconda
wget https://repo.continuum.io/miniconda/Miniconda2-latest-Linux-x86_64.sh \
   -O miniconda.sh
chmod +x miniconda.sh && ./miniconda.sh -b -p $MINICONDA_PATH
export PATH="$MINICONDA_PATH/bin:$PATH"
conda update --yes --quiet conda

# Configure the conda environment and put it in the path using the
# provided versions
conda create -n $CONDA_ENV_NAME --yes python numpy scipy \
  cython nose coverage matplotlib sphinx pillow setuptools
source activate testenv

which python
python setup.py install --user
set -o pipefail && cd doc && make html 2>&1 | tee ~/log.txt
