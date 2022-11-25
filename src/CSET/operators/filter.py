"""
Operators to perform various kind of filtering.
"""
# This file probably wants renaming as it clashes with the builtin filter
# function.

import iris


def extract_field(cube: iris.cube.CubeList, field: str) -> iris.cube.CubeList:
    """
    Returns a cube containing only the specified field.

    Parameters
    ----------
    cube: Cube
        An iris cube of the data to average.

    field: str
        The variable to keep.

    Returns
    -------
    Cube
        A cube containing the averaged field.

    Raises
    ------
    IndexError
        If the cube does not contain `field`.

    Notes
    -----
    Not yet implemented.
    """
    pass
