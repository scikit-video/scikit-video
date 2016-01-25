cd $HOME/download
wget --no-check-certificate "http://ffmpeg.org/releases/ffmpeg-$FFMPEG.tar.bz2" || exit 1
tar xjf "ffmpeg-$FFMPEG.tar.bz2"

if [[ $FFMPEG == "snapshot" ]]; then 
    cd "ffmpeg";
else
    cd "ffmpeg-$FFMPEG"; 
fi

echo ./configure
./configure --disable-yasm --disable-static --enable-shared --disable-doc --prefix="$HOME/builds" || exit 2
echo make
make -j4 || exit 3
echo make install
make install || exit 4
cd $TRAVIS_BUILD_DIR

# also build/install libav
cd $HOME/download
wget --no-check-certificate "https://libav.org/releases/libav-11.4.tar.gz" || exit 1
tar xf "libav-11.4.tar.gz"

cd "libav-11.4"; 

echo ./configure
./configure --disable-yasm --disable-static --enable-shared --disable-doc --prefix="$HOME/builds" || exit 2
echo make
make -j4 || exit 3
echo make install
make install || exit 4
cd $TRAVIS_BUILD_DIR

# also build/install libav
