"""
Operators for writing various types of files to disk.
"""

from pathlib import Path

import iris
import iris.cube


def write_cube_to_nc(cube: iris.cube.Cube, saver: Path) -> str:

    """
    A write operator that sits after the read operator. This operator expects
    an iris cube object that will then be passed to MET for further processing.

    Arguments
    ---------
    cube: iris.cube.Cube
        Single variable to save
    saver: Path
        Path to save the cubes too

    Returns
    -------
    saver: str
        Filepath to saved .nc
    """

    # Append .nc to saver path
    if not saver.endswith(".nc"):
        saver = saver + ".nc"

    # Save the file as nc compliant (iris should handle this)
    iris.save(cube, saver)

    return saver
