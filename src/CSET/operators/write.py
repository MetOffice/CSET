"""
Operators for writing various types of files to disk.
"""

from pathlib import Path
from iris.cube import Cube


def cube_to_netCDF(filename: Path, cube: Cube, overwrite: bool = False) -> Path:
    """
    Writes a netCDF file from an iris cube.

    Parameters
    ----------
    filename: Path or pathlike
        The path of the file to write.

    cube: Cube
        An iris cube of the data to write.

    overwrite: bool, default False
        Whether to overwrite already existing files.

    Returns
    -------
    Path
        The path of the written file.

    Raises
    ------
    FileExistsError
        If the file already exists and `overwrite` is False

    ValueError
        If the cube does not map to a valid netCDF file.

    Notes
    -----
    The netCDF file will be read following the CF conventions.
    """
    pass
