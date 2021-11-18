""" Data Set Identification (DSI) Record. """
from dataclasses import dataclass
from datetime import date, datetime
from io import BytesIO
from typing import Optional, Tuple

from ..definitions import DSI_SIZE, _UTF8
from ..errors import InvalidFileError
from ..latlon import LatLon

_SENTINEL = b"DSI"


@dataclass
class DataSetIdentification:
    # noinspection PyUnresolvedReferences
    """Dataclass holding the contents of the Data Set Identification section of a DTED file.

    Args:
        security_code: The security code of the data (should be "U" for unclassified).
        release_markings: Security control and release markings.
        handling_description: Security handling description.
        product_level: DMA Series designator for product level (i.e. DTED1 or DTED2).
        reference: Unique reference number.
        edition: Data edition number (number between 1 and 99).
        merge_version: match or merge version (single character A-Z).
        maintenance_date: Date of last maintenance (if it exists).
            Note: Only year and month are provided -- no day specified.
        merge_date: Date of last merge (if it exists).
            Note: Only year and month are provided -- no day specified.
        maintenance_code: Maintenance description code.
        producer_code: Code specifying the producer.
        product_specification: Code specifying the product.
        specification_date: Date of the product specification.
        vertical_datum: The name of the vertical datum used to define elevation.
        horizontal_datum: The name of the horizontal datum used.
        collection_system: The name of the digitizing or collection system.
        compilation_date: The date that the data was compiled.

        origin: The origin of the DTED file as a latitude-longitude coordinate.
        south_west_corner: The south west corner of the DTED data.
        north_west_corner: The north west corner of the DTED data.
        north_east_corner: The north east corner of the DTED data.
        south_east_corner: The south east corner of the DTED data.
        orientation: Clockwise orientation angle of data with respect to true North
            (This will usually be 0 for DTED).
        longitude_interval: Longitude data interval in seconds.
        latitude_interval: Latitude data interval in seconds.
        vertical_accuracy: Absolute vertical accuracy in meters
            (with 90% assurance that the linear errors will not exceed this value
             relative to mean sea level).
        shape: The shape of the gridded data as
            (number of longitude lines, number of latitude lines).
        coverage: Percentage of the cell covered by the DTED data.
        _data: raw binary data
    """
    security_code: str
    release_markings: bytes
    handling_description: str
    product_level: str
    reference: bytes
    edition: int
    merge_version: str
    maintenance_date: Optional[date]
    merge_date: Optional[date]
    maintenance_code: bytes
    producer_code: bytes
    product_specification: bytes
    specification_date: Optional[date]
    vertical_datum: str
    horizontal_datum: str
    collection_system: str
    compilation_date: Optional[date]

    origin: LatLon
    south_west_corner: LatLon
    north_west_corner: LatLon
    north_east_corner: LatLon
    south_east_corner: LatLon
    orientation: float
    latitude_interval: float
    longitude_interval: float
    shape: Tuple[int, int]
    coverage: float
    _data: bytes

    @classmethod
    def from_bytes(cls, data: bytes) -> "DataSetIdentification":
        """Parse the Data Set Identification record from the raw data of a DTED file.

        This record is defined to be exactly 648 bytes and therefore the input data
            must contain at least 648 bytes.

        Raises:
            ValueError: If not enough binary data is provided (at least 648 bytes).
            InvalidFileError: If the binary data does not start with "DSI".
        """
        if len(data) < DSI_SIZE:
            raise ValueError(
                f"The Data Set Identification record is {DSI_SIZE} bytes "
                f"but was provided {len(data)} bytes"
            )

        buffered_data = BytesIO(data)
        sentinel = buffered_data.read(3)
        if sentinel != _SENTINEL:
            raise InvalidFileError(
                f"Data Set Identification Records must start with '{_SENTINEL!r}'. "
                f"Found: {sentinel!r}"
            )

        security_code = buffered_data.read(1).decode(_UTF8)
        release_markings = buffered_data.read(2)
        handling_description = buffered_data.read(27).decode(_UTF8)
        _ = buffered_data.read(26)
        product_level = buffered_data.read(5).decode(_UTF8)
        reference = buffered_data.read(15)
        _ = buffered_data.read(8)
        edition = int(buffered_data.read(2))
        merge_version = buffered_data.read(1).decode(_UTF8)
        maintenance_date = parse_month_date(buffered_data.read(4).decode(_UTF8))
        merge_date = parse_month_date(buffered_data.read(4).decode(_UTF8))
        maintenance_code = buffered_data.read(4)
        producer_code = buffered_data.read(8)
        _ = buffered_data.read(16)
        product_specification = buffered_data.read(11)
        specification_date = parse_month_date(buffered_data.read(4).decode(_UTF8))
        vertical_datum = buffered_data.read(3).decode(_UTF8)
        horizontal_datum = buffered_data.read(5).decode(_UTF8)
        collection_system = buffered_data.read(10).decode(_UTF8)
        compilation_date = parse_month_date(buffered_data.read(4).decode(_UTF8))
        _ = buffered_data.read(22)

        origin = LatLon.from_dted(
            latitude_str=buffered_data.read(9).decode(_UTF8),
            longitude_str=buffered_data.read(10).decode(_UTF8),
        )
        south_west_corner = LatLon.from_dted(
            latitude_str=buffered_data.read(7).decode(_UTF8),
            longitude_str=buffered_data.read(8).decode(_UTF8),
        )
        north_west_corner = LatLon.from_dted(
            latitude_str=buffered_data.read(7).decode(_UTF8),
            longitude_str=buffered_data.read(8).decode(_UTF8),
        )
        north_east_corner = LatLon.from_dted(
            latitude_str=buffered_data.read(7).decode(_UTF8),
            longitude_str=buffered_data.read(8).decode(_UTF8),
        )
        south_east_corner = LatLon.from_dted(
            latitude_str=buffered_data.read(7).decode(_UTF8),
            longitude_str=buffered_data.read(8).decode(_UTF8),
        )
        orientation = float(buffered_data.read(9))
        latitude_interval = int(buffered_data.read(4)) / 10
        longitude_interval = int(buffered_data.read(4)) / 10
        shape = (int(buffered_data.read(4)), int(buffered_data.read(4)))[::-1]
        coverage = float(buffered_data.read(2))
        coverage = 1 if coverage == 0 else coverage

        return cls(
            security_code=security_code,
            release_markings=release_markings,
            handling_description=handling_description,
            product_level=product_level,
            reference=reference,
            edition=edition,
            merge_version=merge_version,
            maintenance_date=maintenance_date,
            merge_date=merge_date,
            maintenance_code=maintenance_code,
            producer_code=producer_code,
            product_specification=product_specification,
            specification_date=specification_date,
            vertical_datum=vertical_datum,
            horizontal_datum=horizontal_datum,
            collection_system=collection_system,
            compilation_date=compilation_date,
            origin=origin,
            south_west_corner=south_west_corner,
            north_west_corner=north_west_corner,
            north_east_corner=north_east_corner,
            south_east_corner=south_east_corner,
            orientation=orientation,
            latitude_interval=latitude_interval,
            longitude_interval=longitude_interval,
            shape=shape,
            coverage=coverage,
            _data=data,
        )

    @property
    def data_block_length(self) -> int:
        """Returns the length (in bytes) of a block of data
        within the Data Record of the DTED file containing this DSI record.
        """
        return 12 + (2 * self.shape[1])


def parse_month_date(date_str: str) -> Optional[date]:
    """Parse a nullable DTED date string.

    The DTED date string is of the format YYMM where 0000 is a null value.
    """
    if date_str[2:] == "00":
        return None
    return datetime.strptime(date_str, "%y%m").date()
