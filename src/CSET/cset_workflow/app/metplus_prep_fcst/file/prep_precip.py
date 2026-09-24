#!/usr/bin/env python3

"""
Extract precipitation data from a model.

This is really a CSET recipe with a bit of logic for cell_methods.
It's possible that the input dataset doesn't set cell_methods (e.g. BRIS), so
we only look for that in the case of multiple VARNAME matches in the input
dataset.
"""

from CSET.operators import read, filters, constraints, write
from CSET._common import parse_variable_options
import os.path
import sys
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir")
    args, options = parser.parse_known_args()

    v = parse_variable_options(options)

    cubes: iris.CubeList = read.read_cubes(
        file_paths = v["INPUT_PATHS"],
        constraint = v["VARNAME"],
        subarea_type = v["SUBAREA_TYPE"],
        subarea_extent = v["SUBAREA_EXTENT"],
    )

    if len(cubes) > 1:
        # We matched more than one cube, add a method filter
        cubes = filters.filter_cubes(
                cubes,
                constraint = constraints.generate_cell_methods_constraint(
                    varname= v["VARNAME"],
                    cell_methods = ["sum"],
                    coord = "time",
                    interval = v["ACCUM"],
                    )
                )

    write.write_cube_to_nc(
        cubes,
        filename = os.path.join(args.output_dir,v["FILENAME"]),
        overwrite = True,
        )


if __name__ == '__main__':
    main()
