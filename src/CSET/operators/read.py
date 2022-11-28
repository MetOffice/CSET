"""
Operators for reading various types of files from disk.
"""

from pathlib import Path
from iris.cube import CubeList


def read_cubes(loadpath):

    """
    Read operator that takes a path string (can include wildcards), and uses
    iris to load all the cubes and return an iris.cube.CubeList object.

    Arguments
    ---------

    * **loadpath**  - an string containing a path to where .pp files are located.

    Returns
    -------
    * **cubes** - an iris.cube.CubeList 

    """

    #TODO: validation that data exists

    return iris.load(loadpath)
