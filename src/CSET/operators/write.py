"""
Operators for writing various types of files to disk.
"""

import iris


def write_cubelist_to_nc(cubelist, saver):

    """
    A write operator that sits after the read operator. This operator expects
    a iris.cube.CubeList object containing filtered cubes that will then be
    passed to MET for further processing.

    Arguments
    ---------

    * **cubelist**  - an iris.cube.CubeList object containing cube(s).
    * **saver** - a string containing the path to save the cubes too

    Returns
    -------
    * **saver+'.nc'** - filepath to saved .nc

    """

    # Save the file as nc compliant (iris should handle this). Append .nc to
    # ensure nc format.
    iris.save(cubelist, saver+'.nc')

    return saver+'.nc'

