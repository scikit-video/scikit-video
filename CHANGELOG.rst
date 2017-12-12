1.1.10
-----
- Adding BSD license file

1.1.9
-----
- Dropping ffmpeg 2.1 support
- removed libav warning when ffmpeg is already installed
- scene detector uses less memory

1.1.8
-----
- Added Video Bliinds and BRISQUE quality feature extractors
- Added ST-RRED, MS-SSIM, SSIM, NIQE, Video Oracle quality metrics
- Added initial windows support
- Added supporting unit tests
- Python3 compatibility patches
- Fixed assortment of bugs
- Fixed file descriptor deadlock when using too much data

1.1.7
-----
- Added scene detection, motion estimation, and miscellaneous examples
- Fixed bug of not closing FFmpeg when using vread/vreader
- Fixed bugs with scene detector and motion estimation

1.1.6
-----

- Added scene cut detection functions
- Added global motion estimation
- Added edge extraction, but only canny edge detection for now
- Added more examples to the documentation

1.1.5
1.1.4
-----

- Fixed issues with pypi

1.1.3
-----

- Fixed I/O bug with vreader and greyscale frames 
- Migrated markdown files to rst files

1.1.2
-----

- No longer testing git master of LibAV, since it presented instabilities 
- Updating index and FAQ pages in scikit-video docs
- Initial publishing to pypi under the name sk-video
- Initial changelog created
