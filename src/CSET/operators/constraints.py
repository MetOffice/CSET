# Copyright 2022 Met Office and contributors.
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

"""
Operators to generate constraints to filter with.
"""

import iris
import iris.cube
from datetime import datetime


def generate_stash_constraint(stash: str, **kwargs) -> iris.AttributeConstraint:
    """
    Operator that takes a stash string, and uses iris to generate a constraint
    to be passed into the read operator to minimize the CubeList the read
    operator loads and speed up loading.

    Arguments
    ---------
    stash: str
        stash code to build iris constraint, currently using "m01s03i236"

    Returns
    -------
    stash_constraint: iris.AttributeConstraint
    """

    # At a later stage str list an option to combine constraints. Arguments
    # could be a list of stash codes that combined build the constraint.
    stash_constraint = iris.AttributeConstraint(STASH=stash)
    return stash_constraint


def generate_var_constraint(varname: str, **kwargs) -> iris.Constraint:
    """
    Operator that takes a CF compliant variable name string, and uses iris to
    generate a constraint to be passed into the read operator to minimize the
    CubeList the read operator loads and speed up loading.

    Arguments
    ---------
    varname: str
        CF compliant name of variable. Needed later for LFRic.

    Returns
    -------
    varname_constraint: iris.Constraint
    """

    varname_constraint = iris.Constraint(name=varname)
    return varname_constraint


def generate_cell_methods_constraint(cell_methods: list, **kwargs) -> iris.Constraint:
    """
    Operator that takes a list of cell methods and generates a constraint from
    that.

    Arguments
    ---------
    cell_methods: list
        cube.cell_methods for filtering

    Returns
    -------
    cell_method_constraint: iris.Constraint
    """

    def check_cell_methods(cube: iris.cube.Cube):
        if cube.cell_methods == tuple(cell_methods):
            return True
        else:
            return False

    cell_methods_constraint = iris.Constraint(cube_func=check_cell_methods)
    return cell_methods_constraint


def generate_time_constraint(
    time_start: str, time_end: str = None, **kwargs
) -> iris.AttributeConstraint:
    """
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
    if type(time_start) == str:
        time_start = datetime.fromisoformat(time_start)
    if time_end is None:
        time_end = time_start
    elif type(time_end) == str:
        time_end = datetime.fromisoformat(time_end)
    time_constraint = iris.Constraint(time=lambda t: time_start <= t.point <= time_end)
    return time_constraint


def combine_constraints(
    constraint: iris.Constraint = None, **kwargs
) -> iris.Constraint:
    """
    Operator that combines multiple constraints into one.

    Arguments
    ---------
    constraint: iris.Constraint
        First constraint to combine. This must be named "constraint".
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
    if type(constraint) == iris.Constraint:
        combined_constraint = constraint
    else:
        combined_constraint = iris.Constraint()

    for constr in kwargs.values():
        combined_constraint = combined_constraint & constr
    return combined_constraint
