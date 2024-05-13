# Copyright 2022-2023 Met Office and contributors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Operators for reading various types of files from disk."""

import logging
import warnings
from pathlib import Path

import iris
import iris.coords
import iris.cube
import numpy as np

from CSET._common import iter_maybe


class NoDataWarning(UserWarning):
    """Warning that no data has been loaded."""


def read_cube(
    loadpath: Path,
    constraint: iris.Constraint = None,
    filename_pattern: str = "*",
    **kwargs,
) -> iris.cube.Cube:
    """Read a single cube from files.

    Read operator that takes a path string (can include wildcards), and uses
    iris to load the cube matching the constraint.

    If the loaded data is split across multiple files, a filename_pattern can be
    specified to select the read files using Unix shell-style wildcards. In this
    case the loadpath should point to the directory containing the data.

    Ensemble data can also be loaded. If it has a realization coordinate
    already, it will be directly used. If not, it will have its member number
    guessed from the filename, based on one of several common patterns. For
    example the pattern *emXX*, where XX is the realization.

    Deterministic data will be loaded with a realization of 0, allowing it to be
    processed in the same way as ensemble data.

    Arguments
    ---------
    loadpath: pathlike
        Path to where .pp/.nc files are located
    constraint: iris.Constraint | iris.ConstraintCombination
        Constraints to filter data by
    filename_pattern: str, optional
        Unix shell-style pattern to match filenames to. Defaults to "*"

    Returns
    -------
    cubes: iris.cube.Cube
        Cube loaded

    Raises
    ------
    FileNotFoundError
        If the provided path does not exist
    ValueError
        If the constraint doesn't produce a single cube.
    """
    cubes = read_cubes(loadpath, constraint, filename_pattern)
    # Check filtered cubes is a CubeList containing one cube.
    if len(cubes) == 1:
        return cubes[0]
    else:
        raise ValueError(
            f"Constraint doesn't produce single cube. {constraint}\n{cubes}"
        )


def read_cubes(
    loadpath: Path,
    constraint: iris.Constraint = None,
    filename_pattern: str = "*",
    **kwargs,
) -> iris.cube.CubeList:
    """Read cubes from files.

    Read operator that takes a path string (can include wildcards), and uses
    iris to load_cube all the cubes matching the constraint and return a
    CubeList object.

    If the loaded data is split across multiple files, a filename_pattern can be
    specified to select the read files using Unix shell-style wildcards. In this
    case the loadpath should point to the directory containing the data.

    Ensemble data can also be loaded. If it has a realization coordinate
    already, it will be directly used. If not, it will have its member number
    guessed from the filename, based on one of several common patterns. For
    example the pattern *emXX*, where XX is the realization.

    Deterministic data will be loaded with a realization of 0, allowing it to be
    processed in the same way as ensemble data.

    Arguments
    ---------
    loadpath: pathlike
        Path to where .pp/.nc files are located
    constraint: iris.Constraint | iris.ConstraintCombination, optional
        Constraints to filter data by
    filename_pattern: str, optional
        Unix shell-style pattern to match filenames to. Defaults to "*"

    Returns
    -------
    cubes: iris.cube.CubeList
        Cubes loaded

    Raises
    ------
    FileNotFoundError
        If the provided path does not exist
    """
    if isinstance(loadpath, str):
        loadpath = Path(loadpath)

    if loadpath.is_dir():
        loadpath = sorted(loadpath.glob(filename_pattern))

    logging.info(
        "Loading files:\n%s", "\n".join(str(path) for path in iter_maybe(loadpath))
    )

    if constraint is not None:
        logging.debug("Constraint: %s", constraint)
        cubes = iris.load(loadpath, constraint)
    else:
        cubes = iris.load(loadpath)
    if _is_ensemble(cubes):
        logging.info("Ensemble data, reloading with correct handling.")
        if constraint:
            cubes = iris.load(loadpath, constraint, callback=_ensemble_callback)
        else:
            cubes = iris.load(loadpath, callback=_ensemble_callback)
        cubes.merge()
    else:
        # Give deterministic a realization of 0 so they can be handled in the
        # same way as ensembles.
        for cube in cubes:
            cube.add_aux_coord(
                iris.coords.AuxCoord(
                    np.int32(0), standard_name="realization", units="1"
                )
            )
    logging.debug("Loaded cubes: %s", cubes)
    if len(cubes) == 0:
        warnings.warn(
            "No cubes loaded, check your constraints!", NoDataWarning, stacklevel=2
        )
    return cubes


def _is_ensemble(cubelist: iris.cube.CubeList) -> bool:
    """Test if a cubelist is likely to be ensemble data.

    If cubes either have a realization dimension, or there are multiple files
    for the same time-step, we can assume it is ensemble data.
    """
    unique_cubes = set()
    for cube in cubelist:
        if cube.coords("realization"):
            return True
        # Compare XML representation of cube structure to see if there are
        # duplicates.
        cube_content = cube.xml()
        if cube_content in unique_cubes:
            logging.debug("Cube Contents: %s", unique_cubes)
            return True
        else:
            unique_cubes.add(cube_content)
    logging.debug("Cube Contents: %s", unique_cubes)
    return False


def _ensemble_callback(cube, field, filename: str):
    """Add a realization coordinate to a cube.

    Uses the filename to add an ensemble member ('realization') to each cube.
    Assumes data is formatted enuk_um_0XX/enukaa_pd0HH.pp where XX is the
    ensemble member.

    Args:
        cube - ensemble member cube

        filename - filename of ensemble member data
    """
    if not cube.coords("realization"):
        if "em" in filename:
            # Assuming format is *emXX*
            loc = filename.find("em") + 2
            member = np.int32(filename[loc : loc + 2])
        else:
            # Assuming raw fields files format is enuk_um_0XX/enukaa_pd0HH
            member = np.int32(filename[-15:-13])

        cube.add_aux_coord(iris.coords.AuxCoord(member, standard_name="realization"))
