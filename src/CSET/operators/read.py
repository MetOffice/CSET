# © Crown copyright, Met Office (2022-2024) and CSET contributors.
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

import ast
import logging
import warnings
from collections.abc import Iterable
from pathlib import Path

import iris
import iris.coords
import iris.cube
import iris.util
import numpy as np

from CSET.operators._stash_to_lfric import STASH_TO_LFRIC


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
    constraint: iris.Constraint | iris.ConstraintCombination, optional
        Constraints to filter data by. Defaults to unconstrained.
    filename_pattern: str, optional
        Unix shell-style glob pattern to match filenames to. Defaults to "*"

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
    # TODO: Fix coordinate name to enable full level and half level merging.
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
    iris to load the minimal set of cubes matching the constraint.

    If the loaded data is split across multiple files, a filename_pattern can be
    specified to select the read files using Unix shell-style wildcards. In this
    case the loadpath should point to the directory containing the data.

    Ensemble data can also be loaded. If it has a realization coordinate
    already, it will be directly used. If not, it will have its member number
    guessed from the filename, based on one of several common patterns. For
    example the pattern *emXX*, where XX is the realization.

    Deterministic data will be loaded with a realization of 0, allowing it to be
    processed in the same way as ensemble data.

    Data output by XIOS (such as LFRic) has its per-file metadata removed so
    that the cubes merge across files.

    Arguments
    ---------
    loadpath: pathlike
        Path to where .pp/.nc files are located
    constraint: iris.Constraint | iris.ConstraintCombination, optional
        Constraints to filter data by. Defaults to unconstrained.
    filename_pattern: str, optional
        Unix shell-style glob pattern to match filenames to. Defaults to "*"

    Returns
    -------
    cubes: iris.cube.CubeList
        Cubes loaded after being merged and concatenated.

    Raises
    ------
    FileNotFoundError
        If the provided path does not exist
    """
    input_files = _check_input_files(loadpath, filename_pattern)
    # A constraint of None lets everything be loaded.
    logging.debug("Constraint: %s", constraint)
    # Load the data, then reload with correct handling if it is ensemble data.
    callback = _create_callback(is_ensemble=False)
    cubes = iris.load(input_files, constraint, callback=callback)
    if _is_ensemble(cubes):
        callback = _create_callback(is_ensemble=True)
        cubes = iris.load(input_files, constraint, callback=callback)

    # Merge and concatenate cubes now metadata has been fixed.
    cubes = cubes.merge()
    cubes = cubes.concatenate()

    # Ensure dimension coordinates are bounded.
    for cube in cubes:
        for dim_coord in cube.coords(dim_coords=True):
            # Iris can't guess the bounds of a scalar coordinate.
            if not dim_coord.has_bounds() and dim_coord.shape[0] > 1:
                dim_coord.guess_bounds()

    logging.debug("Loaded cubes: %s", cubes)
    if len(cubes) == 0:
        warnings.warn(
            "No cubes loaded, check your constraints!", NoDataWarning, stacklevel=2
        )
    return cubes


def _is_ensemble(cubelist: iris.cube.CubeList) -> bool:
    """Test if a CubeList is likely to be ensemble data.

    If cubes either have a realization dimension, or there are multiple files
    for the same time-step, we can assume it is ensemble data.
    """
    unique_cubes = set()
    for cube in cubelist:
        # Ignore realization of 0, as that is given to deterministic data.
        if cube.coords("realization") and any(cube.coord("realization").points != 0):
            return True
        # Compare XML representation of cube structure check for duplicates.
        cube_content = cube.xml()
        if cube_content in unique_cubes:
            logging.info("Ensemble data loaded.")
            logging.debug("Cube Contents: %s", unique_cubes)
            return True
        else:
            unique_cubes.add(cube_content)
    logging.info("Deterministic data loaded.")
    logging.debug("Cube Contents: %s", unique_cubes)
    return False


def _create_callback(is_ensemble: bool) -> callable:
    """Compose together the needed callbacks into a single function."""

    def callback(cube: iris.cube.Cube, field, filename: str):
        if is_ensemble:
            _ensemble_callback(cube, field, filename)
        else:
            _deterministic_callback(cube, field, filename)
        _um_normalise_callback(cube, field, filename)
        _lfric_normalise_callback(cube, field, filename)
        _lfric_time_coord_fix_callback(cube, field, filename)
        _longitude_fix_callback(cube, field, filename)

    return callback


def _ensemble_callback(cube, field, filename):
    """Add a realization coordinate to a cube.

    Uses the filename to add an ensemble member ('realization') to each cube.
    Assumes data is formatted enuk_um_0XX/enukaa_pd0HH.pp where XX is the
    ensemble member.

    Arguments
    ---------
    cube: Cube
        ensemble member cube
    field
        Raw data variable, unused.
    filename: str
        filename of ensemble member data
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


def _deterministic_callback(cube, field, filename):
    """Give deterministic cubes a realization of 0.

    This means they can be handled in the same way as ensembles through the rest
    of the code.
    """
    # Only add if realization coordinate does not exist.
    if not cube.coords("realization"):
        cube.add_aux_coord(
            iris.coords.AuxCoord(np.int32(0), standard_name="realization", units="1")
        )


def _um_normalise_callback(cube: iris.cube.Cube, field, filename):
    """Normalise UM STASH variable long names to LFRic variable names.

    Note standard names will remain associated with cubes where different.
    Long name will be used consistently in output filename and titles.
    """
    # Convert STASH to LFRic variable name
    if "STASH" in cube.attributes:
        stash = cube.attributes["STASH"]
        try:
            (name, grid) = STASH_TO_LFRIC[str(stash)]
            cube.long_name = name
        except KeyError:
            logging.warning("Unknown STASH code: %s", stash)
            logging.warning("Please check file stash_to_lfric.py to update.")
            # Don't change cubes with unknown stash codes.
            pass


def _lfric_normalise_callback(cube: iris.cube.Cube, field, filename):
    """Normalise attributes that prevents LFRic cube from merging.

    The uuid and timeStamp relate to the output file, as saved by XIOS, and has
    no relation to the data contained. These attributes are removed.

    The um_stash_source is a list of STASH codes for when an LFRic field maps to
    multiple UM fields, however it can be encoded in any order. This attribute
    is sorted to prevent this. This attribute is only present in LFRic data that
    has been converted to look like UM data.
    """
    # Remove unwanted attributes.
    cube.attributes.pop("timeStamp", None)
    cube.attributes.pop("uuid", None)
    # There might also be a "name" attribute to ditch, which is the filename.

    # Sort STASH code list.
    stash_list = cube.attributes.get("um_stash_source")
    if stash_list:
        # Parse the string as a list, sort, then re-encode as a string.
        cube.attributes["um_stash_source"] = str(sorted(ast.literal_eval(stash_list)))


def _lfric_time_coord_fix_callback(cube: iris.cube.Cube, field, filename):
    """Ensure the time coordinate is a DimCoord rather than an AuxCoord.

    The coordinate is converted and replaced if not. SLAMed LFRic data has this
    issue, though the coordinate satisfies all the properties for a DimCoord.
    Scalar time values are left as AuxCoords.
    """
    # This issue seems to come from iris's handling of NetCDF files where time
    # always ends up as an AuxCoord.
    if cube.coords("time"):
        time_coord = cube.coord("time")
        if not isinstance(time_coord, iris.coords.DimCoord) and cube.coord_dims(
            time_coord
        ):
            iris.util.promote_aux_coord_to_dim_coord(cube, time_coord)

    # Force single-valued coordinates to be scalar coordinates.
    return iris.util.squeeze(cube)


def _longitude_fix_callback(cube: iris.cube.Cube, field, filename):
    """Check longitude coordinates are in the range -180 deg to 180 deg.

    This is necessary if comparing two models with different conventions --
    for example, models where the prime meridian is defined as 0 deg or
    360 deg. If not in the range -180 deg to 180 deg, we wrap the longitude
    so that it falls in this range.
    """
    import CSET.operators._utils as utils

    try:
        y, x = utils.get_cube_yxcoordname(cube)
    except ValueError:
        # Don't modify non-spatial cubes.
        return cube
    long_coord = cube.coord(x)
    long_points = long_coord.points.copy()
    long_centre = np.median(long_points)
    while long_centre < -180.0:
        long_centre += 360.0
        long_points += 360.0
    while long_centre >= 180.0:
        long_centre -= 360.0
        long_points -= 360.0
    long_coord.points = long_points
    return cube


def _check_input_files(input_path: Path | str, filename_pattern: str) -> Iterable[Path]:
    """Get an iterable of files to load, and check that they all exist.

    Arguments
    ---------
    input_path: Path | str
        Path to an input file or directory. The path may itself contain glob
        patterns, but unlike in shells it will match directly first.

    filename_pattern: str
        Shell-style glob pattern to match inside the input directory.

    Returns
    -------
    Iterable[Path]
        A list of files to load.

    Raises
    ------
    FileNotFoundError:
        If the provided arguments don't resolve to at least one existing file.
    """
    logging.debug("Checking '%s' for pattern '%s'", input_path, filename_pattern)
    # Convert string paths into Path objects.
    if isinstance(input_path, str):
        input_path = Path(input_path)

    # Get the list of files in the directory, or use it directly. Error if no
    # files found.
    if input_path.is_dir():
        files = tuple(sorted(input_path.glob(filename_pattern)))
        if len(files) == 0:
            raise FileNotFoundError(
                f"No files found matching filename_pattern {filename_pattern} within {input_path}"
            )
    elif input_path.is_file():
        files = (input_path,)
    else:
        # Handle input_path containing a glob pattern.
        files = tuple(sorted(input_path.parent.glob(input_path.name)))
        if len(files) == 0:
            raise FileNotFoundError(f"{input_path} does not exist!")
    logging.info("Loading files:\n%s", "\n".join(str(path) for path in files))
    return files
