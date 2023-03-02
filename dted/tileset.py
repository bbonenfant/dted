"""API for a collection of DTED tiles."""
import contextlib
import os
from pathlib import Path
from typing import Iterable, Iterator, Optional, Union

from .definitions import _FilePath
from .errors import InvalidFileError, NoElevationDataError
from .latlon import LatLon
from .tile import Tile

_SuffixType = Union[str, Iterable[str]]


class TileSet:
    """An API for accessing data within a collection of DTED files.

    When this class is initialized, the metadata records associated with the
      DTED files will be parsed, but no elevation data will be loaded into
      memory. Individual DTED Tiles can be loaded into memory by the user
      (see examples).

    Attributes:
        source: A record of the DTED sources of this TileSet.

    Methods:
        include: Add DTED data from a new source to the TileSet.
        get_elevation: Lookup the terrain elevation at a particular location.
        get_tile: Returns a Tile that contains a particular location,
            if one exists.
        get_all_tiles: Yields all Tiles that contain a particular location.
        __contains__: Check whether a LatLon point is contained within any DTED tile.

    Examples:

        Quickly lookup terrain elevation at a specific location.
        >>> from dted import LatLon, TileSet
        >>> dted_source: Path
        >>> tiles = TileSet(dted_source)
        >>> tiles.get_elevation(LatLon(latitude=41.36, longitude=-70.55))
        -21

        Check if location is covered by a DTED TileSet.
        >>> from dted import LatLon, TileSet
        >>> dted_source: Path
        >>> tiles = TileSet(dted_source)
        >>> LatLon(latitude=41.5, longitude=-70.25) in tiles
        True

        Load the elevation data a member Tile into memory.
        >>> from dted import LatLon, TileSet
        >>> dted_source: Path
        >>> tiles = TileSet(dted_source)
        >>> tile = tiles.get_tile(LatLon(latitude=41.5, longitude=-70.25))
        >>> tile.load_data()
        >>> tile.data.max()
        125
    """

    def __init__(self, source: _FilePath, suffix: Optional[_SuffixType] = None):
        """
        Args:
            source: A source for the DTED files. This can be a path to a directory
                containing the DTED files.
            suffix: One or several file extensions used to filter files within the
                source, i.e. ".dt1". If no suffix is provided, all files are parsed
                and non-DTED files are silently ignored.
        """
        self.sources = set()
        self._tiles = set()
        self.include(source, suffix)

    def include(self, source: _FilePath, suffix: Optional[_SuffixType] = None) -> None:
        """Include a new source within the TileSet.

        Args:
            source: A source for the DTED files. This can be a path to a directory
                containing the DTED files.
            suffix: One or several file extensions used to filter files within the
                source, i.e. ".dt1". If no suffix is provided, all files are parsed
                and non-DTED files are silently ignored.
        """
        source = Path(source)
        if source.is_dir():
            self.sources.add(source)
            return self._include_directory(source, suffix)
        raise ValueError(f"source must be a directory: {source}")

    def get_elevation(self, latlon: LatLon) -> float:
        """Lookup the terrain elevation at the specified location.

        This will return the elevation of the explicitly defined DTED point
            nearest to the specified location. If more than one Tile contains the
            location, only one of the tiles will be queried with no guarantee
            as to which.

        Args:
            latlon: The location at which to look up the terrain elevation.

        Raises:
            NoElevationDataError: If the specified location is not contained within the
                DTED file.
        """
        try:
            tile = self.get_tile(latlon)
        except ValueError:
            raise NoElevationDataError(f"no Tiles contain the location: {latlon}")
        return tile.get_elevation(latlon)

    def get_tile(self, latlon: LatLon) -> Tile:
        """Returns a Tile that contains the specified location, if one is
        contained within the DTED set.

        If more than one Tile contains the location, only one of the tiles will
            be returned with no guarantee as to which.

        Args:
            latlon: A LatLon location.

        Raises:
            ValueError: No Tiles contain the specified location.
        """
        try:
            return next(self.get_all_tiles(latlon))
        except StopIteration:
            raise ValueError(f"no Tiles contain the location: {latlon}")

    def get_all_tiles(self, latlon: LatLon) -> Iterator[Tile]:
        """Yields all Tiles that contain the specified location.

        Args:
            latlon: A LatLon location.
        """
        for tile in self._tiles:
            if latlon in tile:
                yield tile

    def __contains__(self, item: LatLon) -> bool:
        """Determines whether a location is covered by any DTED tiles."""
        if not isinstance(item, LatLon):
            raise TypeError(f"Expected LatLon -- Found: {item}")
        return any(item in tile for tile in self._tiles)

    def _include_directory(self, source: Path, suffix: Optional[_SuffixType]) -> None:
        """
        Args:
            source: A directory containing the DTED files.
            suffix: One or several file extensions used to filter files within the
                source, i.e. ".dt1". If no suffix is provided, all files are parsed
                and non-DTED files are silently ignored.
        """
        for root, _dirs, files in os.walk(source):
            for file in files:
                file = Path(root, file)
                if suffix:
                    if file.suffix not in suffix:
                        continue
                    tile = Tile(file, in_memory=False)
                    self._tiles.add(tile)
                else:
                    with contextlib.suppress(InvalidFileError):
                        tile = Tile(file, in_memory=False)
                    self._tiles.add(tile)
