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

"""Operators to generate constraints to filter with."""

import numbers
import re
from collections.abc import Iterable
from datetime import timedelta

import iris
import iris.coords
import iris.cube

import CSET.operators._utils as operator_utils
from CSET._common import iter_maybe


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


def generate_cell_methods_constraint(
    cell_methods: list,
    varname: str | None = None,
    coord: iris.coords.Coord | None = None,
    interval: str | None = None,
    comment: str | None = None,
    **kwargs,
) -> iris.Constraint:
    """Generate constraint from cell methods.

    Operator that takes a list of cell methods and generates a constraint from
    that. Use [] to specify non-aggregated data.

    Arguments
    ---------
    cell_methods: list
        cube.cell_methods for filtering.
    varname: str, optional
        CF compliant name of variable.
    coord: iris.coords.Coord, optional
        iris.coords.Coord to which the cell method is applied to.
    interval: str, optional
        interval over which the cell method is applied to (e.g. 1 hour).
    comment: str, optional
        any comments in Cube meta data associated with the cell method.

    Returns
    -------
    cell_method_constraint: iris.Constraint
    """
    if len(cell_methods) == 0:

        def check_no_aggregation(cube: iris.cube.Cube) -> bool:
            """Check that any cell methods are "point", meaning no aggregation."""
            return set(cm.method for cm in cube.cell_methods) <= {"point"}

        def check_cell_sum(cube: iris.cube.Cube) -> bool:
            """Check that any cell methods are "sum"."""
            return set(cm.method for cm in cube.cell_methods) == {"sum"}

        if varname:
            # Require number_of_lightning_flashes to be "sum" cell_method input.
            # Require surface_microphyisical_rainfall_amount and surface_microphysical_snowfall_amount to be "sum" cell_method inputs.
            if ("lightning" in varname) or (
                "surface_microphysical" in varname and "amount" in varname
            ):
                cell_methods_constraint = iris.Constraint(cube_func=check_cell_sum)
                return cell_methods_constraint

        # If no variable name set, assume require instantaneous cube.
        cell_methods_constraint = iris.Constraint(cube_func=check_no_aggregation)

    else:
        # If cell_method constraint set in recipe, check for required input.
        def check_cell_methods(cube: iris.cube.Cube) -> bool:
            return all(
                iris.coords.CellMethod(
                    method=cm, coords=coord, intervals=interval, comments=comment
                )
                in cube.cell_methods
                for cm in cell_methods
            )

        cell_methods_constraint = iris.Constraint(cube_func=check_cell_methods)

    return cell_methods_constraint


def generate_time_constraint(
    time_start: str, time_end: str = None, **kwargs
) -> iris.Constraint:
    """Generate constraint between times.

    Operator that takes one or two ISO 8601 date strings, and returns a
    constraint that selects values between those dates (inclusive).

    Arguments
    ---------
    time_start: str | datetime.datetime | cftime.datetime
        ISO date for lower bound

    time_end: str | datetime.datetime | cftime.datetime
        ISO date for upper bound. If omitted it defaults to the same as
        time_start

    Returns
    -------
    time_constraint: iris.Constraint
    """
    if isinstance(time_start, str):
        pdt_start, offset_start = operator_utils.pdt_fromisoformat(time_start)
    else:
        pdt_start, offset_start = time_start, timedelta(0)

    if time_end is None:
        pdt_end, offset_end = time_start, offset_start
    elif isinstance(time_end, str):
        pdt_end, offset_end = operator_utils.pdt_fromisoformat(time_end)
        print(pdt_end)
        print(offset_end)
    else:
        pdt_end, offset_end = time_end, timedelta(0)

    if offset_start is None:
        offset_start = timedelta(0)
    if offset_end is None:
        offset_end = timedelta(0)

    time_constraint = iris.Constraint(
        time=lambda t: (
            (pdt_start <= (t.point - offset_start))
            and ((t.point - offset_end) <= pdt_end)
        )
    )

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


def generate_remove_single_ensemble_member_constraint(
    ensemble_member: int = 0, **kwargs
) -> iris.Constraint:
    """
    Generate a constraint to remove a single ensemble member.

    Operator that returns a constraint to remove the given ensemble member. By
    default the ensemble member removed is the control member (assumed to have
    a realization of zero). However, any ensemble member can be removed, thus
    allowing a non-zero control member to be removed if the control is a
    different member.

    Arguments
    ---------
    ensemble_member: int
        Default is 0. The ensemble member realization to remove.

    Returns
    -------
        iris.Constraint

    Notes
    -----
    This operator is primarily used to remove the control member to allow
    ensemble metrics to be calculated without the control member. For
    example, the ensemble mean is not normally calculated including the
    control member. It is particularly useful to remove the control member
    when it is not an equally-likely member of the ensemble.
    """
    return iris.Constraint(realization=lambda m: m.point != ensemble_member)


def generate_realization_constraint(
    ensemble_members: int | list[int], **kwargs
) -> iris.Constraint:
    """
    Generate a constraint to subset ensemble members.

    Operator that is given a list of ensemble members and returns a constraint
    to select those ensemble members. This operator is particularly useful for
    subsetting ensembles.

    Arguments
    ---------
    ensemble_members: int | list[int]
        The ensemble members to be subsetted over.

    Returns
    -------
    iris.Constraint
    """
    # Ensure ensemble_members is iterable.
    ensemble_members = iter_maybe(ensemble_members)
    return iris.Constraint(realization=ensemble_members)


def generate_hour_constraint(
    hour_start: int,
    hour_end: int = None,
    **kwargs,
) -> iris.Constraint:
    """Generate an hour constraint between hour of day limits.

    Operator that takes a set of hour of day limits and returns a constraint that
    selects only hours within that time frame regardless of day.

    Alternatively, the result can be constrained to a single hour by just entering
    a starting hour.

    Should any sub-hourly data be given these will have the same hour coordinate
    (e.g., 12:00 and 12:05 both have an hour coordinate of 12) all
    times will be selected with this constraint.

    Arguments
    ---------
    hour_start: int
        The hour of day for the lower bound, within 0 to 23.
    hour_end: int | None
        The hour of day for the upper bound, within 0 to 23. Alternatively,
        set to None if only one hour required.

    Returns
    -------
    hour_constraint: iris.Constraint

    Raises
    ------
    ValueError
        If the provided arguments are outside of the range 0 to 23.
    """
    if hour_end is None:
        hour_end = hour_start

    if (hour_start < 0) or (hour_start > 23) or (hour_end < 0) or (hour_end > 23):
        raise ValueError("Hours must be between 0 and 23 inclusive.")

    hour_constraint = iris.Constraint(hour=lambda h: hour_start <= h.point <= hour_end)
    return hour_constraint


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
