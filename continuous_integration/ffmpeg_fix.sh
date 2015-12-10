cd $HOME/download
wget --no-check-certificate http://ffmpeg.org/releases/ffmpeg-snapshot.tar.bz2 || exit 1
tar xjf ffmpeg-snapshot.tar.bz2
cd ffmpeg
echo ./configure
./configure --disable-yasm --disable-static --enable-shared --disable-doc --prefix="$HOME/builds" || exit 2
echo make
make -j4 || exit 3
echo make install
make install || exit 4
cd $TRAVIS_BUILD_DIR
