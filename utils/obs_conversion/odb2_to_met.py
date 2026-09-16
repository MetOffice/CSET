#!/usr/bin/env python3
"""Convert ODB2 files to MET format."""

import argparse
from pathlib import Path

from .met import to_ascii, to_point_nc
from .odb2 import odb2_to_obs_dataframe


def main():
    """CLI for converting ODB2 files to MET format."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_files", nargs="+", type=Path, help="Input ODB2 files")
    parser.add_argument("--format", choices=["netcdf", "ascii"], default="netcdf")
    parser.add_argument(
        "-o", "--output", type=Path, required=True, help="Output MET file"
    )
    args = parser.parse_args()

    data = odb2_to_obs_dataframe(args.input_files)
    if args.format == "netcdf":
        nc = to_point_nc(data)
        nc.to_netcdf(args.output)  # type: ignore
    else:
        ascii_data = to_ascii(data)
        ascii_data.to_csv(args.output, index=False, header=False, sep="\t")


if __name__ == "__main__":
    main()
