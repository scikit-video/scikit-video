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
