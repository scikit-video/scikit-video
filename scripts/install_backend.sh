# first install desired ffmpeg

alias gcc='gcc-4.8'
alias cc='gcc-4.8'
alias g++='g++-4.8'
alias c++='c++-4.8'

# install yasm
cd $HOME/download
wget --no-check-certificate "http://www.tortall.net/projects/yasm/releases/yasm-1.3.0.tar.gz" || exit 1
tar -xf "yasm-1.3.0.tar.gz"
cd yasm-1.3.0;
echo ./configure
./configure --prefix="$HOME/build_ffmpeg" --bindir="$HOME/build_ffmpeg/bin"
echo make
#make -j4 > /dev/null 2>&1 || exit 3
make -j4
echo make install
#make install || exit 4
make install


cd $HOME/download
wget --no-check-certificate "http://ffmpeg.org/releases/ffmpeg-$FFMPEG.tar.bz2" || exit 1
tar xjf "ffmpeg-$FFMPEG.tar.bz2"

if [[ $FFMPEG == "snapshot" ]]; then 
    cd "ffmpeg";
else
    cd "ffmpeg-$FFMPEG"; 
fi

echo ./configure
PATH="$HOME/build_ffmpeg/bin:$PATH" PKG_CONFIG_PATH="$HOME/build_ffmpeg/lib/pkgconfig" ./configure --disable-static --enable-shared --disable-doc --prefix="$HOME/build_ffmpeg" || exit 2
echo make
PATH="$HOME/build_ffmpeg/bin:$PATH" make -j4 > /dev/null 2>&1 || exit 3
echo make install
make install || exit 4
cd $TRAVIS_BUILD_DIR

# also install desired libav

cd $HOME/download

if [[ $LIBAV != "none" ]]; then
    if [[ $LIBAV == "gitrepo" ]]; then 
	git clone git://git.libav.org/libav.git
	cd libav
    else
	wget --no-check-certificate "https://libav.org/releases/libav-$LIBAV.tar.gz" || exit 1
	tar xf "libav-$LIBAV.tar.gz"
	cd "libav-$LIBAV"; 
    fi

    echo ./configure
    ./configure --disable-yasm --prefix="$HOME/build_libav" || exit 2
    echo make
    make -j4 > /dev/null 2>&1 || exit 3
    echo make install
    make install || exit 4
fi
cd $TRAVIS_BUILD_DIR
