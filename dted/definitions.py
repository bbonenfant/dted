""" Definitions used to parse DTED files. """

from pathlib import Path
from typing import Union

# Definitions of DTED Record lengths.
UHL_SIZE = 80
DSI_SIZE = 648
ACC_SIZE = 2700

# Definitions of the value DTED uses for void data.
VOID_DATA_VALUE = (-1 << 15) + 1


_FilePath = Union[str, Path]
_UTF8 = "utf-8"
