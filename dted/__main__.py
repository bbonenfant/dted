""" CLI to easily access DTED data from the command line. """
import os
import sys
from argparse import ArgumentParser, RawTextHelpFormatter
from pathlib import Path
from typing import NoReturn, Set

import numpy as np

from .definitions import VOID_DATA_VALUE
from .errors import InvalidFileError, NoElevationDataError
from .latlon import LatLon
from .tile import Tile

_DESCRIPTION = (
    "Simple interface for interacting with DTED file. \n"
    "  > Run this command on a DTED file for a high level description of the file. \n"
    "  > Provide a location to look up its approximate terrain elevation. \n"
    "  > Display a low-resolution ASCII representation of a DTED file within your terminal."
)


def main() -> None:
    """Run the CLI."""
    parser = ArgumentParser(description=_DESCRIPTION)
    parser.formatter_class = RawTextHelpFormatter
    parser.add_argument("file", type=Path, help="Path to a DTED file. ")
    parser.add_argument(
        "-l",
        "--location",
        type=float,
        nargs=2,
        metavar=("LATITUDE", "LONGITUDE"),
        help=(
            "Location at which to look up terrain elevation. \n"
            "Coordinate values are expected to be in decimal degrees. "
        ),
    )
    parser.add_argument(
        "--display",
        action="store_true",
        help=(
            "Display a low-resolution ASCII representation of a DTED file. \n"
            "This chart is scaled to fit within your terminal window, thereby \n"
            "the resolution can be increased by expanding your terminal window. "
        ),
    )
    args = parser.parse_args()

    try:
        tile = Tile(args.file, in_memory=False)
    except FileNotFoundError:
        error(f"DTED file not found: {args.file}")
    except InvalidFileError as err:
        error(f"Invalid DTED file: {err}")

    if args.display:
        print(generate_chart(tile))
    elif args.location is None:
        print(generate_report(tile))
    else:
        try:
            location = LatLon(*args.location)
        except ValueError as err:
            error(f"Invalid location specified: {err}")
        try:
            elevation = tile.get_elevation(location)
        except NoElevationDataError as err:
            error(str(err))
        print(f"{elevation:.1f} meters")


def generate_chart(tile: Tile) -> str:
    """Generate a low resolution heat map plot of the DTED tile from ASCII characters."""
    # Load the terrain elevation data into memory and replace void values with 0.
    tile.load_data(perform_checksum=True)
    elevation_data = tile.data
    elevation_data[elevation_data == VOID_DATA_VALUE] = 0

    # Determine the maximum height of the ASCII chart.
    terminal_size = os.get_terminal_size()
    maximum_chart_height = min(terminal_size.lines, terminal_size.columns // 2) - 10
    if maximum_chart_height < 5:
        error(
            "Error displaying DTED file within the terminal. "
            "Please increase the size of your terminal window. "
        )

    # Down-sample the elevation data to fit the terminal screen.
    raw_block_count = max(tile.data.shape) - 1
    step = raw_block_count // max(
        factor for factor in factors(raw_block_count) if factor < maximum_chart_height
    )
    sampled_data = tile.data.T[::-step, :: (step // 2)]

    # Bin the data into 5 equally spaced bins
    min_elevation, max_elevation = sampled_data.min(), sampled_data.max()
    if min_elevation > 0:
        bins = np.linspace(min_elevation, max_elevation + 1, 5)
    else:
        # Handle cases where DTED has <= 0 MSL values to make the chart nicer.
        bins = np.insert(np.linspace(1, max_elevation, 4), 0, min_elevation)
    binned_data = np.digitize(sampled_data, bins)

    # Create the chart.
    chart = ["".join(["X ░▒▓█"[index] for index in array]) for array in binned_data]
    framed_chart = [
        "┏" + "━" * binned_data.shape[1] + "┓",
        *(f"┃{line}┃" for line in chart),
        "┗" + "━" * binned_data.shape[1] + "┛",
    ]
    legend = [
        f"{lower:5.1f}m <= {symbol} < {upper:5.1f}m"
        for symbol, lower, upper in zip("☐░▒▓█", bins, bins[1:])
    ]
    header = [""] * (terminal_size.lines - len(framed_chart) - len(legend) - 2)
    header.append(f"File: {tile.file}")
    return "\n".join(
        line.center(terminal_size.columns) for line in (header + framed_chart + legend)
    )


def generate_report(tile: Tile) -> str:
    """Generate a pretty-printed high-level report on the provided DTED tile."""
    # Preformat some data.
    compilation_date = ""
    if tile.dsi.compilation_date is not None:
        compilation_date = tile.dsi.compilation_date.strftime("%m/%Y")
    maintenance_date = ""
    if tile.dsi.maintenance_date is not None:
        maintenance_date = tile.dsi.maintenance_date.strftime("%m/%Y")
    nw = tile.dsi.north_west_corner.format(1)
    ne = tile.dsi.north_east_corner.format(1)
    sw = tile.dsi.south_west_corner.format(1)
    se = tile.dsi.south_east_corner.format(1)
    resolution = f'{tile.dsi.latitude_interval:.1f}"/{tile.dsi.longitude_interval:.1f}"'
    accuracy = f"{tile.acc.absolute_vertical}m/{tile.acc.absolute_horizontal}m"

    # Generate the report.
    return "\n".join(
        [
            f"File Path:          {tile.file} ({tile.file.stat().st_size >> 20} MB)",
            f"Product Level:      {tile.dsi.product_level}",
            f"Security Code:      {tile.dsi.security_code}",
            f"Compilation Date:   {compilation_date}",
            f"Maintenance Date:   {maintenance_date}",
            f"Datums (V/H):       {tile.dsi.vertical_datum}/{tile.dsi.horizontal_datum}",
            f"",
            f"    {nw}      {ne}",
            f"          NW --------------- NE     ",
            f"          |                   |     ",
            f"          |                   |     ",
            f"          |                   |     ",
            f"          |                   |     ",
            f"          |                   |     ",
            f"          |                   |     ",
            f"          SW --------------- SE     ",
            f"    {sw}      {se}",
            f"",
            f"Origin:                 {tile.dsi.origin.format(1)}",
            f"Resolution (lat/lon):   {resolution}",
            f"Accuracy (V/H):         {accuracy}",
        ]
    )


def error(message: str) -> NoReturn:
    """Print an error to the screen and exit."""
    print(f"ERROR | {message}", file=sys.stderr)
    sys.exit(1)


def factors(n: int) -> Set[int]:
    """Helper function to get the factors of an integer.

    Shamelessly copied and pasted from StackOverflow.
    """
    return set(
        factor for i in range(1, int(n ** 0.5) + 1) if n % i == 0 for factor in (i, n // i)
    )


if __name__ == "__main__":
    main()
