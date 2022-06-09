""" Tests for dted/tile.py """
import warnings
from dataclasses import astuple
from pathlib import Path
from typing import Any

import numpy as np
import pytest

import dted
from dted import LatLon, Tile
from dted.definitions import VOID_DATA_VALUE
from dted.errors import VoidDataWarning

TEST_DATA_DIR: Path = Path(__file__).parent / "data"
DTED_1_VOID_DATA_FILE = TEST_DATA_DIR / "n00_e006_3arc_v2.dt1"
DTED_2_NO_VOID_DATA_FILE = TEST_DATA_DIR / "n41_w071_1arc_v3.dt2"
DTED_2_RECT_RESOLUTION_DATA_FILE = TEST_DATA_DIR / "s55_w069_1arc_v3.dt2"


@pytest.fixture
def suppress_void_data_warning() -> None:
    """Fixture to suppress VoidDataWarnings when we don't care."""
    warnings.simplefilter(action="ignore", category=VoidDataWarning)


@pytest.fixture(
    name="dted_file",
    params=[
        DTED_1_VOID_DATA_FILE,
        DTED_2_NO_VOID_DATA_FILE,
        DTED_2_RECT_RESOLUTION_DATA_FILE,
    ],
)
def _dted_file(request: Any) -> Path:
    """Fixture to parametrize over the test DTED files."""
    return request.param


def test_void_value_warning() -> None:
    """Test that a warning is raised when parsing a DTED file with void data."""
    for dted_file in (DTED_1_VOID_DATA_FILE, DTED_2_RECT_RESOLUTION_DATA_FILE):
        tile = Tile(dted_file, in_memory=False)
        with pytest.warns(VoidDataWarning):
            tile.load_data()
            assert VOID_DATA_VALUE in tile.data


@pytest.mark.usefixtures("suppress_void_data_warning")
def test_rectangular_resolution() -> None:
    """Test that a DTED file where vertical resolution != horizontal resolution
    can be parsed.

    References:
        https://github.com/bbonenfant/dted/issues/1
    """
    tile = Tile(DTED_2_RECT_RESOLUTION_DATA_FILE)
    assert tile.data.size > 0


@pytest.mark.usefixtures("suppress_void_data_warning")
def test_raw_file_parse(dted_file: Path) -> None:
    """Test that elevation data parsed directly from a DTED file matches
    the elevation data loaded entirely into memory.
    """
    in_memory_tile = Tile(dted_file, in_memory=True)
    out_memory_tile = Tile(dted_file, in_memory=False)

    start_latitude, start_longitude = astuple(in_memory_tile.dsi.south_west_corner)
    end_latitude, end_longitude = astuple(in_memory_tile.dsi.north_east_corner)
    points_to_check = 50  # Don't check every point to keep test speedy.

    for latitude in np.linspace(start_latitude, end_latitude, points_to_check):
        for longitude in np.linspace(start_longitude, end_longitude, points_to_check):
            location = LatLon(latitude, longitude)
            in_memory_elevation = in_memory_tile.get_elevation(location)
            out_memory_elevation = out_memory_tile.get_elevation(location)
            assert in_memory_elevation == out_memory_elevation


@pytest.mark.usefixtures("suppress_void_data_warning")
def test_sanity_check_parsing(dted_file: Path) -> None:
    """Perform a sanity check that elevation lookups are performed correctly
    at the corners of the tile.
    """
    tile = Tile(dted_file, in_memory=True)

    assert tile.get_elevation(tile.dsi.south_west_corner) == tile.data[0, 0]
    assert tile.get_elevation(tile.dsi.north_west_corner) == tile.data[0, -1]
    assert tile.get_elevation(tile.dsi.south_east_corner) == tile.data[-1, 0]
    assert tile.get_elevation(tile.dsi.north_east_corner) == tile.data[-1, -1]


@pytest.mark.usefixtures("suppress_void_data_warning")
def test_data_shape(dted_file: Path) -> None:
    tile = Tile(dted_file, in_memory=True)
    assert tile.data.shape == tile.dsi.shape == tile.uhl.shape
    assert tile.dsi.latitude_interval == tile.uhl.latitude_interval
    assert tile.dsi.longitude_interval == tile.uhl.longitude_interval


# fmt: off
@pytest.mark.parametrize(
    "signed_magnitude, twos_complement",
    [(int("0000000000000000", 2), int("0000000000000000", 2)),
     (int("0111111111111111", 2), int("0111111111111111", 2)),
     (int("1000000000000001", 2), int("1111111111111111", 2)),
     (int("1010101010101010", 2), int("1101010101010110", 2))]
)
def test_convert_signed_magnitude(signed_magnitude: int, twos_complement: int) -> None:
    """Test that conversion between signed magnitude and 2's complement for
    16 bit integers works as expected.
    """
    # Created non-writeable views to int16 arrays.
    signed_magnitude_view = np.array([signed_magnitude], dtype=">i2").view()
    signed_magnitude_view.setflags(write=False)
    twos_complement_view = np.array([twos_complement], dtype=">i2")
    twos_complement_view.setflags(write=False)
    assert dted.tile._convert_signed_magnitude(signed_magnitude_view) == twos_complement_view
    assert dted.tile._convert_signed_magnitude(twos_complement_view) == signed_magnitude_view
# fmt: on
