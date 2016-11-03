conda install --yes python=$TRAVIS_PYTHON_VERSION numpy scipy matplotlib nose coverage

echo $TRAVIS_PYTHON_VERSION
if [[ "$TRAVIS_PYTHON_VERSION" == "2.6" ]]; then
	conda install --yes python=$TRAVIS_PYTHON_VERSION unittest2 scipy=0.14.0
fi

GIT_TRAVIS_REPO=$(pwd)
echo $GIT_TRAVIS_REPO
cd $HOME
if [ ! -d "skvideo_build_$NAME" ]; then  mkdir skvideo_build_$NAME; fi
rsync -av --exclude='.git/' --exclude='testvenv/' $GIT_TRAVIS_REPO skvideo_build_${NAME}
cd skvideo_build_${NAME}/scikit-video
python --version
python -c "import numpy; print('numpy %s' % numpy.__version__)"
python -c "import scipy; print('scipy %s' % scipy.__version__)"
