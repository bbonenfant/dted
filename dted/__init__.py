""" Simplified imports for the DTED parsing module. """

# Python version compatibility.
try:
    # >= 3.8
    import importlib.metadata as metadata
except ImportError:
    #  < 3.8
    import importlib_metadata as metadata  # type: ignore

from .latlon import LatLon
from .tile import Tile

__version__ = ""
try:
    __version__ = metadata.version(__name__)  # type: ignore
except FileNotFoundError:
    pass
