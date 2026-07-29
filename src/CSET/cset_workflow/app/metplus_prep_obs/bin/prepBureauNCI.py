#!/usr/bin/env python3

r"""
Convert Bureau ODB2 data at NCI to MET ASCII format.

Valid times can be either ISO timepoints or recurrences, and are used to replace any strftime patterns.
Data is sourced from the mirror in the ig2 project, not all times are available.

    ./prepBureauNCI.py \
            --system access-c3-dn \
            --valid-time 20010101T0000Z \
            --valid-time R4/20010102T0000Z/PT6H \
            --output obs.%Y%m%dT%H%MZ.ascii
"""

import argparse
import logging
import sys

from odb2 import valid_times_iterator
from odb2.bom import BOM_SYSTEMS, PrepBomNci
from prepODB2 import COLUMN_INFO


def main(argv: list[str]):
    """ODB2 to ASCII CLI."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=COLUMN_INFO,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--system",
        help="Bureau forecast system to load observations from (e.g. access_c4_dn)",
        required=True,
        metavar="SYSTEM",
        choices=BOM_SYSTEMS,
    )
    parser.add_argument(
        "--output", "-o", help="output path (default stdout)", default="-"
    )
    parser.add_argument(
        "--valid-time",
        "-t",
        help="valid times to load (ISO format, e.g. '20100512T1200', 'R4/20010101T0000Z/PT6H')",
        action="append",
        required=True,
    )
    parser.add_argument("--verbose", "-v", help="verbose", action="store_true")
    args = parser.parse_args(argv)

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    PrepBomNci(args.system).odb2ascii(
        args.output, valid_times_iterator(args.valid_time)
    )


if __name__ == "__main__":
    main(sys.argv[1:])
