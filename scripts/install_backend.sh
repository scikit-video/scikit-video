# first install desired ffmpeg

alias gcc='gcc-4.8'
alias cc='gcc-4.8'
alias g++='g++-4.8'
alias c++='c++-4.8'

cd $HOME/download
wget --no-check-certificate "http://ffmpeg.org/releases/ffmpeg-$FFMPEG.tar.bz2" || exit 1
tar xjf "ffmpeg-$FFMPEG.tar.bz2"

if [[ $FFMPEG == "snapshot" ]]; then 
    cd "ffmpeg";
else
    cd "ffmpeg-$FFMPEG"; 
fi

echo ./configure
./configure --disable-yasm --disable-static --enable-shared --disable-doc --prefix="$HOME/build_ffmpeg" || exit 2
echo make
make -j4 || exit 3
echo make install
make install || exit 4
cd $TRAVIS_BUILD_DIR

# also install desired libav

cd $HOME/download

if [[ $LIBAV == "gitrepo" ]]; then 
    git clone git://git.libav.org/libav.git
    cd libav
else
    wget --no-check-certificate "https://libav.org/releases/libav-$LIBAV.tar.gz" || exit 1
    tar xf "libav-$LIBAV.tar.gz"
    cd "libav-$LIBAV"; 
fi

echo ./configure
./configure --disable-yasm --disable-static --enable-shared --disable-doc --prefix="$HOME/build_libav" || exit 2
echo make
make -j4 || exit 3
echo make install
make install || exit 4
cd $TRAVIS_BUILD_DIR
