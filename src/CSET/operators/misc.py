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

"""Miscellaneous operators."""

import itertools
import logging
from collections.abc import Iterable

import iris
import iris.coords
import numpy as np
from iris.cube import Cube, CubeList

from CSET._common import iter_maybe
from CSET.operators._utils import (
    fully_equalise_attributes,
    get_cube_yxcoordname,
)
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

    # Check latitude, longitude shape the same. Not comparing points, as these
    # might slightly differ due to rounding errors (especially in future if we
    # are regridding cubes to common resolutions).
    # An exception has been included here to deal with some variables on different
    # grid staggering (cell center vs edge of cell) when comparing UM to LFRic,
    # depending on whether they are on a B grid or Arakawa staggering. Note we do not
    # generally apply regridding to any variable where dimension sizes do not
    # match, to make sure we are using appropriate regridding technique. In this
    # case for winds, a Linear regridding is appropriate (smooth variable).
    if (
        base.coord(base_lat_name).shape != other.coord(other_lat_name).shape
        or base.coord(base_lon_name).shape != other.coord(other_lon_name).shape
    ):
        if base.long_name in [
            "eastward_wind_at_10m",
            "northward_wind_at_10m",
            "northward_wind_at_cell_centres",
            "eastward_wind_at_cell_centres",
            "zonal_wind_at_pressure_levels",
            "meridional_wind_at_pressure_levels",
            "potential_vorticity_at_pressure_levels",
            "vapour_specific_humidity_at_pressure_levels_for_climate_averaging",
        ]:
            base = regrid_onto_cube(base, other, method="Linear")
        else:
            raise ValueError(
                f"Cubes should have the same shape, got {base.coord(base_lat_name)} {other.coord(other_lat_name)}"
            )

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
    if "time" in [coord.name() for coord in base.coords()]:
        logging.debug("Base: %s\nOther: %s", base.coord("time"), other.coord("time"))
        base_times = set(base.coord("time").units.num2date(base.coord("time").points))
        other_times = set(
            other.coord("time").units.num2date(other.coord("time").points)
        )
        shared_times = set.intersection(base_times, other_times)
        time_constraint = iris.Constraint(time=lambda cell: cell.point in shared_times)
        base = base.extract(time_constraint)
        other = other.extract(time_constraint)
        if base is None or other is None:
            raise ValueError("No common time points found!")
    else:
        logging.debug("No time coord, skipping equalisation.")

    # Equalise attributes so we can merge.
    fully_equalise_attributes([base, other])
    logging.debug("Base: %s\nOther: %s", base, other)

    # This currently relies on the cubes having the same underlying data layout.
    difference = base.copy()

    # Differences don't have a standard name; long name gets a suffix. We are
    # assuming we can rely on cubes having a long name, so we don't check for
    # its presents.
    difference.standard_name = None
    difference.long_name = base.long_name + "_difference"

    difference.data = base.data - other.data
    return difference
