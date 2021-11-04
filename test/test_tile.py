""" Tests for dted/tile.py """
import warnings
from dataclasses import astuple
from pathlib import Path
from warnings import catch_warnings

import numpy as np
import pytest

from dted import LatLon, Tile, tile
from dted.definitions import VOID_DATA_VALUE
from dted.errors import VoidDataWarning

TEST_DATA_DIR: Path = Path(__file__).parent / "data"
DTED_1_VOID_DATA_FILE = TEST_DATA_DIR / "n00_e006_3arc_v2.dt1"
DTED_2_NO_VOID_DATA_FILE = TEST_DATA_DIR / "n41_w071_1arc_v3.dt2"
DTED_2_RECT_RESOLUTION_DATA_FILE = TEST_DATA_DIR / "s55_w069_1arc_v3.dt2"


@pytest.fixture
def suppress_void_data_warning() -> None:
    """ Fixture to suppress VoidDataWarnings when we don't care. """
    warnings.simplefilter(action="ignore", category=VoidDataWarning)


def test_void_value_warning() -> None:
    """Test that a warning is raised when parsing a DTED file with void data."""
    for dted_file in (DTED_1_VOID_DATA_FILE, DTED_2_RECT_RESOLUTION_DATA_FILE):
        dted_tile = Tile(dted_file, in_memory=False)
        with pytest.warns(VoidDataWarning):
            dted_tile.load_data()
            assert VOID_DATA_VALUE in dted_tile.data


@pytest.mark.usefixtures("suppress_void_data_warning")
def test_rectangular_resolution() -> None:
    """Test that a DTED file where vertical resolution != horizontal resolution
    can be parsed.

    References:
        https://github.com/bbonenfant/dted/issues/1
    """
    with catch_warnings():
        dted_tile = Tile(DTED_2_RECT_RESOLUTION_DATA_FILE)
        assert dted_tile.data.size > 0


def test_raw_file_parse() -> None:
    """Test that elevation data parsed directly from a DTED file matches
    the elevation data loaded entirely into memory.
    """
    in_memory_file = Tile(DTED_2_NO_VOID_DATA_FILE, in_memory=True)
    out_memory_file = Tile(DTED_2_NO_VOID_DATA_FILE, in_memory=False)

    start_latitude, start_longitude = astuple(in_memory_file.dsi.south_west_corner)
    end_latitude, end_longitude = astuple(in_memory_file.dsi.north_east_corner)
    points_to_check = 51  # Don't check every point to keep test speedy.

    for latitude in np.linspace(start_latitude, end_latitude, points_to_check):
        for longitude in np.linspace(start_longitude, end_longitude, points_to_check):
            location = LatLon(latitude, longitude)
            in_memory_elevation = in_memory_file.get_elevation(location)
            out_memory_elevation = out_memory_file.get_elevation(location)
            assert in_memory_elevation == out_memory_elevation


# fmt: off
@pytest.mark.parametrize(
    "signed_magnitude, twos_complement",
    [(int("0000000000000000", 2), int("0000000000000000", 2)),
     (int("0111111111111111", 2), int("0111111111111111", 2)),
     (int("1000000000000001", 2), int("1111111111111111", 2)),
     (int("1010101010101010", 2), int("1101010101010110", 2))]
)
# fmt: on
def test_convert_signed_magnitude(signed_magnitude: int, twos_complement: int) -> None:
    """Test that conversion between signed magnitude and 2's complement for
    16 bit integers works as expected.
    """
    # Created non-writeable views to int16 arrays.
    signed_magnitude_view = np.array([signed_magnitude], dtype=">i2").view()
    signed_magnitude_view.setflags(write=False)
    twos_complement_view = np.array([twos_complement], dtype=">i2")
    twos_complement_view.setflags(write=False)
    assert tile._convert_signed_magnitude(signed_magnitude_view) == twos_complement_view
    assert tile._convert_signed_magnitude(twos_complement_view) == signed_magnitude_view
