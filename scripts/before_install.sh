mkdir $HOME/skvideo_build || echo "Already exists.";
mkdir $HOME/.cache/pip || echo "Already exists.";
mkdir $HOME/download || echo "Already exists.";
mkdir $HOME/build_ffmpeg || echo "Already exists.";
mkdir $HOME/build_libav || echo "Already exists.";

cd $HOME/download

if [[ "$TRAVIS_OS_NAME" == "osx" ]]; then 
    brew update;
    wget http://repo.continuum.io/miniconda/Miniconda-latest-MacOSX-x86_64.sh -O miniconda.sh


    # brew outdated <package-name> || brew upgrade <package-name>;
else
     # - libatlas-dev
     # - ffmpeg # wrong version (libav), installed only for dependencies that come with it
     # - mediainfo

    wget http://repo.continuum.io/miniconda/Miniconda-latest-Linux-x86_64.sh -O miniconda.sh
fi

chmod +x miniconda.sh
./miniconda.sh -b
export PATH="$HOME/miniconda/bin:$HOME/miniconda2/bin:$HOME/miniconda3/bin:$PATH"
cd $TRAVIS_BUILD_DIR
conda update --yes conda
conda create --yes -n condaenv python=$TRAVIS_PYTHON_VERSION
conda install --yes -n condaenv pip
source activate condaenv
# The next couple lines fix a crash with multiprocessing on Travis and are not specific to using Miniconda
sudo rm -rf /dev/shm
sudo ln -s /run/shm /dev/shm
python --version

# update gcc for building
# sudo add-apt-repository -y ppa:ubuntu-toolchain-r/test
# sudo apt-get -qq update
# sudo apt-get -qq install g++-4.8

# sudo rm /usr/bin/gcc
# sudo rm /usr/bin/g++

# sudo ln -s /usr/bin/gcc-4.8 /usr/bin/gcc
# sudo ln -s /usr/bin/g++-4.8 /usr/bin/g++

source scripts/install_backend.sh
export PYTHON_BIN=python

$PYTHON_BIN --version;
