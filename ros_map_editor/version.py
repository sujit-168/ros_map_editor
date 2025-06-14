"""Version information."""

# Version of the ros-map-editor package
__version__ = "0.1.2"

# Version info tuple: (major, minor, patch)
VERSION_INFO = tuple(map(int, __version__.split('.')))

__all__ = ['__version__', 'VERSION_INFO']