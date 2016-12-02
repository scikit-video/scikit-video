#!/usr/bin/env python
descr = """\
This library provides easy access to common as well as
state-of-the-art video processing routines. Check out the
website for more details.

"""

DISTNAME            = 'sk-video'
DESCRIPTION         = 'Video Processing in Python'
LONG_DESCRIPTION    = descr
MAINTAINER          = 'Todd Goodall',
MAINTAINER_EMAIL    = 'info@scikit-video.org',
URL                 = 'http://scikit-video.org/'
LICENSE             = 'BSD'
DOWNLOAD_URL        = 'https://github.com/scikit-video/scikit-video'
PACKAGE_NAME        = 'scikit-video'
EXTRA_INFO          = dict(
    install_requires=['numpy', 'scipy'],
    classifiers=['Development Status :: 3 - Alpha',
                 'Intended Audience :: Developers',
                 'Intended Audience :: Science/Research',
                 'License :: OSI Approved :: BSD License',
                 'Operating System :: POSIX :: Linux',
                 'Operating System :: MacOS',
                 'Operating System :: Microsoft :: Windows',
                 'Programming Language :: Python :: 2.6',
                 'Programming Language :: Python :: 2.7',
                 'Topic :: Multimedia :: Video',
                 'Topic :: Scientific/Engineering']
)


import os
import sys
import subprocess

import setuptools
from numpy.distutils.core import setup

import skvideo

def configuration(parent_package='', top_path=None, package_name=PACKAGE_NAME):
    if os.path.exists('MANIFEST'): os.remove('MANIFEST')

    from numpy.distutils.misc_util import Configuration
    config = Configuration(None, parent_package, top_path)

    # Avoid non-useful msg: "Ignoring attempt to set 'name' (from ... "
    config.set_options(ignore_setup_xxx_py=True,
                       assume_default_configuration=True,
                       delegate_options_to_subpackages=True,
                       quiet=True)

    config.add_subpackage('skvideo')
    config.add_data_dir('skvideo/datasets/data')
    config.add_data_dir('skvideo/measure/data')
    return config

# Documentation building command
try:
    from sphinx.setup_command import BuildDoc as SphinxBuildDoc
    class BuildDoc(SphinxBuildDoc):
        """Run in-place build before Sphinx doc build"""
        def run(self):
            ret = subprocess.call([sys.executable, sys.argv[0], 'build_ext', '-i'])
            if ret != 0:
                raise RuntimeError("Building Scipy failed!")
            SphinxBuildDoc.run(self)
    cmdclass = {'build_sphinx': BuildDoc}
except ImportError:
    cmdclass = {}

# Call the setup function
if __name__ == "__main__":
    setup(configuration=configuration,
          name=DISTNAME,
          maintainer=MAINTAINER,
          maintainer_email=MAINTAINER_EMAIL,
          description=DESCRIPTION,
          license=LICENSE,
          url=URL,
          download_url=DOWNLOAD_URL,
          long_description=LONG_DESCRIPTION,
          include_package_data=True,
          test_suite="nose.collector",
          cmdclass=cmdclass,
          version=skvideo.__version__,
          **EXTRA_INFO)
