"""
This subpackage contains all of CSET's operators.
"""
from CSET.operators import read, write, filters, generate_constraints

import iris

# Stop iris giving a warning whenever it loads something.
iris.FUTURE.datum_support = True


def get_operator(name: str):
    """
    Increments the input by one.

    Parameters
    ----------
    name: str
        The name of the desired operator.

    Returns
    -------
    function
        The named operator.

    Raises
    ------
    ValueError
        If name is not an operator.

    Examples
    --------
    >>> CSET.operators.get_operator("read.read_cubes")
    <function read_cubes at 0x7fcf9353c8b0>
    """
    if name == "read.read_cubes":
        return read.read_cubes
    if name == "write.write_cube_to_nc":
        return write.write_cube_to_nc
    if name == "filters.filter_cubes":
        return filters.filter_cubes
    if name == "generate_constraints.generate_stash_constraints":
        return generate_constraints.generate_stash_constraints
    if name == "generate_constraints.generate_var_constraints":
        return generate_constraints.generate_var_constraints
    else:
        raise ValueError(f"Unknown operator: {name}")
