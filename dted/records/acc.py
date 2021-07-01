""" Accuracy Description (ACC) Record. """
from dataclasses import dataclass
from io import BytesIO
from typing import Optional

from ..definitions import ACC_SIZE
from ..errors import InvalidFileError

_SENTINEL = b"ACC"


@dataclass
class AccuracyDescription:
    # noinspection PyUnresolvedReferences
    """Dataclass holding the contents of the Data Set Identification section of a DTED file.

    Args:
        absolute_horizontal: Absolute horizontal accuracy of the data, if available.
        absolute_vertical: Absolute vertical accuracy of the data, if available.
        relative_horizontal: Relative (point-to-point) horizontal accuracy, if available.
        relative_vertical: Relative (point-to-point) vertical accuracy, if available.
        _data: raw binary data
    """
    absolute_horizontal: Optional[int]
    absolute_vertical: Optional[int]
    relative_horizontal: Optional[int]
    relative_vertical: Optional[int]
    _data: bytes

    @classmethod
    def from_bytes(cls, data: bytes) -> "AccuracyDescription":
        """Parse the Accuracy Description record from the raw data of a DTED file.

        This record is defined to be exactly 2700 bytes and therefore the input data
            must contain at least 2700 bytes.

        Raises:
            ValueError: If not enough binary data is provided (at least 2700 bytes).
            InvalidFileError: If the binary data does not start with "ACC".
        """
        if len(data) < ACC_SIZE:
            raise ValueError(
                f"The Accuracy Description record is {ACC_SIZE} bytes "
                f"but was provided {len(data)} bytes"
            )

        buffered_data = BytesIO(data)
        sentinel = buffered_data.read(3)
        if sentinel != _SENTINEL:
            raise InvalidFileError(
                f"Accuracy Description Records must start with '{_SENTINEL!r}'. "
                f"Found: {sentinel!r}"
            )
        abs_horizontal = buffered_data.read(4)
        abs_vertical = buffered_data.read(4)
        rel_horizontal = buffered_data.read(4)
        rel_vertical = buffered_data.read(4)
        return cls(
            absolute_horizontal=None if b"NA" in abs_horizontal else int(abs_horizontal),
            absolute_vertical=None if b"NA" in abs_vertical else int(abs_vertical),
            relative_horizontal=None if b"NA" in rel_horizontal else int(rel_horizontal),
            relative_vertical=None if b"NA" in rel_vertical else int(rel_vertical),
            _data=data,
        )
