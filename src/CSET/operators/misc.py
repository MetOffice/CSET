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

"""Miscellaneous operators."""

import itertools
import logging
from collections.abc import Iterable
from functools import reduce

import iris
import iris.analysis.calculus
import numpy as np
from iris.cube import Cube, CubeList

from CSET._common import is_increasing, iter_maybe
from CSET.operators._utils import (
    ensure_common_time_points,
    fully_equalise_attributes,
    get_cube_yxcoordname,
    get_shared_times,
    get_time_coord,
)
from CSET.operators.regrid import regrid_onto_cube

logger = logging.getLogger(__name__)


def noop(x, **kwargs):
    """Return its input without doing anything to it.

    Useful for constructing diagnostic chains.

    Arguments
    ---------
    x: Any
        Input to return.

    Returns
    -------
    x: Any
        The input that was given.
    """
    return x


def remove_attribute(
    cubes: Cube | CubeList, attribute: str | Iterable, **kwargs
) -> CubeList:
    """Remove a cube attribute.

    If the attribute is not on the cube, the cube is passed through unchanged.

    Arguments
    ---------
    cubes: Cube | CubeList
        One or more cubes to remove the attribute from.
    attribute: str | Iterable
        Name of attribute (or Iterable of names) to remove.

    Returns
    -------
    cubes: CubeList
        CubeList of cube(s) with the attribute removed.
    """
    # Ensure cubes is a CubeList.
    if not isinstance(cubes, CubeList):
        cubes = CubeList(iter_maybe(cubes))

    for cube in cubes:
        for attr in iter_maybe(attribute):
            cube.attributes.pop(attr, None)

    # Combine things that can be merged due to remove removing the
    # attributes.
    cubes = cubes.merge()
    # combine items that can be merged after removing unwanted attributes
    cubes = cubes.concatenate()
    return cubes


def remove_scalar_coords(
    cubes: Cube | CubeList, coords: str | Iterable[str]
) -> CubeList:
    """Remove scalar coordinates from one or more cubes.

    Coordinates are only removed if they exist on the cube and are
    scalar coordinates (i.e. have no associated dimensions). Examples
    include ``realization`` and ``forecast_reference_time`` on model
    data cubes. Dimensional and non-scalar auxiliary coordinates are
    left unchanged.

    Arguments
    ---------
    cubes: Cube | CubeList
        One or more cubes from which scalar coordinates will be removed.
    coords: str | Iterable
        Name of a coordinate (or Iterable of coordinate names) to remove.

    Returns
    -------
    cubes: CubeList
        CubeList of cube(s) with the requested scalar coordinates
        removed where present.
    """
    if not isinstance(cubes, CubeList):
        cubes = CubeList(iter_maybe(cubes))

    if isinstance(coords, str):
        coords = [coords]

    for cube in cubes:
        for coord_name in iter_maybe(coords):
            if cube.coords(coord_name):
                coord = cube.coord(coord_name)
                # only remove if scalar
                if cube.coord_dims(coord) == ():
                    cube.remove_coord(coord)

    return cubes


def combine_cubes_into_cubelist(first: Cube | CubeList, **kwargs) -> CubeList:
    """Operator that combines multiple cubes or CubeLists into one.

    Arguments
    ---------
    first: Cube | CubeList
        First cube or CubeList to merge into CubeList.
    second: Cube | CubeList
        Second cube or CubeList to merge into CubeList. This must be a named
        argument.
    third: Cube | CubeList
        There can be any number of additional arguments, they just need unique
        names.
    ...

    Returns
    -------
    combined_cubelist: CubeList
        Combined CubeList containing all cubes/CubeLists.

    Raises
    ------
    TypeError:
        If the provided arguments are not either a Cube or CubeList.
    """
    # Create empty CubeList to store cubes/CubeList.
    all_cubes = CubeList()

    # Combine all CubeLists into a single flat iterable.
    for item in itertools.chain(iter_maybe(first), *map(iter_maybe, kwargs.values())):
        # Check each item is a Cube, erroring if not.
        if isinstance(item, Cube):
            # Add cube to CubeList.
            all_cubes.append(item)
        else:
            raise TypeError("Not a Cube or CubeList!", item)

    return all_cubes


def difference(cubes: CubeList):
    """Difference of two fields.

    Parameters
    ----------
    cubes: CubeList
        A list of exactly two cubes. One must have the cset_comparison_base
        attribute set to 1, and will be used as the base of the comparison.

    Returns
    -------
    Cube

    Raises
    ------
    ValueError
        When the cubes are not compatible.

    Notes
    -----
    This is a simple operator designed for combination of diagnostics or
    creating new diagnostics by using recipes. It can be used for model
    differences to allow for comparisons between the same field in different
    models or model configurations.

    Examples
    --------
    >>> model_diff = misc.difference(temperature_model_A, temperature_model_B)

    """
    if len(cubes) != 2:
        raise ValueError("cubes should contain exactly 2 cubes.")
    base: Cube = cubes.extract_cube(iris.AttributeConstraint(cset_comparison_base=1))
    other: Cube = cubes.extract_cube(
        iris.Constraint(
            cube_func=lambda cube: "cset_comparison_base" not in cube.attributes
        )
    )

    # If cubes contain a pressure coordinate, ensure it is increasing.
    for cube in cubes:
        try:
            if len(cube.coord("pressure").points) > 2 and not is_increasing(
                cube.coord("pressure").points
            ):
                cube.data = np.flip(cube.data, axis=cube.coord_dims("pressure")[0])

        except iris.exceptions.CoordinateNotFoundError:
            pass

    # Get spatial coord names.
    base_lat_name, base_lon_name = get_cube_yxcoordname(base)
    other_lat_name, other_lon_name = get_cube_yxcoordname(other)

    # Ensure cubes to compare are on common differencing grid.
    # This is triggered if either
    #      i) latitude and longitude shapes are not the same. Note grid points
    #         are not compared directly as these can differ through rounding
    #         errors.
    #     ii) or variables are known to often sit on different grid staggering
    #         in different models (e.g. cell center vs cell edge), as is the case
    #         for UM and LFRic comparisons.
    # In future greater choice of regridding method might be applied depending
    # on variable type. Linear regridding can in general be appropriate for smooth
    # variables. Care should be taken with interpretation of differences
    # given this dependency on regridding.
    if (
        base.coord(base_lat_name).shape != other.coord(other_lat_name).shape
        or base.coord(base_lon_name).shape != other.coord(other_lon_name).shape
    ) or (
        base.long_name
        in [
            "eastward_wind_at_10m",
            "northward_wind_at_10m",
            "northward_wind_at_cell_centres",
            "eastward_wind_at_cell_centres",
            "zonal_wind_at_pressure_levels",
            "meridional_wind_at_pressure_levels",
            "potential_vorticity_at_pressure_levels",
            "vapour_specific_humidity_at_pressure_levels_for_climate_averaging",
        ]
    ):
        logger.debug("Linear regridding base cube to other grid to compute differences")
        base = regrid_onto_cube(base, other, method="Linear")

    # Figure out if we are comparing between UM and LFRic; flip array if so.
    base_lat_direction = is_increasing(base.coord(base_lat_name).points)
    other_lat_direction = is_increasing(other.coord(other_lat_name).points)
    if base_lat_direction != other_lat_direction:
        other.data = np.flip(other.data, other.coord(other_lat_name).cube_dims(other))

    # Equalise attributes so we can merge.
    fully_equalise_attributes([base, other])
    logger.debug("Base: %s\nOther: %s", base, other)

    # This currently relies on the cubes having the same underlying data layout.
    difference = base.copy()

    # Differences don't have a standard name; long name gets a suffix. We are
    # assuming we can rely on cubes having a long name, so we don't check for
    # its presents.
    difference.standard_name = None
    difference.long_name = (
        base.long_name if base.long_name else base.name()
    ) + "_difference"
    if base.var_name:
        difference.var_name = base.var_name + "_difference"
    elif base.standard_name:
        difference.var_name = base.standard_name + "_difference"

    # will raise if not common times
    ensure_common_time_points(base, other)

    difference.data = other.data - base.data
    return difference


def extract_common_time_points(cubes: CubeList) -> CubeList:
    """Return cubes restricted to their common time points.

    If the first cube has more than one FRT point, every cube must have identical
    FRT points. The cubes are then trimmed to their shared
    forecast_period values, so lead times line up across cubes.
    Otherwise (no FRT coordinate, or a single FRT), the cubes are
    trimmed to their shared times.

    Parameters
    ----------
    cubes: CubeList
        Cubes to align in time. The first cube is used as the reference.

    Returns
    -------
    CubeList
        Cubes containing only the time points common to all inputs.

    Raises
    ------
    ValueError
        If the first cube has multiple FRT points and any other cube either
        lacks a forecast_reference_time coordinate or has different FRT
        values (compared element-wise, so order matters).
    """
    multi_frt = any(
        len(c.coord("forecast_reference_time").points) > 1
        for c in cubes
        if c.coords("forecast_reference_time")
    )

    if multi_frt:
        for cb in cubes[1:]:
            cb_frt_coord = cb.coords("forecast_reference_time")
            if not cb_frt_coord:
                raise ValueError(
                    "All cubes must have a forecast_reference_time coordinate."
                )
        cubes_common = extract_common_points(cubes, "forecast_period")

        return cubes_common
    else:
        return _extract_common_time_points_one_frt(cubes)


def _ensure_same_frt(cubes: CubeList) -> None:
    """Ensure that all cubes have the same forecast_reference_time(s)."""

    def _frt_points(cb: Cube):
        coords = cb.coords("forecast_reference_time")
        return coords[0].points if coords else None

    reference = _frt_points(cubes[0])
    if reference is None:
        return

    for cube in cubes[1:]:
        points = _frt_points(cube)
        if points is None:
            raise ValueError("Cube does not contain any forecast_reference_times.")
        elif len(points) != len(reference):
            raise ValueError(
                "Cubes do not have same number of forecast_reference_times"
            )
        elif not np.array_equal(reference, points):
            raise ValueError(
                "Cubes do not share the same forecast_reference_time values."
            )


def _extract_common_time_points_one_frt(cubes: CubeList) -> CubeList:

    # typehints
    obs: Cube | None
    models: CubeList
    obs, models = split_obs_and_models(cubes)
    if obs is not None:
        base = obs
        others = models[0:]
    else:
        base = models[0]
        others = models[1:]
    list_shared_times: list[set[int]] = []
    time_coord = get_time_coord(cubes)

    if not time_coord:
        logger.debug("No time coord, skipping equalisation.")
        return cubes

    for other in iter_maybe(others):
        list_shared_times.append(get_shared_times(base, other, time_coord))

    shared_times_all = reduce(lambda x, y: x.intersection(y), list_shared_times)

    logger.debug("Shared times: %s", shared_times_all)

    time_constraint = iris.Constraint(
        coord_values={
            time_coord: lambda cell, shared_times=shared_times_all: (
                cell.point in shared_times
            )
        }
    )

    # Extract points matching the shared times.
    cubes_common_time = CubeList()
    for cube in cubes:
        cubes_common_time.append(cube.extract(time_constraint))

    return cubes_common_time


from iris.cube import CubeList


def _extract_common_time_points_multiplecubes(
    cubes: iris.cube.CubeList,
) -> iris.cube.CubeList:
    """Equalise forecast periods across all cubes."""

    if len(cubes) < 2:
        return cubes

    # Check all cubes have identical forecast reference times.
    try:
        reference_frts = cubes[0].coord("forecast_reference_time").points

        for cube in cubes[1:]:
            cube_frts = cube.coord("forecast_reference_time").points

            if not np.array_equal(reference_frts, cube_frts):
                raise ValueError(
                    "Cubes do not share the same "
                    "forecast_reference_time values."
                )

    except iris.exceptions.CoordinateNotFoundError as err:
        raise ValueError(
            "All cubes must have a forecast_reference_time coordinate."
        ) from err

    # Keep only forecast periods shared by all cubes.
    return extract_common_points(cubes, "forecast_period")


def convert_units(cubes: iris.cube.Cube | iris.cube.CubeList, units: str):
    """Convert the units of a cube.

    Arguments
    ---------
    cubes: iris.cube.Cube | iris.cube.CubeList
        A Cube or CubeList of a field for its units to be converted.

    units: str
        The unit that the original field is to be converted to. It takes
        CF compliant units.

    Returns
    -------
    iris.cube.Cube | iris.cube.CubeList
        The field converted into the specified units.

    Examples
    --------
    >>> T_in_F = misc.convert_units(temperature_in_K, "Fahrenheit")

    """
    new_cubelist = iris.cube.CubeList([])
    for cube in iter_maybe(cubes):
        # Copy cube to keep original data.
        cube_a = cube.copy()
        # Convert cube units.
        cube_a.convert_units(units)
        new_cubelist.append(cube_a)
    if len(new_cubelist) == 1:
        return new_cubelist[0]
    else:
        return new_cubelist


def rename_cube(cubes: iris.cube.Cube | iris.cube.CubeList, name: str):
    """Rename a cube.

    Arguments
    ---------
    cubes: iris.cube.Cube | iris.cube.CubeList
        A Cube or CubeList of a field to be renamed.

    name: str
        The new name of the cube. It should be CF compliant.

    Returns
    -------
    iris.cube.Cube | iris.cube.CubeList
        The renamed field.

    Notes
    -----
    This operator is designed to be used when the output field name does not
    match expectations or needs to be different to defaults in standard_name, var_name or
    long_name. For example, if combining masks
    to create light rain you would like the field to be named "mask_for_light_rain"
    rather than "mask_for_microphysical_precip_gt_0.0_x_mask_for_microphysical_precip_lt_2.0".

    Examples
    --------
    >>> light_rain_mask = misc.rename_cube(light_rain_mask,"mask_for_light_rainfall"
    """
    new_cubelist = iris.cube.CubeList([])
    for cube in iter_maybe(cubes):
        cube.rename(name)
        new_cubelist.append(cube)
    if len(new_cubelist) == 1:
        return new_cubelist[0]
    else:
        return new_cubelist


def _slice_cube_on_levels(cube: iris.cube.Cube, coord_name: str, levels: list):
    """
    Extract levels from a cube for a given coordinate.

    Arguments
    ---------
    cube: iris.cube.Cube
        A Cube to be sliced.

    coord_name: str
        The coordinate name to be sliced

    levels: list
        A list containing points to be extracted from the cube.

    Returns
    -------
    iris.cube.Cube
        The sliced cube.
    """
    coord = cube.coord(coord_name)
    (dim_index,) = cube.coord_dims(coord)

    mask = np.isin(coord.points, levels)

    slicer = [slice(None)] * cube.ndim
    slicer[dim_index] = mask

    return cube[tuple(slicer)]


def extract_common_points(cubes: iris.cube.CubeList, coordinate: str):
    """
    Extract common points for a given coordinate between cubes in a CubeList.

    Parameters
    ----------
    cubes: iris.cube.CubeList
        CubeList containing cubes for which to extract common points.

    coordinate: str
        The coordinate name to be checked for common points.

    Returns
    -------
    iris.cube.CubeList
        CubeList containing the two cubes sliced to common points
        for the given coordinate.
    """

    # Check type of input
    if type(cubes) is not iris.cube.CubeList:
        raise TypeError(f"Not a CubeList, got type {type(cubes)}")

    # Extract coordinate
    try:
        points_list = []
        for cube in cubes:
            points_list.append(cube.coord(coordinate).points)
    except iris.exceptions.CoordinateNotFoundError as err:
        raise ValueError(f"Both cubes must have an {coordinate} coordinate") from err

    # Find common points
    common_points = reduce(np.intersect1d, points_list)

    # Check that common points is more than zero.
    if common_points.size == 0:
        raise ValueError("No common levels found")

    # Extract common points
    common_cubes = iris.cube.CubeList()
    for cube in cubes:
        common_cubes.append(_slice_cube_on_levels(cube, coordinate, common_points))
    return common_cubes


def split_obs_and_models(cubes: CubeList) -> tuple[Cube | None, CubeList]:
    """Return (obs_cube or None, CubeList of model cubes)."""
    obs = [cb for cb in cubes if "observed" in (cb.long_name or "")]

    if len(obs) > 1:
        raise ValueError(f"Expected at most one 'observed' cube, found {len(obs)}")
    if not obs:
        return None, CubeList(cubes)

    base = obs[0]
    return base, CubeList(cb for cb in cubes if cb is not base)
