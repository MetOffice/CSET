"""
Operators for writing various types of files to disk.
"""

import iris


def write_cube_to_nc(cube: iris.cube, saver: str) -> str:

    """
    A write operator that sits after the read operator. This operator expects
    a iris.cube object that will then be passed to MET for further processing.

    Arguments
    ---------

    * **cube**  - an iris.cube
    * **saver** - a string containing the path to save the cubes too

    Returns
    -------
    * **saver** - filepath to saved .nc

    """

    # Append .nc to saver path
    if not saver.endswith('.nc'):
        saver = saver+'.nc'

    # Save the file as nc compliant (iris should handle this)
    iris.save(cube, saver)

    return saver

