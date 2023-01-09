"""
This subpackage contains all of CSET's operators.
"""
from CSET.operators import read, write, filters, generate_constraints

import iris

# Stop iris giving a warning whenever it loads something.
iris.FUTURE.datum_support = True


def get_operator(name: str):
    match name:
        case "read.read_cubes":
            return read.read_cubes
        case "write.write_cube_to_nc":
            return write.write_cube_to_nc
        case "filters.filter_cubes":
            return filters.filter_cubes
        case "generate_constraints.generate_stash_constraints":
            return generate_constraints.generate_stash_constraints
        case "generate_constraints.generate_var_constraints":
            return generate_constraints.generate_var_constraints
        case _:
            raise ValueError(f"Unknown operator: {name}")
