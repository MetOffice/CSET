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
Operators to perform various kind of filtering.
"""

import iris
import iris.cube


def filter_cubes(
    cube: iris.cube.Cube, constraint: iris.Constraint, **kwargs
) -> iris.cube.Cube:
    """
    Filters a cubelist down to a single cube based on a constraint.

    Arguments
    ---------
    cube: iris.cube.Cube | iris.cube.CubeList
        Cube(s) to iterate over
    constraint: iris.Constraint
        Constraint to extract

    Returns
    -------
    filtered_cube: iris.cube.Cube
        Filtered cube

    Raises
    ------
    ValueError
        If the constraint doesn't produce a single cube.
    """

    filtered_cubes = cube.extract(constraint)

    # Check filtered cubes is a CubeList containing one cube.
    if len(filtered_cubes) == 1:
        return filtered_cubes[0]
    else:
        raise ValueError(
            f"Constraint doesn't produce single cube. {constraint}\n{filtered_cubes}"
        )
