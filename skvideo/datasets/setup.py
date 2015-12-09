def configuration(parent_package='',top_path=None):
    from numpy.distutils.misc_util import Configuration
    config = Configuration('datasets', parent_package, top_path)

    config.add_subpackage('data')

    return config
