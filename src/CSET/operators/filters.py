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
    cubelist: iris.cube.CubeList, stash: str, cell_methods: list, **kwargs
) -> iris.cube:

    """
    Arguments
    ---------
    cubelist: iris.cube.CubeList
        Cubes to iterate over
    stash: str
        Stash code to extract
    cell_methods: list
        cube.cell_methods for filtering

    Returns
    -------
    cube: iris.cube.Cube
        Single variable
    """

    # Initialise empty cubelist to append filtered cubes to
    filtered_cubes = iris.cube.CubeList()

    # Initialise stash constraint
    stash_constraint = iris.AttributeConstraint(STASH=stash)

    # Iterate over all cubes and check stash/cell method
    # TODO - need to add additional filtering/checking i.e. time/accum, pressure level...
    for cube in cubelist.extract(stash_constraint):
        if cube.cell_methods == tuple(cell_methods):
            filtered_cubes.append(cube)

    # Check filtered cubes is a cubelist containing one cube.
    if len(filtered_cubes) == 1:
        return filtered_cubes[0]
    else:
        print("Still multiple cubes, additional filtering required...")
        print(filtered_cubes)
