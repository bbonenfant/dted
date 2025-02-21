"""Tests for the TileSet class."""

import pytest

from dted import LatLon, TileSet
from dted.errors import NoElevationDataError
from . import TEST_DATA_DIR


def test_tileset_from_directory() -> None:
    """Test loading DTED files from a directory."""
    tileset = TileSet(TEST_DATA_DIR)
    assert len(tileset.tiles) == 3
    for tile in tileset.tiles:
        assert tile.dsi.south_west_corner in tileset


def test_tileset_from_files() -> None:
    """Test loading individual DTED files."""
    tileset = TileSet()
    for file in TEST_DATA_DIR.glob("*.dt2"):
        tileset.include(file)
    assert len(tileset.tiles) == 2


def test_tileset_with_filters() -> None:
    """Test loading DTED files using filters."""
    tileset_dir = TileSet(TEST_DATA_DIR, suffixes=(".dt2",))
    tileset_files = TileSet(suffixes=(".dt2",))
    for file in TEST_DATA_DIR.glob("*.dt2"):
        tileset_files.include(file)
    assert tileset_dir.tiles == tileset_files.tiles


def test_get_elevation() -> None:
    """Test retrieving DTED elevation data."""
    tileset = TileSet(TEST_DATA_DIR)
    for tile in tileset.tiles:
        location = tile.dsi.south_west_corner
        assert tileset.get_elevation(location) == tile.get_elevation(location)

    with pytest.raises(NoElevationDataError):
        tileset.get_elevation(LatLon(0, 0))
    assert LatLon(0, 0) not in tileset


def test_load_and_unload_tile() -> None:
    """Test the load and unload example."""
    tiles = TileSet(TEST_DATA_DIR)
    tile = tiles.get_tile(LatLon(latitude=41.5, longitude=-70.25))
    tile.load_data()
    tile.data.max()
    tile.unload_data()
