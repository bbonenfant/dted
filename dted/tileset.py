"""API for a collection of DTED tiles."""

import contextlib
import os
from pathlib import Path
from typing import Iterator, Optional, Set, Tuple

from .definitions import _FilePath
from .errors import InvalidFileError, NoElevationDataError
from .latlon import LatLon
from .tile import Tile


class TileSet:
    """An API for accessing data within a collection of DTED files.

    When this class is initialized, the metadata records associated with the
      DTED files will be parsed, but no elevation data will be loaded into
      memory. Individual DTED Tiles can be loaded into memory by the user
      (see examples).

    Attributes:
        tiles: A set of Tile objects.
        suffixes: A tuple of file extensions used as the default to filter
            files within a source directory. If no suffixes are provided, then
            no filter is applied.
        warn: The default value passed as the warn argument to the Tile class.

    Methods:
        include: Add DTED data from a new source to the TileSet.
        get_elevation: Lookup the terrain elevation at a particular location.
            Raises NoElevationDataError if no tiles contain the location.
        get_tile: Returns a Tile that contains a particular location,
            if one exists. Raises NoElevationDataError if no tile exists.
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

    def __init__(
        self, *sources: _FilePath, suffixes: Optional[Tuple[str]] = None, warn: bool = True
    ):
        """
        Args:
            sources: One of more sources of DTED files.
                This can be a path to DTED file or to a directory containing DTED files.
            suffix: A tuple of file extensions used to filter files within the
                source, i.e. ".dt1". If no suffixes are provided, all files are parsed
                and non-DTED files are silently ignored.
            warn: Whether to emit the warning if void data is detected within
                the DTED file. Defaults to True.
        """
        self.suffixes: Tuple[str] = suffixes or tuple()
        self.tiles: Set[Tile] = set()
        self.warn = warn
        for source in sources:
            self.include(source, suffixes)

    @property
    def files(self) -> Set[Path]:
        return set(tile.file for tile in self.tiles)

    def include(self, source: _FilePath, suffixes: Optional[Tuple[str]] = None) -> None:
        """Include a new source within the TileSet.

        Args:
            source: A source of DTED files.
                This can be a path to DTED file or to a directory containing DTED files.
            suffixes: A tuple of file extensions used to filter files within the
                source, i.e. ".dt1". If no suffixes are provided, all files are parsed
                and non-DTED files are silently ignored.
        """
        source = Path(source)
        if not source.exists():
            raise ValueError(f"source does not exist: {source}")
        self._include_source(source, suffixes or self.suffixes)

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
        tile = self.get_tile(latlon)
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
            raise NoElevationDataError(f"no Tiles contain the location: {latlon}")

    def get_all_tiles(self, latlon: LatLon) -> Iterator[Tile]:
        """Yields all Tiles that contain the specified location.

        Args:
            latlon: A LatLon location.
        """
        for tile in self.tiles:
            if latlon in tile:
                yield tile

    def __contains__(self, item: LatLon) -> bool:
        """Determines whether a location is covered by any DTED tiles."""
        if not isinstance(item, LatLon):
            raise TypeError(f"Expected LatLon -- Found: {item}")
        return any(item in tile for tile in self.tiles)

    def _include_source(self, source: Path, suffixes: Tuple[str]) -> None:
        """
        Args:
            source: A DTED file or a directory containing DTED files.
            suffixes: A tuple of file extensions used to filter files within the
                source, i.e. ".dt1". If no suffixes are provided, all files are parsed
                and non-DTED files are silently ignored.
        """
        if source.is_file():
            self._include_file(source, suffixes)
            return

        for root, _dirs, files in os.walk(source):
            for file in files:
                self._include_file(Path(root, file), suffixes)

    def _include_file(self, file: Path, suffixes: Tuple[str]) -> None:
        """
        Args:
            file: A DTED file.
            suffixes: A tuple of file extensions used to filter files within the
                source, i.e. ".dt1". If no suffixes are provided, all files are parsed
                and non-DTED files are silently ignored.
        """
        if not suffixes:
            with contextlib.suppress(InvalidFileError):
                tile = Tile(file, in_memory=False, warn=self.warn)
                self.tiles.add(tile)
        if file.suffix in suffixes:
            tile = Tile(file, in_memory=False, warn=self.warn)
            self.tiles.add(tile)
