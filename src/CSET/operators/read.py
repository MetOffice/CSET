"""
Operators for reading various types of files from disk.
"""

import iris
from pathlib import Path


def read_cubes(loadpath: Path, stash: str) -> iris.cube.CubeList:

    """
    Read operator that takes a path string (can include wildcards), and uses
    iris to load all the cubes matching stash and return an
    iris.cube.CubeList object.

    Arguments
    ---------
    loadpath: Path or str
        Path to where .pp files are located

    stash: str
        Stash code to filter

    Returns
    -------
    cubes: iris.cube.CubeList
        Cubes extracted
    """

    # TODO: validation that data exists

    return iris.load(loadpath, stash)
