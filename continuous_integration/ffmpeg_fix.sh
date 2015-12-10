cd $HOME/
wget --no-check-certificate http://ffmpeg.org/releases/ffmpeg-snapshot.tar.bz2 || exit 1
tar xjf ffmpeg-snapshot.tar.bz2
cd ffmpeg
echo ./configure
./configure --disable-yasm --disable-static --enable-shared --disable-doc --prefix="$HOME/ffmpeg" || exit 2
echo make
make -j4 || exit 3
# waste of time, just fix the paths
# echo make install
# make install || exit 4
cd $TRAVIS_BUILD_DIR
