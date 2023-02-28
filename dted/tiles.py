import os
import math
import glob
from pathlib import Path

from .tile import Tile
from .latlon import LatLon


class Tiles:
    """
    Holds a dictionary of Tile objects

    Allows the user to specify a directory to
    load files from and access tiles.
    """

    def __init__(self, in_memory: bool = True, dted_level: int = None):
        """
        Initializes the Tiles class

        Args:
            in_memory: whether or not the dted files will be
                loaded into memory
            dted_level: acceptable values = 1 or 2 corresponding
                to which level of dted you will search for in your
                directory. if this is not set it will load both level 1
                and 2.
        """
        self.in_memory = in_memory
        self.dted_level = dted_level
        self.tile_map = {}

    def load_tiles_from_dir(self, folder: str) -> bool:
        """
        makes tile objects from passed in folder of dted
        and stores into a dictionary. This also works recursively.

        Args:
            folder: the string containing a directory of dted
                files that you would like to load.
        """
        if not os.path.isdir(folder):
            print("passed in folder does not exist")
            return False

        if self.dted_level:
            search = f"{folder}/**/*.dt{self.dted_level}"
        else:
            search = f"{folder}/**/*.dt*"

        for filepath in glob.glob(search, recursive=True):
            tile = Tile(Path(filepath), in_memory=self.in_memory)
            key = self._get_dict_key_from_ll(tile.dsi.south_west_corner)
            self.tile_map[f"{key}"] = tile
        return True

    def get_tile(self, latlon: LatLon) -> Tile:
        """
        Gets a Tile object from the tile dictionary.

        Args:
            latlon: a lat lon which you want the tile
                for
        Returns:
            Tile object if tile is present
            None if no tile present
        """
        key = self._get_dict_key_from_ll(latlon)
        if key in self.tile_map:
            return self.tile_map[f"{key}"]
        return None

    def get_elevation(self, latlon: LatLon) -> float:
        """
        Lookup the terrain elevation at the specified location.

        This will return the elevation of the explicitly defined DTED point
            nearest to the specified location. will automatically find the
            correct dted file loaded in the tile_map and query it

        Args:
            latlon: The location at which to lookup the terrain elevation.

        Raises:
            NoElevationDataError: If the specified location is not contained within the
                DTED file.
        """
        key = self._get_dict_key_from_ll(latlon)
        if key in self.tile_map:
            tile = self.tile_map[f"{key}"]
            if tile:
                return tile.get_elevation(latlon)
        return None

    def _get_dict_key_from_ll(self, latlon: LatLon) -> str:
        """
        Create the key for the dictionary based on a LatLon
        object.

        Args:
            latlon: the lat lon which lies within the dted file
        """
        return f"{int(math.floor(latlon.latitude))}{int(math.floor(latlon.longitude))}"
