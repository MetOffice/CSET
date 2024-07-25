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

"""Operators to perform various kind of filtering."""

from typing import Union

import iris
import iris.cube
import iris.exceptions


def filter_cubes(
    cube: Union[iris.cube.Cube, iris.cube.CubeList],
    constraint: iris.Constraint,
    **kwargs,
) -> iris.cube.Cube:
    """Filter a CubeList down to a single Cube based on a constraint.

    Arguments
    ---------
    cube: iris.cube.Cube | iris.cube.CubeList
        Cube(s) to filter
    constraint: iris.Constraint
        Constraint to extract

    Returns
    -------
    iris.cube.Cube

    Raises
    ------
    ValueError
        If the constraint doesn't produce a single cube.
    """
    filtered_cubes = cube.extract(constraint)
    # Return directly if already a cube.
    if isinstance(filtered_cubes, iris.cube.Cube):
        return filtered_cubes
    # Check filtered cubes is a CubeList containing one cube.
    if isinstance(filtered_cubes, iris.cube.CubeList) and len(filtered_cubes) == 1:
        return filtered_cubes[0]
    else:
        raise ValueError(
            f"Constraint doesn't produce single cube. Constraint: {constraint}"
            f"\nSource: {cube}\nResult: {filtered_cubes}"
        )


def filter_multiple_cubes(
    cubes: Union[iris.cube.Cube, iris.cube.CubeList],
    **kwargs,
) -> iris.cube.CubeList:
    """Filter a CubeList on multiple constraints, returning another CubeList.

    Arguments
    ---------
    cube: iris.cube.Cube | iris.cube.CubeList
        Cube(s) to filter
    constraint: iris.Constraint
        Constraint to extract. This must be a named argument. There can be any
        number of additional constraints, they just need unique names.

    Returns
    -------
    iris.cube.CubeList

    Raises
    ------
    ValueError
        The constraints don't produce a single cube per constraint.
    """
    # Ensure input is a CubeList.
    if isinstance(cubes, iris.cube.Cube):
        cubes = iris.cube.CubeList((cubes,))
    if len(kwargs) < 1:
        raise ValueError("Must have at least one constraint.")
    try:
        filtered_cubes = cubes.extract_cubes(kwargs.values())
    except iris.exceptions.ConstraintMismatchError as err:
        raise ValueError(
            "The constraints don't produce a single cube per constraint."
        ) from err
    return filtered_cubes
