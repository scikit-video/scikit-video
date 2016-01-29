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
source install_backend.sh
