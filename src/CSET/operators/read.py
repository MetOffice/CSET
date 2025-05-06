# © Crown copyright, Met Office (2022-2025) and CSET contributors.
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
import datetime
import functools
import glob
import itertools
import logging
import warnings
from pathlib import Path

import iris
import iris.coords
import iris.cube
import iris.exceptions
import iris.util
import numpy as np

from CSET._common import iter_maybe
from CSET.operators._stash_to_lfric import STASH_TO_LFRIC


class NoDataWarning(UserWarning):
    """Warning that no data has been loaded."""


def read_cube(
    file_paths: list[str] | str,
    constraint: iris.Constraint = None,
    **kwargs,
) -> iris.cube.Cube:
    """Read a single cube from files.

    Read operator that takes a path string (can include shell-style glob
    patterns), and loads the cube matching the constraint. If any paths point to
    directory, all the files contained within are loaded.

    Ensemble data can also be loaded. If it has a realization coordinate
    already, it will be directly used. If not, it will have its member number
    guessed from the filename, based on one of several common patterns. For
    example the pattern *emXX*, where XX is the realization.

    Deterministic data will be loaded with a realization of 0, allowing it to be
    processed in the same way as ensemble data.

    Arguments
    ---------
    file_paths: str | list[str]
        Path or paths to where .pp/.nc files are located
    constraint: iris.Constraint | iris.ConstraintCombination, optional
        Constraints to filter data by. Defaults to unconstrained.

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
    cubes = read_cubes(file_paths, constraint)
    # Check filtered cubes is a CubeList containing one cube.
    if len(cubes) == 1:
        return cubes[0]
    else:
        raise ValueError(
            f"Constraint doesn't produce single cube: {constraint}\n{cubes}"
        )


def read_cubes(
    file_paths: list[str] | str,
    constraint: iris.Constraint | None = None,
    model_names: str | list[str] | None = None,
    **kwargs,
) -> iris.cube.CubeList:
    """Read cubes from files.

    Read operator that takes a path string (can include shell-style glob
    patterns), and loads the cubes matching the constraint. If any paths point
    to directory, all the files contained within are loaded.

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
    file_paths: str | list[str]
        Path or paths to where .pp/.nc files are located. Can include globs.
    constraint: iris.Constraint | iris.ConstraintCombination, optional
        Constraints to filter data by. Defaults to unconstrained.
    model_names: str | list[str], optional
        Names of the models that correspond to respective paths in file_paths.

    Returns
    -------
    cubes: iris.cube.CubeList
        Cubes loaded after being merged and concatenated.

    Raises
    ------
    FileNotFoundError
        If the provided path does not exist
    """
    # Get iterable of paths. Each path corresponds to 1 model.
    paths = iter_maybe(file_paths)
    model_names = iter_maybe(model_names)

    # Check we have appropriate number of model names.
    if model_names != (None,) and len(model_names) != len(paths):
        raise ValueError(
            f"The number of model names ({len(model_names)}) should equal "
            f"the number of paths given ({len(paths)})."
        )

    # Load the data for each model into a CubeList per model.
    model_cubes = (
        _load_model(path, name, constraint)
        for path, name in itertools.zip_longest(paths, model_names, fillvalue=None)
    )

    # Split out first model's cubes and mark it as the base for comparisons.
    cubes = next(model_cubes)
    for cube in cubes:
        # Use 1 to indicate True, as booleans can't be saved in NetCDF attributes.
        cube.attributes["cset_comparison_base"] = 1

    # Load the rest of the models.
    cubes.extend(itertools.chain.from_iterable(model_cubes))

    # Unify time units so different case studies can merge.
    iris.util.unify_time_units(cubes)

    # Merge and concatenate cubes now metadata has been fixed.
    cubes = cubes.merge()
    cubes = cubes.concatenate()

    # Ensure dimension coordinates are bounded.
    for cube in cubes:
        for dim_coord in cube.coords(dim_coords=True):
            # Iris can't guess the bounds of a scalar coordinate.
            if not dim_coord.has_bounds() and dim_coord.shape[0] > 1:
                dim_coord.guess_bounds()

    logging.info("Loaded cubes: %s", cubes)
    if len(cubes) == 0:
        warnings.warn(
            "No cubes loaded, check your constraints!", NoDataWarning, stacklevel=2
        )
    return cubes


def _load_model(
    paths: str | list[str],
    model_name: str | None,
    constraint: iris.Constraint | None,
) -> iris.cube.CubeList:
    """Load a single model's data into a CubeList."""
    input_files = _check_input_files(paths)
    # If unset, a constraint of None lets everything be loaded.
    logging.debug("Constraint: %s", constraint)
    cubes = iris.load(
        input_files, constraint, callback=_create_callback(is_ensemble=False)
    )
    # Reload with ensemble handling if needed.
    if _is_ensemble(cubes):
        cubes = iris.load(
            input_files, constraint, callback=_create_callback(is_ensemble=True)
        )

    # Add model_name attribute to each cube to make it available at any further
    # step without needing to pass it as function parameter.
    if model_name is not None:
        for cube in cubes:
            cube.attributes["model_name"] = model_name
    return cubes


def _check_input_files(input_paths: str | list[str]) -> list[Path]:
    """Get an iterable of files to load, and check that they all exist.

    Arguments
    ---------
    input_paths: list[str]
        List of paths to input files or directories. The path may itself contain
        glob patterns, but unlike in shells it will match directly first.

    Returns
    -------
    list[Path]
        A list of files to load.

    Raises
    ------
    FileNotFoundError:
        If the provided arguments don't resolve to at least one existing file.
    """
    files = []
    for raw_filename in iter_maybe(input_paths):
        # Match glob-like files first, if they exist.
        raw_path = Path(raw_filename)
        if raw_path.is_file():
            files.append(raw_path)
        else:
            for input_path in glob.glob(raw_filename):
                # Convert string paths into Path objects.
                input_path = Path(input_path)
                # Get the list of files in the directory, or use it directly.
                if input_path.is_dir():
                    logging.debug("Checking directory '%s' for files")
                    files.extend(p for p in input_path.iterdir() if p.is_file())
                else:
                    files.append(input_path)

    files.sort()
    logging.info("Loading files:\n%s", "\n".join(str(path) for path in files))
    if len(files) == 0:
        raise FileNotFoundError(f"No files found for {input_paths}")
    return files


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
            return True
        else:
            unique_cubes.add(cube_content)
    logging.info("Deterministic data loaded.")
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
        _fix_spatial_coord_name_callback(cube)
        _fix_pressure_coord_callback(cube)
        _lfric_normalise_varname(cube)
        _fix_um_radtime_prehour(cube)
        _fix_um_radtime_posthour(cube)
        _fix_um_lightning(cube)
        _lfric_time_callback(cube)
        _lfric_forecast_period_standard_name_callback(cube)

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


@functools.lru_cache(None)
def _warn_once(msg):
    """Print a warning message, skipping recent duplicates."""
    logging.warning(msg)


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
            # Don't change cubes with unknown stash codes.
            _warn_once(
                f"Unknown STASH code: {stash}. Please check file stash_to_lfric.py to update."
            )


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
    cube.attributes.pop("name", None)

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
        if (
            not isinstance(time_coord, iris.coords.DimCoord)
            and len(cube.coord_dims(time_coord)) == 1
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


def _fix_spatial_coord_name_callback(cube: iris.cube.Cube):
    """Check latitude and longitude coordinates name.

    This is necessary as some models define their grid as 'grid_latitude' and 'grid_longitude'
    and this means that recipes will fail - particularly if the user is comparing multiple models
    where the spatial coordinate names differ.
    """
    import CSET.operators._utils as utils

    # Check if cube is spatial.
    if not utils.is_spatialdim(cube):
        # Don't modify non-spatial cubes.
        return cube

    # Get spatial coords and dimension index.
    y_name, x_name = utils.get_cube_yxcoordname(cube)
    ny = utils.get_cube_coordindex(cube, y_name)
    nx = utils.get_cube_coordindex(cube, x_name)

    if y_name in ["latitude"] and cube.coord(y_name).units in [
        "degrees",
        "degrees_north",
        "degrees_south",
    ]:
        if "grid_latitude" not in [
            coord.name() for coord in cube.coords(dim_coords=False)
        ]:
            cube.add_aux_coord(
                iris.coords.AuxCoord(
                    cube.coord(y_name).points, long_name="grid_latitude"
                ),
                ny,
            )
    if x_name in ["longitude"] and cube.coord(x_name).units in [
        "degrees",
        "degrees_west",
        "degrees_east",
    ]:
        if "grid_longitude" not in [
            coord.name() for coord in cube.coords(dim_coords=False)
        ]:
            cube.add_aux_coord(
                iris.coords.AuxCoord(
                    cube.coord(x_name).points, long_name="grid_longitude"
                ),
                nx,
            )


def _fix_pressure_coord_callback(cube: iris.cube.Cube):
    """Rename pressure coordinate to "pressure" if it exists and ensure hPa units.

    This problem was raised because the AIFS model data from ECMWF
    defines the pressure coordinate with the name "pressure_level" rather
    than compliant CF coordinate names.

    Additionally, set the units of pressure to be hPa to be consistent with the UM,
    and approach the coordinates in a unified way.
    """
    for coord in cube.dim_coords:
        if coord.name() in ["pressure_level", "pressure_levels"]:
            coord.rename("pressure")

        if coord.name() == "pressure":
            if str(cube.coord("pressure").units) != "hPa":
                cube.coord("pressure").convert_units("hPa")


def _fix_um_radtime_posthour(cube: iris.cube.Cube):
    """Fix radiation which is output 1 minute past every hour."""
    try:
        if cube.attributes["STASH"] in [
            "m01s01i208",
            "m01s02i205",
            "m01s02i201",
            "m01s01i207",
            "m01s02i207",
            "m01s01i235",
        ]:
            time_coord = cube.coord("time")

            # Convert time points to datetime objects
            time_unit = time_coord.units
            time_points = time_unit.num2date(time_coord.points)

            # Skip if times don't need fixing.
            if time_points[0].minute != 1:
                return

            # Subtract 1 minute from each time point
            new_time_points = time_points - datetime.timedelta(minutes=1)

            # Convert back to numeric values using the original time unit
            new_time_values = time_unit.date2num(new_time_points)

            # Replace the time coordinate with corrected values
            time_coord.points = new_time_values
    except KeyError:
        pass


def _fix_um_radtime_prehour(cube: iris.cube.Cube):
    """Fix radiation which is output 1 minute before every hour."""
    try:
        if cube.attributes["STASH"] == "m01s01i207":
            time_coord = cube.coord("time")

            # Convert time points to datetime objects
            time_unit = time_coord.units
            time_points = time_unit.num2date(time_coord.points)

            # Skip if times don't need fixing.
            if time_points[0].minute != 59:
                return

            # Add 1 minute from each time point
            new_time_points = time_points + datetime.timedelta(minutes=1)

            # Convert back to numeric values using the original time unit
            new_time_values = time_unit.date2num(new_time_points)

            # Replace the time coordinate with corrected values
            time_coord.points = new_time_values
    except KeyError:
        pass


def _fix_um_lightning(cube: iris.cube.Cube):
    """To fix the date points in lightning accumulation STASH.

    Lightning (m01s21i104) is being output as a time accumulation in UM,
    over each hour (TAcc1hr), not from the start of the forecast, to be compatible
    with LFRic. So this is a short term solution to remove cell methods (
    as variables are ignored with cell methods for surface plots currently),
    and also adjust the time so that the value is at the end of each hour.
    """
    if cube.attributes.get("STASH") == "m01s21i104":
        # Remove aggregation cell method.
        cube.cell_methods = ()

        time_coord = cube.coord("time")

        # Convert time points to datetime objects.
        time_unit = time_coord.units
        time_points = time_unit.num2date(time_coord.points)

        # Skip if times don't need fixing.
        if time_points[0].minute == 0:
            return

        # Add 30 minutes to each time point.
        new_time_points = time_points + datetime.timedelta(minutes=30)

        # Convert back to numeric values using the original time unit.
        new_time_values = time_unit.date2num(new_time_points)

        # Replace the time coordinate with corrected values.
        time_coord.points = new_time_values


def _lfric_normalise_varname(cube: iris.cube.Cube):
    """Fix LFRic varnames for consistency to allow merging.

    LFRic data seems to sometime have a coordinate name end in "_0", which
    causes the cubes to fail to merge. This has been noticed in
    model_level_number as well as forecast_period.
    """
    for coord in cube.coords():
        if coord.var_name and coord.var_name.endswith("_0"):
            coord.var_name = coord.var_name.removesuffix("_0")


def _lfric_time_callback(cube: iris.cube.Cube):
    """Fix time coordinate metadata if missing dimensions.

    Some model data does not contain forecast_reference_time or forecast_period as
    expected coordinates, and so we cannot aggregate over case studies without this
    metadata. This callback fixes these issues.

    Notes
    -----
    Some parts of the code have been adapted from Paul Earnshaw's scripts.
    """
    # Construct forecast_reference time if it doesn't exist.
    try:
        tcoord = cube.coord("time")
        if not cube.coords("forecast_reference_time"):
            try:
                init_time = datetime.datetime.fromisoformat(
                    tcoord.attributes["time_origin"]
                )
                frt_point = tcoord.units.date2num(init_time)
                frt_coord = iris.coords.AuxCoord(
                    frt_point,
                    units=tcoord.units,
                    standard_name="forecast_reference_time",
                    long_name="forecast_reference_time",
                )
                cube.add_aux_coord(frt_coord)
            except KeyError:
                logging.warning(
                    "Cannot find forecast_reference_time, but no `time_origin` attribute to construct it from."
                )

        # Remove time_origin to allow multiple case studies to merge.
        tcoord.attributes.pop("time_origin", None)

        # Construct forecast_period axis (forecast lead time) if it doesn't exist.
        if not cube.coords("forecast_period"):
            try:
                # Create array of forecast lead times.
                init_coord = cube.coord("forecast_reference_time")
                init_time_points_in_tcoord_units = tcoord.units.date2num(
                    init_coord.units.num2date(init_coord.points)
                )
                lead_times = tcoord.points - init_time_points_in_tcoord_units

                # Get unit for lead time from time coordinate's unit.
                if "seconds" in str(tcoord.units):
                    units = "seconds"
                elif "hours" in str(tcoord.units):
                    units = "hours"
                else:
                    raise ValueError(f"Unrecognised base time unit: {tcoord.units}")

                # Create lead time coordinate.
                lead_time_coord = iris.coords.AuxCoord(
                    lead_times,
                    standard_name="forecast_period",
                    long_name="forecast_period",
                    units=units,
                )

                # Associate lead time coordinate with time dimension.
                cube.add_aux_coord(lead_time_coord, cube.coord_dims("time"))
            except iris.exceptions.CoordinateNotFoundError:
                logging.warning(
                    "Cube does not have both time and forecast_reference_time coordinate, so cannot construct forecast_period"
                )
    except iris.exceptions.CoordinateNotFoundError:
        logging.warning("No time coordinate on cube.")


def _lfric_forecast_period_standard_name_callback(cube: iris.cube.Cube):
    """Add forecast_period standard name if missing."""
    try:
        coord = cube.coord("forecast_period")
        if not coord.standard_name:
            coord.standard_name = "forecast_period"
    except iris.exceptions.CoordinateNotFoundError:
        pass
