""" Implementation of a Latitude-Longitude coordinate. """
from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class LatLon:
    latitude: float
    longitude: float

    @classmethod
    def from_dted(cls, latitude_str: str, longitude_str: str) -> "LatLon":
        """Constructs a LatLon object from DTED records coordinates in the
        format ([D]DDMMSS[.S]H) where
            D: degree value
            M: minute value
            S: second value
            H: hemisphere

        Args:
            latitude_str: DTED record for the latitude coordinate.
            longitude_str: DTED record for the longitude coordinate.
        """
        lat_sign = -1 if latitude_str[-1] == "S" else 1
        latitude = lat_sign * dms_to_decimal(*parse_dms_coordinate(latitude_str[:-1]))

        lon_sign = -1 if longitude_str[-1] == "W" else 1
        longitude = lon_sign * dms_to_decimal(*parse_dms_coordinate(longitude_str[:-1]))
        return cls(latitude, longitude)

    def format(self, precision: int) -> str:
        """Format a LatLon coordinate with the specified precision into a string.

        The string format is the following:
            (Latitude [N/S], Longitude [E/W])

        Example:
             >>> LatLon(41.26, -70).format(1) == "(41.3N,70.0W)"

        Args:
            precision: The decimal precision used to format the decimal-degree coordinates.

        Raises:
            ValueError: If the decimal precision is not positive.

        Returns:
            Formatted string.
        """
        if precision < 0:
            raise ValueError(f"Precision value must be positive. Found: {precision}")

        latitude_hemisphere = "N" if self.latitude >= 0 else "S"
        longitude_hemisphere = "E" if self.longitude >= 0 else "W"
        latitude_str = f"{abs(self.latitude):.{precision}f}{latitude_hemisphere}"
        longitude_str = f"{abs(self.longitude):.{precision}f}{longitude_hemisphere}"
        return f"({latitude_str},{longitude_str})"

    def __post_init__(self) -> None:
        """Simple validation of a LatLon point."""
        if not -90 <= self.latitude <= 90:
            raise ValueError(
                f"Latitude value must be between -90 and 90. Found: {self.latitude}"
            )
        if not -180 <= self.longitude <= 180:
            raise ValueError(
                f"Longitude value must be between -180 and 180. Found: {self.longitude}"
            )


def dms_to_decimal(degree: int, minute: int, second: float) -> float:
    """Converts a degree-minute-second coordinate to a decimal-degree coordinate."""
    return degree + ((minute + (second / 60)) / 60)


def parse_dms_coordinate(coordinate: str) -> Tuple[int, int, float]:
    """Parse a degree-minute-second coordinate from a DTED coordinate string.

    The DTED coordinate string has the following format:
        [D]DDMMSS[.S]
    where:
        D - Degree
        M - Minute
        S - Second

    Args:
        coordinate: DTED coordinate string (without the hemisphere identifier).

    Returns:
        degree-minute-second coordinate as a tuple of the following types:
            (degree: int, minute: int, second: float)
    """
    seconds_index = -4 if coordinate[-2] == "." else -2
    minutes_index = seconds_index - 2
    degrees = int(coordinate[:minutes_index])
    minutes = int(coordinate[minutes_index:seconds_index])
    seconds = float(coordinate[seconds_index:])
    return degrees, minutes, seconds
