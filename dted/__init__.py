""" Simplified imports for the DTED parsing module. """

import importlib.metadata as metadata
from .latlon import LatLon
from .tile import Tile
from .tileset import TileSet

__version__ = ""
try:
    __version__ = metadata.version(__name__)  # type: ignore
except FileNotFoundError:
    pass
