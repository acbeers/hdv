"""HDV - Hierarchical Data Viewer for CSV."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("hdv")
except PackageNotFoundError:
    __version__ = "0.0.0+dev"
