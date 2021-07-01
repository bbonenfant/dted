""" User Header Label (UHL) Record. """
from dataclasses import dataclass
from io import BytesIO
from typing import Optional, Tuple

from ..definitions import UHL_SIZE, _UTF8
from ..errors import InvalidFileError
from ..latlon import LatLon

_SENTINEL = b"UHL1"


@dataclass
class UserHeaderLabel:
    # noinspection PyUnresolvedReferences
    """Dataclass holding the contents of the User Header Label of a DTED file.

    Args:
        origin: The origin of the DTED file as a latitude-longitude coordinate.
        longitude_interval: Longitude data interval in seconds.
        latitude_interval: Latitude data interval in seconds.
        vertical_accuracy: Absolute vertical accuracy in meters
            (with 90% assurance that the linear errors will not exceed this value
             relative to mean sea level).
        security_code: The security code of the data (should be "U" for unclassified).
        reference: Unique reference number.
        shape: The shape of the gridded data as
            (number of longitude lines, number of latitude lines).
        multiple_accuracy: Whether multiple accuracy is enabled.
        _data: raw binary data
    """
    origin: LatLon
    longitude_interval: float
    latitude_interval: float
    vertical_accuracy: Optional[int]
    security_code: bytes
    reference: bytes
    shape: Tuple[int, int]
    multiple_accuracy: bool
    _data: bytes

    @classmethod
    def from_bytes(cls, data: bytes) -> "UserHeaderLabel":
        """Parse the User Header Label from the raw data of a DTED file.

        This section is defined to be exactly 80 bytes and therefore the input data
            must contain at least 80 bytes.

        Raises:
            ValueError: If not enough binary data is provided (at least 80 bytes).
            InvalidFileError: If the binary data does not start with "UHL1".
        """
        if len(data) < UHL_SIZE:
            raise ValueError(
                f"The User Header Label section is {UHL_SIZE} bytes "
                f"but was provided {len(data)} bytes"
            )

        buffered_data = BytesIO(data)
        sentinel = buffered_data.read(4)
        if sentinel != _SENTINEL:
            raise InvalidFileError(
                f"DTED files must start with '{_SENTINEL!r}'. Found: {sentinel!r}"
            )

        longitude_str = buffered_data.read(8).decode(_UTF8)
        latitude_str = buffered_data.read(8).decode(_UTF8)
        origin = LatLon.from_dted(latitude_str=latitude_str, longitude_str=longitude_str)
        longitude_interval = int(buffered_data.read(4)) / 10
        latitude_interval = int(buffered_data.read(4)) / 10
        vertical_accuracy_ = buffered_data.read(4)
        vertical_accuracy = None if b"NA" in vertical_accuracy_ else int(vertical_accuracy_)
        security_code = buffered_data.read(3)
        reference = buffered_data.read(12)
        shape = int(buffered_data.read(4)), int(buffered_data.read(4))
        multiple_accuracy = buffered_data.read(1) != b"0"
        return cls(
            origin=origin,
            longitude_interval=longitude_interval,
            latitude_interval=latitude_interval,
            vertical_accuracy=vertical_accuracy,
            security_code=security_code,
            reference=reference,
            shape=shape,
            multiple_accuracy=multiple_accuracy,
            _data=data,
        )
