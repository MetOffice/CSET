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
Operators to generate load constraints and pass into read operator.
"""

import logging

import iris
import iris.cube


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
        CF compliant name of variable. Needed later for LFRic. Currently using
        "test"

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


def combine_constraints(unused_positional_argument, **kwargs) -> iris.Constraint:
    """
    Operator that combines multiple constraints into one.

    Arguments
    ---------
    constraint1: iris.Constraint
        First constraint to combine. The argument can have any name.
    constraint2: iris.Constraint
        Seconds constraint to combine. There can be any number of named
        arguments.
    ...

    Returns
    -------
    combined_constraint: iris.Constraint
    """

    combined_constraint = iris.Constraint()
    for constraint in kwargs.values():
        combined_constraint = combined_constraint & constraint
    return combined_constraint
