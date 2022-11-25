"""
Operators to perform various kind of filtering.
"""
# This file probably wants renaming as it clashes with the builtin filter
# function.

from iris.cube import CubeList


def extract_field(cube: CubeList, field: str) -> CubeList:
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
