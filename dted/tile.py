""" Implementation of a DTED tile. """

from dataclasses import astuple
from pathlib import Path
from struct import unpack
from typing import Optional, Union
from warnings import warn as emit_warning

import numpy as np
import numpy.typing as npt

from .definitions import ACC_SIZE, DSI_SIZE, UHL_SIZE, VOID_DATA_VALUE
from .errors import InvalidFileError, NoElevationDataError, VoidDataWarning
from .latlon import LatLon
from .records import AccuracyDescription, DataSetIdentification, UserHeaderLabel


_FilePath = Union[str, Path]
_DATA_SENTINEL = 0xAA


class Tile:
    # noinspection PyUnresolvedReferences
    """An API for accessing data within a DTED file.

    When this class is initialized with a path to a DTED file, the metadata records
      associated with the DTED file will always parsed and the terrain elevation data
      will optionally be parsed (defaults to being parsed).

    By not loading all of the terrain elevation data into memory, you can quickly
      perform elevation lookups on raw files.

    Attributes:
        file: The path to the DTED file.
        uhl: Parsed User Header Label (UHL) record from the DTED file.
        dsi: Parsed Data Set Identification (DSI) record from the DTED file.
        acc: Parsed Accuracy Description (ACC) record from the DTED file.
        data: The (optionally loaded) raw terrain elevation data from the DTED file.

    Methods:
        get_elevation: Lookup the terrain elevation at a particular location.
            Data does not need to be loaded into memory to perform this operation.
        load_data: Load the terrain elevation data into memory from the DTED file.
            Note: by default this is done automatically during class initialization.
        __contains__: Check whether a LatLon point is contained within the DTED file.

    Examples:

        Access metadata within a DTED file.
        >>> from dted import Tile
        >>> dted_file: Path
        >>> tile = Tile(dted_file)
        >>> tile.dsi.origin
        LatLon(latitude=41.0, longitude=-71.0)

        Read a DTED file and get the maximum terrain elevation
        >>> from dted import Tile
        >>> dted_file: Path
        >>> tile = Tile(dted_file)
        >>> tile.data.max()
        125

        Quickly lookup terrain elevation at a specific location within a DTED file.
        >>> from dted import LatLon, Tile
        >>> dted_file: Path
        >>> tile = Tile(dted_file, in_memory=False)
        >>> tile.get_elevation(LatLon(latitude=41.36, longitude=-70.55))
        -21

        Check if location is covered by a DTED file.
        >>> from dted import LatLon, Tile
        >>> dted_file: Path
        >>> tile = Tile(dted_file)
        >>> LatLon(latitude=41.5, longitude=-70.25) in tile
        True

        Load DTED data into memory fast with minimal checks.
        >>> from dted import Tile
        >>> dted_file: Path
        >>> tile = Tile(dted_file, in_memory=False)
        >>> tile.load_data(perform_checksum=False)

    References:
        SRTM DTED Specification:
            https://www.dlr.de/eoc/Portaldata/60/Resources/dokumente/7_sat_miss/SRTM-XSAR-DEM-DTED-1.1.pdf
    """

    def __init__(self, file: _FilePath, *, in_memory: bool = True, warn: bool = True):
        """
        Args:
            file: The DTED file to parse.
            in_memory: Whether to read the elevation data into memory.
                If in_memory is False, elevation data can still be accessed at
                individual points directly from the file.
            warn: Whether to emit the warning if void data is detected within
                the DTED file. Defaults to True.
        """
        self.file = Path(file)
        self._data: Optional[npt.NDArray[np.int16]] = None
        self._warn = warn

        with self.file.open("rb") as f:
            self.uhl = UserHeaderLabel.from_bytes(f.read(UHL_SIZE))
            self.dsi = DataSetIdentification.from_bytes(f.read(DSI_SIZE))
            self.acc = AccuracyDescription.from_bytes(f.read(ACC_SIZE))

        if in_memory:
            self.load_data()

    @property
    def data(self) -> np.ndarray:
        """Access the elevation data, if it has been read into memory."""
        if self._data is not None:
            return self._data
        raise ValueError("Data not loaded into memory. ")

    def get_elevation(self, latlon: LatLon) -> int:
        """Lookup the terrain elevation at the specified location.

        This will return the elevation of the explicitly defined DTED point
            nearest to the specified location.

        Args:
            latlon: The location at which to lookup the terrain elevation.

        Raises:
            NoElevationDataError: If the specified location is not contained within the
                DTED file.
        """
        if latlon not in self:
            raise NoElevationDataError(
                f"Specified location is not contained within DTED file: {latlon.format(1)}"
            )

        origin_latitude, origin_longitude = astuple(self.dsi.origin)
        lon_count, lat_count = self.dsi.shape
        latitude_index = round((latlon.latitude - origin_latitude) * (lat_count - 1))
        longitude_index = round((latlon.longitude - origin_longitude) * (lon_count - 1))

        if self._data is not None:
            return int(self._data[longitude_index, latitude_index])

        with self.file.open("rb") as f:
            block_length = self.dsi.data_block_length
            f.seek(UHL_SIZE + DSI_SIZE + ACC_SIZE + (longitude_index * block_length))
            data_block = _parse_data_block(f.read(block_length), perform_checksum=True)
            data_block = _convert_signed_magnitude(data_block)
            return int(data_block[latitude_index])

    def load_data(
        self, *, perform_checksum: bool = True, warn: Optional[bool] = None
    ) -> None:
        """Load the elevation data into memory.

        This loaded elevation data can be accessed through the `self.data` attribute.

        Args:
            perform_checksum: Whether to perform the checksum for each data block.
                The user is allowed to toggle this off, but it is strongly suggested
                that the checksums be performed.
            warn: Whether to emit the warning if void data is detected within
                the DTED file. Defaults to value set at initialization.

        Raises:
            InvalidFileError: If a data block fails its checksum.

        Warnings:
            VoidDataWarning: If void data is detected within the DTED file.
        """
        if isinstance(self._data, np.ndarray) and self._data.size > 0:
            # Data already loaded, no need to reload.
            return

        # Open the file, seek to the data blocks, and start parsing.
        with self.file.open("rb") as f:
            f.seek(UHL_SIZE + DSI_SIZE + ACC_SIZE)
            data_record = f.read()

        block_length = self.dsi.data_block_length
        parsed_data_blocks = [
            _parse_data_block(
                block=data_record[column * block_length : (column + 1) * block_length],
                perform_checksum=perform_checksum,
            )
            for column in range(self.dsi.shape[0])
        ]
        self._data = _convert_signed_magnitude(np.asarray(parsed_data_blocks))

        warn = self._warn if warn is None else warn
        if warn and VOID_DATA_VALUE in self._data:
            emit_warning(  # Void Data Warning  )
                f"\n\tVoid data has been detected within the DTED file ({self.file}). "
                f"\n\tThis can happen when DTED data is not specified over bodies of water. "
                f"\n\tThis does not mean the DTED data is invalid, but you must handle this "
                f"\n\t data carefully. VOID_DATA_VALUE={VOID_DATA_VALUE}",
                category=VoidDataWarning,
            )

    def unload_data(self) -> None:
        """Unload the elevation memory from memory."""
        del self._data
        self._data = None

    def __contains__(self, item: LatLon) -> bool:
        """Determines whether a location is covered by the DTED file."""
        if not isinstance(item, LatLon):
            raise TypeError(f"Expected LatLon -- Found: {item}")

        minimum_latitude, minimum_longitude = astuple(self.dsi.south_west_corner)
        maximum_latitude, maximum_longitude = astuple(self.dsi.north_east_corner)
        within_latitude_band = minimum_latitude <= item.latitude <= maximum_latitude
        within_longitude_band = minimum_longitude <= item.longitude <= maximum_longitude
        return within_latitude_band and within_longitude_band

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Tile) and (hash(self) == hash(other))

    def __hash__(self) -> int:
        """The hash of a Tile is set by the hash of the file metadata.
        The elevation data is not considered, and therefore it is assumed that
          files with the same metadata are identical.
        """
        return hash((self.acc, self.dsi, self.uhl))


def _parse_data_block(block: bytes, perform_checksum: bool) -> npt.NDArray[np.int16]:
    """Parse an individual block of data.

    Args:
        block: A single data block of raw binary data.
        perform_checksum: Whether to perform the checksum verification.

    Returns:
        Parsed terrain elevation data as a numpy array. NOTE: This elevation is data
          is _not_ converted from signed-magnitude representation. This is not done
          in this step to optimize the file parsing.

    Raises:
        InvalidFileError: If the checksum fails verification or the data block is malformed.
    """
    if perform_checksum:
        checksum = unpack(">i", block[-4:])[0]
        sum_ = np.frombuffer(block[:-4], dtype=">B").sum()
        if sum_ != checksum:
            block_index = (_DATA_SENTINEL << 24) - unpack(">I", block[:4])[0]
            raise InvalidFileError(
                f"Checksum failed for data block {block_index}. "
                f"Expected {checksum} -- Found {sum_} "
            )
    if block[0] != _DATA_SENTINEL:
        raise InvalidFileError(
            f"All data blocks within a DTED file must begin with {_DATA_SENTINEL}. "
            f"Found: {block[0]}"
        )

    return np.frombuffer(block[8:-4], dtype=">i2")


def _convert_signed_magnitude(data: npt.NDArray[np.int16]) -> npt.NDArray[np.int16]:
    """Converts a numpy array of binary 16 bit integers between
    signed magnitude and 2's complement.
    """
    if not data.flags.writeable:
        data = data.copy()
    negatives = data < 0
    data[negatives] = np.array(-32768).astype(">i2") - data[negatives]
    return data
