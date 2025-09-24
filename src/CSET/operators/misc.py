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

import iris
import numpy as np
from iris.cube import Cube, CubeList

from CSET._common import iter_maybe
from CSET.operators._utils import fully_equalise_attributes, get_cube_yxcoordname
from CSET.operators.regrid import regrid_onto_cube


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
    return cubes


def addition(addend_1, addend_2):
    """Addition of two fields.

    Parameters
    ----------
    addend_1: Cube
        Any field to have another field added to it.
    addend_2: Cube
        Any field to be added to another field.

    Returns
    -------
    Cube

    Raises
    ------
    ValueError, iris.exceptions.NotYetImplementedError
        When the cubes are not compatible.

    Notes
    -----
    This is a simple operator designed for combination of diagnostics or
    creating new diagnostics by using recipes.

    Examples
    --------
    >>> field_addition = misc.addition(kinetic_energy_u, kinetic_energy_v)

    """
    return addend_1 + addend_2


def subtraction(minuend, subtrahend):
    """Subtraction of two fields.

    Parameters
    ----------
    minuend: Cube
        Any field to have another field subtracted from it.
    subtrahend: Cube
        Any field to be subtracted from to another field.

    Returns
    -------
    Cube

    Raises
    ------
    ValueError, iris.exceptions.NotYetImplementedError
        When the cubes are not compatible.

    Notes
    -----
    This is a simple operator designed for combination of diagnostics or
    creating new diagnostics by using recipes. It can be used for model
    differences to allow for comparisons between the same field in different
    models or model configurations.

    Examples
    --------
    >>> model_diff = misc.subtraction(temperature_model_A, temperature_model_B)

    """
    return minuend - subtrahend


def division(numerator, denominator):
    """Division of two fields.

    Parameters
    ----------
    numerator: Cube
        Any field to have the ratio taken with respect to another field.
    denominator: Cube
        Any field used to divide another field or provide the reference
        value in a ratio.

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
    creating new diagnostics by using recipes.

    Examples
    --------
    >>> bowen_ratio = misc.division(sensible_heat_flux, latent_heat_flux)

    """
    return numerator / denominator


def multiplication(multiplicand, multiplier):
    """Multiplication of two fields.

    Parameters
    ----------
    multiplicand: Cube
        Any field to be multiplied by another field.
    multiplier: Cube
        Any field to be multiplied to another field.

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
    creating new diagnostics by using recipes.

    Examples
    --------
    >>> filtered_CAPE_ratio = misc.multiplication(CAPE_ratio, inflow_layer_properties)

    """
    return multiplicand * multiplier


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
        logging.debug(
            "Linear regridding base cube to other grid to compute differences"
        )
        base = regrid_onto_cube(base, other, method="Linear")

    def is_increasing(sequence: list) -> bool:
        """Determine the direction of an ordered sequence.

        Returns "increasing" or "decreasing" depending on whether the sequence
        is going up or down. The sequence should already be monotonic, with no
        duplicate values. An iris DimCoord's points fulfills this criteria.
        """
        return sequence[0] < sequence[1]

    # Figure out if we are comparing between UM and LFRic; flip array if so.
    base_lat_direction = is_increasing(base.coord(base_lat_name).points)
    other_lat_direction = is_increasing(other.coord(other_lat_name).points)
    if base_lat_direction != other_lat_direction:
        other.data = np.flip(other.data, other.coord(other_lat_name).cube_dims(other))

    # Extract just common time points.
    base, other = _extract_common_time_points(base, other)

    # Equalise attributes so we can merge.
    fully_equalise_attributes([base, other])
    logging.debug("Base: %s\nOther: %s", base, other)

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

    difference.data = base.data - other.data
    return difference


def _extract_common_time_points(base: Cube, other: Cube) -> tuple[Cube, Cube]:
    """Extract common time points from cubes to allow comparison."""
    # Get the name of the first non-scalar time coordinate.
    time_coord = next(
        map(
            lambda coord: coord.name(),
            filter(
                lambda coord: coord.shape > (1,) and coord.name() in ["time", "hour"],
                base.coords(),
            ),
        ),
        None,
    )
    if not time_coord:
        logging.debug("No time coord, skipping equalisation.")
        return (base, other)
    base_time_coord = base.coord(time_coord)
    other_time_coord = other.coord(time_coord)
    logging.debug("Base: %s\nOther: %s", base_time_coord, other_time_coord)
    if time_coord == "hour":
        # We directly compare points when comparing coordinates with
        # non-absolute units, such as hour. We can't just check the units are
        # equal as iris automatically converts to datetime objects in the
        # comparison for certain coordinate names.
        base_times = base_time_coord.points
        other_times = other_time_coord.points
        shared_times = set.intersection(set(base_times), set(other_times))
    else:
        # Units don't match, so converting to datetimes for comparison.
        base_times = base_time_coord.units.num2date(base_time_coord.points)
        other_times = other_time_coord.units.num2date(other_time_coord.points)
        shared_times = set.intersection(set(base_times), set(other_times))
    logging.debug("Shared times: %s", shared_times)
    time_constraint = iris.Constraint(
        coord_values={time_coord: lambda cell: cell.point in shared_times}
    )
    # Extract points matching the shared times.
    base = base.extract(time_constraint)
    other = other.extract(time_constraint)
    if base is None or other is None:
        raise ValueError("No common time points found!")
    return (base, other)


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
