""" Tests for dted/latlon.py """
import pytest
from typing import Tuple

from dted import latlon


# fmt: off
@pytest.mark.parametrize(
    "latitude, longitude",
    [(-100, 0), (100, 0), (0, -200), (0, 200)]
)
# fmt: on
def test_latlon_validation(latitude: float, longitude: float) -> None:
    """Test that the invalid latitude and longitudes raise errors."""
    with pytest.raises(ValueError):
        latlon.LatLon(latitude, longitude)


# fmt: off
@pytest.mark.parametrize(
    "latitude_str, longitude_str, expected_latitude, expected_longitude",
    [("423045N", "1170003.6W", 42.5125, -117.001)]
)
# fmt: on
def test_latlon_from_dted(
    latitude_str: str,
    longitude_str: str,
    expected_latitude: float,
    expected_longitude: float,
) -> None:
    """Test that DTED coordinate strings are parsed as expected."""
    result = latlon.LatLon.from_dted(latitude_str, longitude_str)
    assert result.latitude == expected_latitude
    assert result.longitude == expected_longitude


# fmt: off
@pytest.mark.parametrize(
    "degree, minute, second, expected",
    [(1, 0, 0, 1.0),
     (-1, 0, 0, -1.0),
     (1, 30, 0, 1.5),
     (1, 30, 45, 1.5125)]
)
# fmt: on
def test_dms_to_decimal(degree: int, minute: int, second: int, expected: float) -> None:
    """Tests for the `dms_to_decimal` function."""
    assert latlon.dms_to_decimal(degree, minute, second) == expected


# fmt: off
@pytest.mark.parametrize(
    "coordinate, expected",
    [("1234567", (123, 45, 67.0)),
     ("123456", (12, 34, 56.0)),
     ("1234567.8", (123, 45, 67.8)),
     ("123456.7", (12, 34, 56.7))]
)
# fmt: on
def test_parse_dms_coordinate(coordinate: str, expected: Tuple[int, int, float]) -> None:
    """Tests for the `parse_dms_coordinate` function."""
    assert latlon.parse_dms_coordinate(coordinate) == expected
