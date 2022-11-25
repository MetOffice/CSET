"""
Operators for reading various types of files from disk.
"""

from pathlib import Path
from iris.cube import CubeList


def netCDF_to_cube(filename: Path) -> CubeList:
    """
    Read a netCDF file into an iris cube.

    Parameters
    ----------
    filename: Path or pathlike
        The path of the file to read.

    Returns
    -------
    Cube
        An iris cube of the data.

    Raises
    ------
    FileNotFoundError
        If the file cannot be found.

    ValueError
        If the file in not a valid netCDF file.

    Notes
    -----
    The netCDF file will be read following the CF conventions.
    """
    # To be written by James W.
    pass
