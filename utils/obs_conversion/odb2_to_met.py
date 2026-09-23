#!/usr/bin/env python3
"""Convert ODB2 files to MET format."""

import argparse
from pathlib import Path

from .met import save_obs_dataframe_as_met
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
    save_obs_dataframe_as_met(data, output=args.output, format=args.format)


if __name__ == "__main__":
    main()
