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
from pathlib import Path
from typing import Literal

import iris
import iris.coord_systems
import iris.coords
import iris.cube
import iris.exceptions
import iris.util
import numpy as np
from iris.analysis.cartography import rotate_pole, rotate_winds

from CSET._common import iter_maybe
from CSET.operators._stash_to_lfric import STASH_TO_LFRIC
from CSET.operators._utils import get_cube_yxcoordname


class NoDataError(FileNotFoundError):
    """Error that no data has been loaded."""


def read_cube(
    file_paths: list[str] | str,
    constraint: iris.Constraint = None,
    model_names: list[str] | str | None = None,
    subarea_type: str = None,
    subarea_extent: list[float] = None,
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
    model_names: str | list[str], optional
        Names of the models that correspond to respective paths in file_paths.
    subarea_type: "gridcells" | "modelrelative" | "realworld", optional
        Whether to constrain data by model relative coordinates or real world
        coordinates.
    subarea_extent: list, optional
        List of coordinates to constraint data by, in order lower latitude,
        upper latitude, lower longitude, upper longitude.

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
    cubes = read_cubes(
        file_paths=file_paths,
        constraint=constraint,
        model_names=model_names,
        subarea_type=subarea_type,
        subarea_extent=subarea_extent,
    )
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
    subarea_type: str = None,
    subarea_extent: list = None,
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
    subarea_type: str, optional
        Whether to constrain data by model relative coordinates or real world
        coordinates.
    subarea_extent: list[float], optional
        List of coordinates to constraint data by, in order lower latitude,
        upper latitude, lower longitude, upper longitude.

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

    # Select sub region.
    cubes = _cutout_cubes(cubes, subarea_type, subarea_extent)
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
        raise NoDataError("No cubes loaded, check your constraints!")
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
    # Make the UM's winds consistent with LFRic.
    _fix_um_winds(cubes)

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
                    logging.debug("Checking directory '%s' for files", input_path)
                    files.extend(p for p in input_path.iterdir() if p.is_file())
                else:
                    files.append(input_path)

    files.sort()
    logging.info("Loading files:\n%s", "\n".join(str(path) for path in files))
    if len(files) == 0:
        raise FileNotFoundError(f"No files found for {input_paths}")
    return files


def _cutout_cubes(
    cubes: iris.cube.CubeList,
    subarea_type: Literal["gridcells", "realworld", "modelrelative"] | None,
    subarea_extent: list[float, float, float, float],
):
    """Cut out a subarea from a CubeList."""
    if subarea_type is None:
        logging.debug("Subarea selection is disabled.")
        return cubes

    # If selected, cutout according to number of grid cells to trim from each edge.
    cutout_cubes = iris.cube.CubeList()
    # Find spatial coordinates
    for cube in cubes:
        # Find dimension coordinates.
        lat_name, lon_name = get_cube_yxcoordname(cube)

        # Compute cutout based on number of cells to trim from edges.
        if subarea_type == "gridcells":
            logging.debug(
                "User requested LowerTrim: %s LeftTrim: %s UpperTrim: %s RightTrim: %s",
                subarea_extent[0],
                subarea_extent[1],
                subarea_extent[2],
                subarea_extent[3],
            )
            lat_points = np.sort(cube.coord(lat_name).points)
            lon_points = np.sort(cube.coord(lon_name).points)
            # Define cutout region using user provided cell points.
            lats = [lat_points[subarea_extent[0]], lat_points[-subarea_extent[2] - 1]]
            lons = [lon_points[subarea_extent[1]], lon_points[-subarea_extent[3] - 1]]

        # Compute cutout based on specified coordinate values.
        elif subarea_type == "realworld" or subarea_type == "modelrelative":
            # If not gridcells, cutout by requested geographic area,
            logging.debug(
                "User requested LLat: %s ULat: %s LLon: %s ULon: %s",
                subarea_extent[0],
                subarea_extent[1],
                subarea_extent[2],
                subarea_extent[3],
            )
            # Define cutout region using user provided coordinates.
            lats = np.array(subarea_extent[0:2])
            lons = np.array(subarea_extent[2:4])
            # Ensure cutout longitudes are within +/- 180.0 bounds.
            while lons[0] < -180.0:
                lons += 360.0
            while lons[1] > 180.0:
                lons -= 360.0
            # If the coordinate system is rotated we convert coordinates into
            # model-relative coordinates to extract the appropriate cutout.
            coord_system = cube.coord(lat_name).coord_system
            if subarea_type == "realworld" and isinstance(
                coord_system, iris.coord_systems.RotatedGeogCS
            ):
                lons, lats = rotate_pole(
                    lons,
                    lats,
                    pole_lon=coord_system.grid_north_pole_longitude,
                    pole_lat=coord_system.grid_north_pole_latitude,
                )
        else:
            raise ValueError("Unknown subarea_type:", subarea_type)

        # Do cutout and add to cutout_cubes.
        intersection_args = {lat_name: lats, lon_name: lons}
        logging.debug("Cutting out coords: %s", intersection_args)
        try:
            cutout_cubes.append(cube.intersection(**intersection_args))
        except IndexError as err:
            raise ValueError(
                "Region cutout error. Check and update SUBAREA_EXTENT."
                "Cutout region requested should be contained within data area. "
                "Also check if cutout region requested is smaller than input grid spacing."
            ) from err

    return cutout_cubes


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
        _normalise_var0_varname(cube)
        _fix_spatial_coords_callback(cube)
        _fix_pressure_coord_callback(cube)
        _fix_um_radtime(cube)
        _fix_cell_methods(cube)
        _convert_cube_units_callback(cube)
        _grid_longitude_fix_callback(cube)
        _fix_lfric_cloud_base_altitude(cube)
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


def _grid_longitude_fix_callback(cube: iris.cube.Cube):
    """Check grid_longitude coordinates are in the range -180 deg to 180 deg.

    This is necessary if comparing two models with different conventions --
    for example, models where the prime meridian is defined as 0 deg or
    360 deg. If not in the range -180 deg to 180 deg, we wrap the grid_longitude
    so that it falls in this range. Checks are for near-180 bounds given
    model data bounds may not extend exactly to 0. or 360.
    Input cubes on non-rotated grid coordinates are not impacted.
    """
    import CSET.operators._utils as utils

    try:
        y, x = utils.get_cube_yxcoordname(cube)
    except ValueError:
        # Don't modify non-spatial cubes.
        return cube

    # Wrap longitudes if rotated pole coordinates
    coord_system = cube.coord(x).coord_system
    if x == "grid_longitude" and isinstance(
        coord_system, iris.coord_systems.RotatedGeogCS
    ):
        long_coord = cube.coord(x)
        long_points = long_coord.points.copy()
        long_centre = np.median(long_points)
        while long_centre < -175.0:
            long_centre += 360.0
            long_points += 360.0
        while long_centre >= 175.0:
            long_centre -= 360.0
            long_points -= 360.0
        long_coord.points = long_points

        # Update coord bounds to be consistent with wrapping.
        if long_coord.has_bounds() and np.size(long_coord) > 1:
            long_coord.bounds = None
            long_coord.guess_bounds()

    return cube


def _fix_spatial_coords_callback(cube: iris.cube.Cube):
    """Check latitude and longitude coordinates name.

    This is necessary as some models define their grid as on rotated
    'grid_latitude' and 'grid_longitude' coordinates while others define
    the grid on non-rotated 'latitude' and 'longitude'.
    Cube dimensions need to be made consistent to avoid recipe failures,
    particularly where comparing multiple input models with differing spatial
    coordinates.
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

    # Translate [grid_latitude, grid_longitude] to an unrotated 1-d DimCoord
    # [latitude, longitude] for instances where rotated_pole=90.0
    if "grid_latitude" in [coord.name() for coord in cube.coords(dim_coords=True)]:
        coord_system = cube.coord("grid_latitude").coord_system
        pole_lat = coord_system.grid_north_pole_latitude
        if pole_lat == 90.0:
            lats = cube.coord("grid_latitude").points
            lons = cube.coord("grid_longitude").points

            cube.remove_coord("grid_latitude")
            cube.add_dim_coord(
                iris.coords.DimCoord(
                    lats,
                    standard_name="latitude",
                    var_name="latitude",
                    units="degrees",
                    coord_system=iris.coord_systems.GeogCS(6371229.0),
                    circular=True,
                ),
                ny,
            )
            y_name = "latitude"
            cube.remove_coord("grid_longitude")
            cube.add_dim_coord(
                iris.coords.DimCoord(
                    lons,
                    standard_name="longitude",
                    var_name="longitude",
                    units="degrees",
                    coord_system=iris.coord_systems.GeogCS(6371229.0),
                    circular=True,
                ),
                nx,
            )
            x_name = "longitude"

    # Create additional AuxCoord [grid_latitude, grid_longitude] with
    # rotated pole attributes for cases with [lat, lon] inputs
    if y_name in ["latitude"] and cube.coord(y_name).units in [
        "degrees",
        "degrees_north",
        "degrees_south",
    ]:
        # Add grid_latitude AuxCoord
        if "grid_latitude" not in [
            coord.name() for coord in cube.coords(dim_coords=False)
        ]:
            cube.add_aux_coord(
                iris.coords.AuxCoord(
                    cube.coord(y_name).points,
                    var_name="grid_latitude",
                    units="degrees",
                ),
                ny,
            )
        # Ensure input latitude DimCoord has CoordSystem
        # This attribute is sometimes lost on iris.save
        if not cube.coord(y_name).coord_system:
            cube.coord(y_name).coord_system = iris.coord_systems.GeogCS(6371229.0)

    if x_name in ["longitude"] and cube.coord(x_name).units in [
        "degrees",
        "degrees_west",
        "degrees_east",
    ]:
        # Add grid_longitude AuxCoord
        if "grid_longitude" not in [
            coord.name() for coord in cube.coords(dim_coords=False)
        ]:
            cube.add_aux_coord(
                iris.coords.AuxCoord(
                    cube.coord(x_name).points,
                    var_name="grid_longitude",
                    units="degrees",
                ),
                nx,
            )

        # Ensure input longitude DimCoord has CoordSystem
        # This attribute is sometimes lost on iris.save
        if not cube.coord(x_name).coord_system:
            cube.coord(x_name).coord_system = iris.coord_systems.GeogCS(6371229.0)


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


def _fix_um_radtime(cube: iris.cube.Cube):
    """Move radiation diagnostics from timestamps which are output N minutes or seconds past every hour.

    This callback does not have any effect for output diagnostics with
    timestamps exactly 00 or 30 minutes past the hour. Only radiation
    diagnostics are checked.
    Note this callback does not interpolate the data in time, only adjust
    timestamps to sit on the hour to enable time-to-time difference plotting
    with models which may output radiation data on the hour.
    """
    try:
        if cube.attributes["STASH"] in [
            "m01s01i207",
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
            if time_points[0].minute == 0 and time_points[0].second == 0:
                return
            if time_points[0].minute == 30 and time_points[0].second == 0:
                return

            # Subtract time difference from the hour from each time point
            n_minute = time_points[0].minute
            n_second = time_points[0].second
            # If times closer to next hour, compute difference to add on to following hour
            if n_minute > 30:
                n_minute = n_minute - 60
            # Compute new diagnostic time stamp
            new_time_points = (
                time_points
                - datetime.timedelta(minutes=n_minute)
                - datetime.timedelta(seconds=n_second)
            )

            # Convert back to numeric values using the original time unit.
            new_time_values = time_unit.date2num(new_time_points)

            # Replace the time coordinate with updated values.
            time_coord.points = new_time_values

            # Recompute forecast_period with corrected values.
            if cube.coord("forecast_period"):
                fcst_prd_points = cube.coord("forecast_period").points
                new_fcst_points = (
                    time_unit.num2date(fcst_prd_points)
                    - datetime.timedelta(minutes=n_minute)
                    - datetime.timedelta(seconds=n_second)
                )
                cube.coord("forecast_period").points = time_unit.date2num(
                    new_fcst_points
                )
    except KeyError:
        pass


def _fix_cell_methods(cube: iris.cube.Cube):
    """To fix the assumed cell_methods in accumulation STASH from UM.

    Lightning (m01s21i104), rainfall amount (m01s04i201, m01s05i201) and snowfall amount
    (m01s04i202, m01s05i202) in UM is being output as a time accumulation,
    over each hour (TAcc1hr), but input cubes show cell_methods as "mean".
    For UM and LFRic inputs to be compatible, we assume accumulated cell_methods are
    "sum". This callback changes "mean" cube attribute cell_method to "sum",
    enabling the cell_method constraint on reading to select correct input.
    """
    # Shift "mean" cell_method to "sum" for selected UM inputs.
    if cube.attributes.get("STASH") in [
        "m01s21i104",
        "m01s04i201",
        "m01s04i202",
        "m01s05i201",
        "m01s05i202",
    ]:
        # Check if input cell_method contains "mean" time-processing.
        if set(cm.method for cm in cube.cell_methods) == {"mean"}:
            # Retrieve interval and any comment information.
            for cell_method in cube.cell_methods:
                interval_str = cell_method.intervals
                comment_str = cell_method.comments

            # Remove input aggregation method.
            cube.cell_methods = ()

            # Replace "mean" with "sum" cell_method to indicate aggregation.
            cube.add_cell_method(
                iris.coords.CellMethod(
                    method="sum",
                    coords="time",
                    intervals=interval_str,
                    comments=comment_str,
                )
            )


def _convert_cube_units_callback(cube: iris.cube.Cube):
    """Adjust diagnostic units for specific variables.

    Some precipitation diagnostics are output with unit kg m-2 s-1 and are
    converted here to mm hr-1.

    Visibility diagnostics are converted here from m to km to improve output
    formatting.
    """
    # Convert precipitation diagnostic units if required.
    varnames = filter(None, [cube.long_name, cube.standard_name, cube.var_name])
    if any("surface_microphysical" in name for name in varnames):
        if cube.units == "kg m-2 s-1":
            logging.debug(
                "Converting precipitation rate units from kg m-2 s-1 to mm hr-1"
            )
            # Convert from kg m-2 s-1 to mm s-1 assuming 1kg water = 1l water = 1dm^3 water.
            # This is a 1:1 conversion, so we just change the units.
            cube.units = "mm s-1"
            # Convert the units to per hour.
            cube.convert_units("mm hr-1")
        elif cube.units == "kg m-2":
            logging.debug("Converting precipitation amount units from kg m-2 to mm")
            # Convert from kg m-2 to mm assuming 1kg water = 1l water = 1dm^3 water.
            # This is a 1:1 conversion, so we just change the units.
            cube.units = "mm"

    # Convert visibility diagnostic units if required.
    varnames = filter(None, [cube.long_name, cube.standard_name, cube.var_name])
    if any("visibility" in name for name in varnames):
        if cube.units == "m":
            logging.debug("Converting visibility units m to km.")
            # Convert the units to km.
            cube.convert_units("km")

    return cube


def _fix_lfric_cloud_base_altitude(cube: iris.cube.Cube):
    """Mask cloud_base_altitude diagnostic in regions with no cloud."""
    varnames = filter(None, [cube.long_name, cube.standard_name, cube.var_name])
    if any("cloud_base_altitude" in name for name in varnames):
        # Mask cube where set > 144kft to catch default 144.35695538058164
        cube.data = np.ma.masked_array(cube.data)
        cube.data[cube.data > 144.0] = np.ma.masked


def _fix_um_winds(cubes: iris.cube.CubeList):
    """To make winds from the UM consistent with those from LFRic.

    Diagnostics of wind are not always consistent between the UM
    and LFric. Here, winds from the UM are adjusted to make them i
    consistent with LFRic.
    """
    # Check whether we have components of the wind identified by STASH,
    # (so this will apply only to cubes from the UM), but not the
    # wind speed and calculate it if it is missing. Note that
    # this will be biased low in general because the components will mostly
    # be time averages. For simplicity, we do this only if there is just one
    # cube of a component. A more complicated approach would be to consider
    # the cell methods, but it may not be warranted.
    u_constr = iris.AttributeConstraint(STASH="m01s03i225")
    v_constr = iris.AttributeConstraint(STASH="m01s03i226")
    speed_constr = iris.AttributeConstraint(STASH="m01s03i227")
    try:
        if cubes.extract(u_constr) and cubes.extract(v_constr):
            if len(cubes.extract(u_constr)) == 1 and not cubes.extract(speed_constr):
                _add_wind_speed_um(cubes)
            # Convert winds in the UM to be relative to true east and true north.
            _convert_wind_true_dirn_um(cubes)
    except (KeyError, AttributeError):
        pass


def _add_wind_speed_um(cubes: iris.cube.CubeList):
    """Add windspeeds to cubes from the UM."""
    wspd10 = (
        cubes.extract_cube(iris.AttributeConstraint(STASH="m01s03i225"))[0] ** 2
        + cubes.extract_cube(iris.AttributeConstraint(STASH="m01s03i226"))[0] ** 2
    ) ** 0.5
    wspd10.attributes["STASH"] = "m01s03i227"
    wspd10.standard_name = "wind_speed"
    wspd10.long_name = "wind_speed_at_10m"
    cubes.append(wspd10)


def _convert_wind_true_dirn_um(cubes: iris.cube.CubeList):
    """To convert winds to true directions.

    Convert from the components relative to the grid to true directions.
    This functionality only handles the simplest case.
    """
    u_grid = cubes.extract_cube(iris.AttributeConstraint(STASH="m01s03i225"))
    v_grid = cubes.extract_cube(iris.AttributeConstraint(STASH="m01s03i226"))
    true_u, true_v = rotate_winds(u_grid, v_grid, iris.coord_systems.GeogCS(6371229.0))
    u_grid.data = true_u.data
    v_grid.data = true_v.data


def _normalise_var0_varname(cube: iris.cube.Cube):
    """Fix varnames for consistency to allow merging.

    Some model data netCDF sometimes have a coordinate name end in
    "_0" etc, where duplicate coordinates of same name are defined but
    with different attributes. This can be inconsistently managed in
    different model inputs and can cause cubes to fail to merge.
    """
    for coord in cube.coords():
        if coord.var_name and coord.var_name.endswith("_0"):
            coord.var_name = coord.var_name.removesuffix("_0")
        if coord.var_name and coord.var_name.endswith("_1"):
            coord.var_name = coord.var_name.removesuffix("_1")
        if coord.var_name and coord.var_name.endswith("_2"):
            coord.var_name = coord.var_name.removesuffix("_2")
        if coord.var_name and coord.var_name.endswith("_3"):
            coord.var_name = coord.var_name.removesuffix("_3")

    if cube.var_name and cube.var_name.endswith("_0"):
        cube.var_name = cube.var_name.removesuffix("_0")


def _lfric_time_callback(cube: iris.cube.Cube):
    """Fix time coordinate metadata if missing dimensions.

    Some model data does not contain forecast_reference_time or forecast_period as
    expected coordinates, and so we cannot aggregate over case studies without this
    metadata. This callback fixes these issues.

    This callback also ensures all time coordinates are referenced as hours since
    1970-01-01 00:00:00 for consistency across different model inputs.

    Notes
    -----
    Some parts of the code have been adapted from Paul Earnshaw's scripts.
    """
    # Construct forecast_reference time if it doesn't exist.
    try:
        tcoord = cube.coord("time")
        # Set time coordinate to common basis "hours since 1970"
        try:
            tcoord.convert_units("hours since 1970-01-01 00:00:00")
        except ValueError:
            logging.error("Unrecognised base time unit: {tcoord.units}")

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
                # Convert all lead time to hours for consistency between models.
                if "seconds" in str(tcoord.units):
                    lead_times = lead_times / 3600.0
                    units = "hours"
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
