"""
Operators for reading various types of files from disk.
"""

from pathlib import Path

import iris
import iris.cube


def read_cubes(loadpath: Path, stash: str = None) -> iris.cube.CubeList:

    """
    Read operator that takes a path string (can include wildcards), and uses
    iris to load all the cubes matching stash and return a CubeList object.

    Arguments
    ---------
    loadpath: Path or str
        Path to where .pp files are located
    stash: str, optional
        Stash code to filter

    Returns
    -------
    cubes: iris.cube.CubeList
        Cubes extracted
    """

    # TODO: validation that data exists

    if stash:
        # Create name constraint for stash
        stash_constraint = iris.NameConstraint(stash)
        return iris.load(loadpath, stash_constraint)
    else:
        return iris.load(loadpath)
