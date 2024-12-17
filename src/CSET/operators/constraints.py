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

"""Operators to generate constraints to filter with."""

import numbers
import re
from collections.abc import Iterable
from datetime import datetime

import iris
import iris.cube
import iris.exceptions


def generate_stash_constraint(stash: str, **kwargs) -> iris.AttributeConstraint:
    """Generate constraint from STASH code.

    Operator that takes a stash string, and uses iris to generate a constraint
    to be passed into the read operator to minimize the CubeList the read
    operator loads and speed up loading.

    Arguments
    ---------
    stash: str
        stash code to build iris constraint, such as "m01s03i236"

    Returns
    -------
    stash_constraint: iris.AttributeConstraint
    """
    # At a later stage str list an option to combine constraints. Arguments
    # could be a list of stash codes that combined build the constraint.
    stash_constraint = iris.AttributeConstraint(STASH=stash)
    return stash_constraint


def generate_var_constraint(varname: str, **kwargs) -> iris.Constraint:
    """Generate constraint from variable name or STASH code.

    Operator that takes a CF compliant variable name string, and generates an
    iris constraint to be passed into the read or filter operator. Can also be
    passed a STASH code to generate a STASH constraint.

    Arguments
    ---------
    varname: str
        CF compliant name of variable, or a UM STASH code such as "m01s03i236".

    Returns
    -------
    varname_constraint: iris.Constraint
    """
    if re.match(r"m[0-9]{2}s[0-9]{2}i[0-9]{3}$", varname):
        varname_constraint = iris.AttributeConstraint(STASH=varname)
    else:
        varname_constraint = iris.Constraint(name=varname)
    return varname_constraint


def generate_level_constraint(
    coordinate: str, levels: int | list[int] | str, **kwargs
) -> iris.Constraint:
    """Generate constraint for particular levels on the specified coordinate.

    Operator that generates a constraint to constrain to specific model or
    pressure levels. If no levels are specified then any cube with the specified
    coordinate is rejected.

    Typically ``coordinate`` will be ``"pressure"`` or ``"model_level_number"``
    for UM, or ``"full_levels"`` or ``"half_levels"`` for LFRic.

    Arguments
    ---------
    coordinate: str
        Level coordinate name about which to constraint.
    levels: int | list[int] | str
        CF compliant level points, ``"*"`` for retrieving all levels, or
        ``[]`` for no levels.

    Returns
    -------
    constraint: iris.Constraint

    Notes
    -----
    Due to the specification of ``coordinate`` as an argument any iterable
    coordinate can be stratified with this function. Therefore,
    ``"realization"`` is a valid option. Subsequently, ``levels`` specifies the
    ensemble members, or group of ensemble members you wish to constrain your
    results over.
    """
    # If asterisks, then return all levels for given coordinate.
    if levels == "*":
        return iris.Constraint(**{coordinate: lambda cell: True})
    else:
        # Ensure is iterable.
        if not isinstance(levels, Iterable):
            levels = [levels]

        # When no levels specified reject cube with level coordinate.
        if len(levels) == 0:

            def no_levels(cube):
                # Reject cubes for which coordinate exists.
                return not cube.coords(coordinate)

            return iris.Constraint(cube_func=no_levels)

        # Filter the coordinate to the desired levels.
        # Dictionary unpacking is used to provide programmatic keyword arguments.
        return iris.Constraint(**{coordinate: levels})


def generate_cell_methods_constraint(cell_methods: list, **kwargs) -> iris.Constraint:
    """Generate constraint from cell methods.

    Operator that takes a list of cell methods and generates a constraint from
    that. Use [] to specify non-aggregated data.

    Arguments
    ---------
    cell_methods: list
        cube.cell_methods for filtering

    Returns
    -------
    cell_method_constraint: iris.Constraint
    """
    if len(cell_methods) == 0:

        def check_no_aggregation(cube: iris.cube.Cube) -> bool:
            """Check that any cell methods are "point", meaning no aggregation."""
            return set(cm.method for cm in cube.cell_methods) <= {"point"}

        cell_methods_constraint = iris.Constraint(cube_func=check_no_aggregation)
    else:

        def check_cell_methods(cube: iris.cube.Cube) -> bool:
            return cube.cell_methods == tuple(cell_methods)

        cell_methods_constraint = iris.Constraint(cube_func=check_cell_methods)
    return cell_methods_constraint


def generate_time_constraint(
    time_start: str, time_end: str = None, **kwargs
) -> iris.AttributeConstraint:
    """Generate constraint between times.

    Operator that takes one or two ISO 8601 date strings, and returns a
    constraint that selects values between those dates (inclusive).

    Arguments
    ---------
    time_start: str | datetime.datetime
        ISO date for lower bound

    time_end: str | datetime.datetime
        ISO date for upper bound. If omitted it defaults to the same as
        time_start

    Returns
    -------
    time_constraint: iris.Constraint
    """
    if isinstance(time_start, str):
        time_start = datetime.fromisoformat(time_start)
    if time_end is None:
        time_end = time_start
    elif isinstance(time_end, str):
        time_end = datetime.fromisoformat(time_end)
    time_constraint = iris.Constraint(time=lambda t: time_start <= t.point <= time_end)
    return time_constraint


def generate_area_constraint(
    lat_start: float | None,
    lat_end: float | None,
    lon_start: float | None,
    lon_end: float | None,
    **kwargs,
) -> iris.Constraint:
    """Generate an area constraint between latitude/longitude limits.

    Operator that takes a set of latitude and longitude limits and returns a
    constraint that selects grid values only inside that area. Works with the
    data's native grid so is defined within the rotated pole CRS.

    Alternatively, all arguments may be None to indicate the area should not be
    constrained. This is useful to allow making subsetting an optional step in a
    processing pipeline.

    Arguments
    ---------
    lat_start: float | None
        Latitude value for lower bound
    lat_end: float | None
        Latitude value for top bound
    lon_start: float | None
        Longitude value for left bound
    lon_end: float | None
        Longitude value for right bound

    Returns
    -------
    area_constraint: iris.Constraint
    """
    # Check all arguments are defined, or all are None.
    if not (
        all(
            (
                isinstance(lat_start, numbers.Real),
                isinstance(lat_end, numbers.Real),
                isinstance(lon_start, numbers.Real),
                isinstance(lon_end, numbers.Real),
            )
        )
        or all((lat_start is None, lat_end is None, lon_start is None, lon_end is None))
    ):
        raise TypeError("Bounds must real numbers, or all None.")

    # Don't constrain area if all arguments are None.
    if lat_start is None:  # Only need to check once, as they will be the same.
        # An empty constraint allows everything.
        return iris.Constraint()

    # Handle bounds crossing the date line.
    if lon_end < lon_start:
        lon_end = lon_end + 360

    def bound_lat(cell: iris.coords.Cell) -> bool:
        return lat_start < cell < lat_end

    def bound_lon(cell: iris.coords.Cell) -> bool:
        # Adjust cell values to handle crossing the date line.
        if cell < lon_start:
            cell = cell + 360
        return lon_start < cell < lon_end

    area_constraint = iris.Constraint(
        coord_values={"grid_latitude": bound_lat, "grid_longitude": bound_lon}
    )
    return area_constraint


def combine_constraints(
    constraint: iris.Constraint = None, **kwargs
) -> iris.Constraint:
    """
    Operator that combines multiple constraints into one.

    Arguments
    ---------
    constraint: iris.Constraint
        First constraint to combine.
    additional_constraint_1: iris.Constraint
        Second constraint to combine. This must be a named argument.
    additional_constraint_2: iris.Constraint
        There can be any number of additional constraint, they just need unique
        names.
    ...

    Returns
    -------
    combined_constraint: iris.Constraint

    Raises
    ------
    TypeError
        If the provided arguments are not constraints.
    """
    # If the first argument is not a constraint, it is ignored. This handles the
    # automatic passing of the previous step's output.
    if isinstance(constraint, iris.Constraint):
        combined_constraint = constraint
    else:
        combined_constraint = iris.Constraint()

    for constr in kwargs.values():
        combined_constraint = combined_constraint & constr
    return combined_constraint
