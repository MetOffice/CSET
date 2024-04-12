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

"""Miscellaneous operators."""

from typing import Union

from iris.cube import Cube, CubeList

from CSET._common import iter_maybe


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
    cubes: Union[Cube, CubeList], attribute: str, **kwargs
) -> CubeList:
    """Remove a cube attribute.

    If the attribute is not on the cube, the cube is passed through unchanged.

    Arguments
    ---------
    cubes: Cube | CubeList
        One or more cubes to remove the attribute from.
    attribute: str
        Name of attribute to remove.

    Returns
    -------
    cubes: CubeList
        CubeList of cube(s) with the attribute removed.
    """
    # Ensure cubes is a CubeList.
    if not isinstance(cubes, CubeList):
        cubes = CubeList(iter_maybe(cubes))
    for cube in cubes:
        cube.attributes.pop(attribute, None)
    return cubes
