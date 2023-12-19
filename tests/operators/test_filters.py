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

"""Test filter operators."""

import pytest

from CSET.operators import constraints, filters


def test_filters_operator(cubes):
    """Filter cube and verify."""
    constraint = constraints.generate_cell_methods_constraint([])
    # Test filtering a CubeList.
    cube = filters.filter_cubes(cubes, constraint)
    assert cube.cell_methods == ()
    expected_cube = "<iris 'Cube' of air_temperature / (K) (time: 3; grid_latitude: 17; grid_longitude: 13)>"
    assert repr(cube) == expected_cube
    # Test for exception when multiple cubes returned.
    constraint = constraints.generate_stash_constraint("m01s03i236")
    with pytest.raises(ValueError):
        cube = filters.filter_cubes(cubes, constraint)
    # Test filtering a single Cube.
    single_cube = filters.filter_cubes(cube, constraint)
    assert repr(cube) == repr(single_cube)
