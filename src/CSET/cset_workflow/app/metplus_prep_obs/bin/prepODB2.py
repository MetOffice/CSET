#!/usr/bin/env python3

r"""
Convert ODB2 data to MET ASCII format.

Paths can use strftime formatting and shell globs - all matching ODB2 files will be loaded into the same ASCII file.
Valid times can be either ISO timepoints or recurrences, and are used to replace any strftime patterns.

    ./prepODB2.py /path/to/%Y/%m/%Y%m%dT%H%MZ/*.odb \
            --valid-time 20010101T0000Z \
            --valid-time R4/20010102T0000Z/PT6H \
            --output obs.ascii
"""

import argparse
import logging
import sys
from contextlib import nullcontext

from odb2.odb2 import PrepODB2Pattern, valid_times_iterator

log = logging.getLogger(__name__)

COLUMN_INFO = """
ASCII Column Info:
 0 - Message_Type: uses PrepBUFR names where known, otherwise the ODB reportype@hdr value
 1 - Station_ID: statid@hdr
 2 - Valid_Time: date@hdr_time@hdr
 3 - Lat: lat@hdr
 4 - Lon: lon@hdr
 5 - Elevation: stalt@hdr
 6 - Variable_Name: uses ODB variable names from https://codes.ecmwf.int/odb/varno/
 7 - Level: is the observation pressure level (where available)
 8 - Height: is 0 for surface observations
 9 - QC_String: unused
10 - Observation_Value: obsvalue@body

https://metplus.readthedocs.io/projects/met/en/latest/Users_Guide/reformat_point.html#table-reformat-point-ascii2nc-format
"""


def main(argv: list[str]):
    """ODB2 to ASCII CLI."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=COLUMN_INFO,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "file",
        nargs="+",
        help="ODB2 files to load (can be strftime-formatted with values replaced using the list from --valid-times)",
    )
    parser.add_argument("--output", "-o", help="output path", default="-")
    parser.add_argument(
        "--valid-time",
        "-t",
        help="valid times to load (ISO format, e.g. '20100512T1200', 'R4/20010101T0000Z/PT6H')",
        action="append",
        default=["20010101T0000Z"],
    )
    parser.add_argument("--verbose", "-v", help="verbose", action="store_true")
    args = parser.parse_args(argv)

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
        sys.tracebacklimit = 0

    if args.output == "-":
        out_context = nullcontext(sys.stdout)
    else:
        out_context = open(args.output, "wt")

    with out_context as output:
        for pattern in args.file:
            PrepODB2Pattern(pattern).odb2ascii(
                output, valid_times_iterator(args.valid_time)
            )


if __name__ == "__main__":
    main(sys.argv[1:])
