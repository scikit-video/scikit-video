mkdir $HOME/skvideo_build_ubuntu || echo "Already exists."
mkdir $HOME/.cache/pip || echo "Already exists."
mkdir $HOME/download || echo "Already exists."
mkdir $HOME/build_ffmpeg || echo "Already exists."
mkdir $HOME/build_libav || echo "Already exists."
cd $HOME/download
wget http://repo.continuum.io/miniconda/Miniconda-latest-Linux-x86_64.sh -O miniconda.sh
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
sudo add-apt-repository -y ppa:ubuntu-toolchain-r/test
sudo apt-get -qq update
sudo apt-get -qq install g++-4.8

alias gcc='gcc-4.8'
alias cc='gcc-4.8'
alias g++='g++-4.8'
alias c++='c++-4.8'

cc -v
exit
source scripts/install_backend.sh
