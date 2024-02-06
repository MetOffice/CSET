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

import iris.cube
import pytest

from CSET.operators import constraints, filters

constraint_single = constraints.combine_constraints(
    constraints.generate_stash_constraint("m01s03i236"),
    a=constraints.generate_cell_methods_constraint([]),
)


def test_filter_cubes_cubelist(cubes):
    """Test filtering a CubeList."""
    constraint = constraints.generate_cell_methods_constraint([])
    cube = filters.filter_cubes(cubes, constraint)
    assert cube.cell_methods == ()
    expected_cube = "<iris 'Cube' of air_temperature / (K) (time: 3; grid_latitude: 17; grid_longitude: 13)>"
    assert repr(cube) == expected_cube


def test_filter_cubes_cube(cube):
    """Test filtering a Cube."""
    constraint = constraints.generate_cell_methods_constraint([])
    single_cube = filters.filter_cubes(cube, constraint)
    assert repr(cube) == repr(single_cube)


def test_filter_cubes_multiple_returned_exception(cubes):
    """Test for exception when multiple cubes returned."""
    constraint = constraints.generate_stash_constraint("m01s03i236")
    with pytest.raises(ValueError):
        filters.filter_cubes(cubes, constraint)


def test_filter_cubes_pressure_coord(cube):
    """Test a cube without a pressure coordinate is passed through."""
    pressure_constraint = constraints.generate_pressure_level_constraint(
        pressure_levels=[]
    )
    assert filters.filter_cubes(cube, pressure_constraint)


def test_filter_cubes_pressure_coord_none_returned(cube):
    """Test exception when pressure coordinate is excluded."""
    pressure_constraint = constraints.generate_pressure_level_constraint(
        pressure_levels=[]
    )
    cube = cube.copy()
    cube.add_aux_coord(iris.coords.DimCoord(100, var_name="pressure"))
    with pytest.raises(ValueError):
        filters.filter_cubes(cube, pressure_constraint)


def test_filter_multiple_cubes(cubes):
    """Test to a CubeList of a single Cube."""
    filtered_cubes = filters.filter_multiple_cubes(cubes, c=constraint_single)
    assert isinstance(filtered_cubes, iris.cube.CubeList)
    assert len(filtered_cubes) == 1
    assert filtered_cubes[0].cell_methods == ()


def test_filter_multiple_cubes_single_cube(cube):
    """Test filtering a Cube."""
    filtered_cube = filters.filter_multiple_cubes(cube, c=constraint_single)
    assert isinstance(filtered_cube, iris.cube.CubeList)
    assert len(filtered_cube) == 1


def test_filter_multiple_cubes_multiple_out(cubes):
    """Test filtering for multiple Cubes."""
    constraint_single_2 = constraints.combine_constraints(
        constraints.generate_stash_constraint("m01s03i236"),
        a=constraints.generate_cell_methods_constraint(
            [
                iris.coords.CellMethod(
                    method="minimum", coords="time", intervals="1 hour"
                )
            ]
        ),
    )
    filtered_multi_cubes = filters.filter_multiple_cubes(
        cubes, c1=constraint_single, c2=constraint_single_2
    )
    assert len(filtered_multi_cubes) == 2


def test_filter_multiple_cubes_no_constraint_exception(cubes):
    """Test exception when no constraints given."""
    with pytest.raises(ValueError):
        filters.filter_multiple_cubes(cubes)


def test_filter_multiple_cubes_returned(cubes):
    """Test exception when multiple cubes returned."""
    constraint_multiple = constraints.generate_stash_constraint("m01s03i236")
    with pytest.raises(ValueError):
        filters.filter_multiple_cubes(cubes, c=constraint_multiple)


def test_filter_multiple_cubes_none_returned(cubes):
    """Test exception when no Cubes returned."""
    constraint_none = constraints.generate_stash_constraint("m01s01i001")
    with pytest.raises(ValueError):
        filters.filter_multiple_cubes(cubes, c=constraint_none)
