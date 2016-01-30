mkdir $HOME/skvideo_build || echo "Already exists.";
mkdir $HOME/.cache/pip || echo "Already exists.";
mkdir $HOME/download || echo "Already exists.";
mkdir $HOME/build_ffmpeg || echo "Already exists.";
mkdir $HOME/build_libav || echo "Already exists.";

if [[ "$TRAVIS_OS_NAME" == "osx" ]]; then 
    brew update;

    if [ "$TRAVIS_PYTHON_VERSION" == "3.5" ]; then
        brew install python3;
        /usr/local/bin/pip3 install https://github.com/wbond/asn1crypto/archive/master.zip;
        export PYTHON_BIN=/usr/local/bin/python3;
    else
        if [ "$TRAVIS_PYTHON_VERSION" == "2.7" ]; then
            curl --silent --show-error https://bootstrap.pypa.io/get-pip.py | sudo /usr/bin/python2.7;
            sudo /usr/bin/python2.7 -W ignore -c "import pip; pip.main(['--disable-pip-version-check', '--quiet', 'install', 'https://github.com/wbond/asn1crypto/archive/master.zip'])";
            export PYTHON_BIN=/usr/bin/python2.7;
        else
            curl --silent --show-error https://bootstrap.pypa.io/get-pip.py | sudo -H /usr/bin/python2.6;
            sudo -H /usr/bin/python2.6 -W ignore -c "import pip; pip.main(['--disable-pip-version-check', '--quiet', 'install', 'https://github.com/wbond/asn1crypto/archive/master.zip'])";
            sudo -H /usr/bin/python2.6 -W ignore -c "import pip; pip.main(['--disable-pip-version-check', '--quiet', 'install', 'nose'])";

            export PYTHON_BIN=/usr/bin/python2.6;
        fi
    fi

    $PYTHON_BIN --version;
    # brew outdated <package-name> || brew upgrade <package-name>;
    source scripts/install_backend.sh;
else
     # - libatlas-dev
     # - ffmpeg # wrong version (libav), installed only for dependencies that come with it
     # - mediainfo

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

    sudo rm /usr/bin/gcc
    sudo rm /usr/bin/g++

    sudo ln -s /usr/bin/gcc-4.8 /usr/bin/gcc
    sudo ln -s /usr/bin/g++-4.8 /usr/bin/g++

    source scripts/install_backend.sh
fi
