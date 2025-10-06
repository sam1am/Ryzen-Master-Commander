# src/version.py
VERSION_MAJOR = 1
VERSION_MINOR = 2
VERSION_PATCH = 0
VERSION_TUPLE = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
__version__ = ".".join(map(str, VERSION_TUPLE))


def get_version():
    return __version__
