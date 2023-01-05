"""
Extract Instant Air Temperature

This is a longer description. It should detail what the task takes in and
outputs.
"""
from CSET.operators import read, write, filters, generate_constraints


def input_file_path():
    import sys
    import pathlib

    """Magic function that gives the initial input file path."""
    return pathlib.Path(sys.argv[1])


write.write_cube_to_nc(
    filters.filter_cubes(
        read.read_cubes(
            input_file_path(),
            generate_constraints.generate_stash_constraints("m01s03i236"),
        ),
        generate_constraints.generate_stash_constraints("m01s03i236"),
        (),
    )
)
