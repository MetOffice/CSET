"""
Operators for reading various types of files from disk.
"""

from pathlib import Path

import iris
import iris.cube


def read_cubes(
    loadpath: Path, constraint: iris.Constraint = None
) -> iris.cube.CubeList:

    """
    Read operator that takes a path string (can include wildcards), and uses
    iris to load all the cubes matching stash and return a CubeList object.

    Arguments
    ---------
    loadpath: Path or str
        Path to where .pp/.nc files are located
    constraint: iris.Constraint or iris.ConstraintCombination, optional
        Constraints to filter by

    Returns
    -------
    cubes: iris.cube.CubeList
        Cubes extracted
    """

    if constraint:
        return iris.load(loadpath, constraint)
    else:
        return iris.load(loadpath)
