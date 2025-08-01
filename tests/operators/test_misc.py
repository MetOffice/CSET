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

"""Test miscellaneous operators."""

import datetime

import iris
import iris.coords
import iris.cube
import iris.exceptions
import numpy as np
import pytest

from CSET.operators import misc, read


def test_noop_operator():
    """Passes through input unchanged."""
    a = 7
    b = misc.noop(a)
    assert a == b


def test_remove_attribute_cube(cube):
    """Remove attribute from a Cube."""
    assert "STASH" in cube.attributes
    cube = misc.remove_attribute(cube, "STASH")[0]
    assert "STASH" not in cube.attributes


def test_remove_attribute_cubelist(cubes):
    """Remove attribute from a CubeList."""
    for cube in cubes:
        assert "STASH" in cube.attributes
    cubes = misc.remove_attribute(cubes, "STASH")
    for cube in cubes:
        assert "STASH" not in cube.attributes


def test_addition(cube):
    """Adds two objects together."""
    a = cube + cube
    b = misc.addition(cube, cube)
    assert np.allclose(b.data, a.data, atol=1e-5, equal_nan=True)


def test_addition_failure(cube):
    """Tests arrays of different units produces an error."""
    a = read.read_cube("tests/test_data/convection/ECFlagB.nc")
    with pytest.raises(iris.exceptions.NotYetImplementedError):
        misc.addition(cube, a)


def test_subtraction(cube):
    """Subtracts one object from another one."""
    a = cube - cube
    b = misc.subtraction(cube, cube)
    assert np.allclose(b.data, a.data, atol=1e-5, equal_nan=True)


def test_subtraction_failure(cube):
    """Tests arrays of different units produces an error."""
    a = read.read_cube("tests/test_data/convection/ECFlagB.nc")
    with pytest.raises(iris.exceptions.NotYetImplementedError):
        misc.subtraction(cube, a)


def test_division(cube):
    """Divides one object by another."""
    a = cube / cube
    b = misc.division(cube, cube)
    assert np.allclose(b.data, a.data, atol=1e-5, equal_nan=True)


def test_division_failure(cube):
    """Tests arrays of different shapes produces an error."""
    a = read.read_cube("tests/test_data/convection/ECFlagB.nc")
    with pytest.raises(ValueError):
        misc.division(cube, a)


def test_multiplication(cube):
    """Multiplies one object by another."""
    a = cube * cube
    b = misc.multiplication(cube, cube)
    assert np.allclose(b.data, a.data, atol=1e-5, equal_nan=True)


def test_multiplication_failure(cube):
    """Tests arrays of different shapes produces an error."""
    a = read.read_cube("tests/test_data/convection/ECFlagB.nc")
    with pytest.raises(ValueError):
        misc.multiplication(cube, a)


def test_combine_single_cube_into_cubelist(cube):
    """Test case of single cube into cubelist."""
    cubelist = misc.combine_cubes_into_cubelist(cube)
    expected_cubelist = "[<iris 'Cube' of air_temperature / (K) (time: 3; grid_latitude: 17; grid_longitude: 13)>]"
    assert repr(cubelist) in expected_cubelist


def test_combine_single_cubelist_into_cubelist(cube):
    """Test case of single cubelist into cubelist."""
    cubelist = misc.combine_cubes_into_cubelist(iris.cube.CubeList([cube, cube]))
    expected_cubelist = "[<iris 'Cube' of air_temperature / (K) (time: 3; grid_latitude: 17; grid_longitude: 13)>,\n<iris 'Cube' of air_temperature / (K) (time: 3; grid_latitude: 17; grid_longitude: 13)>]"
    assert repr(cubelist) in expected_cubelist


def test_combine_single_noncompliant_into_cubelist():
    """Test case of single object which isn't cube or cubelist."""
    with pytest.raises(TypeError):
        misc.combine_cubes_into_cubelist("hello")


def test_combine_multiple_cube_into_cubelist(cube):
    """Test case of multiple cube into cubelist."""
    cubelist = misc.combine_cubes_into_cubelist(cube, a=cube)
    expected_cubelist = "[<iris 'Cube' of air_temperature / (K) (time: 3; grid_latitude: 17; grid_longitude: 13)>,\n<iris 'Cube' of air_temperature / (K) (time: 3; grid_latitude: 17; grid_longitude: 13)>]"
    assert repr(cubelist) in expected_cubelist


def test_combine_multiple_cube_and_noncompliant_into_cubelist(cube):
    """Test case of a valid cube with some non compliant data which isn't cube or cubelist."""
    with pytest.raises(TypeError):
        misc.combine_cubes_into_cubelist(cube, a="hello")


def test_combine_multiple_cube_mixed_into_cubelist(cube):
    """Test case of multiple cubes and cubelist into cubelist."""
    cubelist = misc.combine_cubes_into_cubelist(cube, a=cube)
    out_cubelist = misc.combine_cubes_into_cubelist(cube, a=cubelist, b=cube)
    expected_cubelist = "[<iris 'Cube' of air_temperature / (K) (time: 3; grid_latitude: 17; grid_longitude: 13)>,\n<iris 'Cube' of air_temperature / (K) (time: 3; grid_latitude: 17; grid_longitude: 13)>,\n<iris 'Cube' of air_temperature / (K) (time: 3; grid_latitude: 17; grid_longitude: 13)>,\n<iris 'Cube' of air_temperature / (K) (time: 3; grid_latitude: 17; grid_longitude: 13)>]"
    assert repr(out_cubelist) in expected_cubelist


def test_difference(cube: iris.cube.Cube):
    """Test taking the difference between two cubes."""
    # Data preparation.
    other_cube = cube.copy()
    del other_cube.attributes["cset_comparison_base"]
    cubes = iris.cube.CubeList([cube, other_cube])

    # Take difference.
    difference_cube = misc.difference(cubes)

    # As both cubes use the same data, check the difference is zero.
    assert isinstance(difference_cube, iris.cube.Cube)
    assert np.allclose(
        difference_cube.data, np.zeros_like(difference_cube.data), atol=1e-9
    )
    assert difference_cube.standard_name is None
    assert difference_cube.long_name == cube.standard_name + "_difference"
    assert difference_cube.var_name == cube.var_name + "_difference"


def test_difference_no_time_coord(cube):
    """Difference of cubes with no time coordinate."""
    c1 = cube.extract(iris.Constraint(time=datetime.datetime(2022, 9, 21, 3, 30)))
    c1.remove_coord("time")
    c2 = c1.copy()
    del c2.attributes["cset_comparison_base"]
    cubes = iris.cube.CubeList([c1, c2])
    difference_cube = misc.difference(cubes)
    assert isinstance(difference_cube, iris.cube.Cube)
    assert np.allclose(
        difference_cube.data, np.zeros_like(difference_cube.data), atol=1e-9
    )


def test_difference_no_common_points(cube):
    """Test exception when there are no common time points between cubes."""
    other_cube = cube.copy()
    # Offset times by 6 hours.
    new_times = other_cube.coord("time").points.copy()
    new_times += 6
    other_cube.coord("time").points = new_times
    del other_cube.attributes["cset_comparison_base"]
    cubes = iris.cube.CubeList([cube, other_cube])
    with pytest.raises(ValueError, match="No common time points found!"):
        misc.difference(cubes)


def test_difference_incorrect_number_of_cubes(cube):
    """Test exception when incorrect number of cubes provided."""
    no_cubes = iris.cube.CubeList([])
    with pytest.raises(ValueError, match="cubes should contain exactly 2 cubes."):
        misc.difference(no_cubes)

    one_cube = iris.cube.CubeList([cube])
    with pytest.raises(ValueError, match="cubes should contain exactly 2 cubes."):
        misc.difference(one_cube)

    three_cubes = iris.cube.CubeList([cube, cube, cube])
    with pytest.raises(ValueError, match="cubes should contain exactly 2 cubes."):
        misc.difference(three_cubes)


def test_difference_different_data_shape_regrid(cube):
    """Test when data shape differs, but gets regridded.

    For any cube shapes differ.
    """
    rearranged_cube = cube.copy()
    rearranged_cube = rearranged_cube[:, :, 1:]
    del cube.attributes["cset_comparison_base"]
    cubes = iris.cube.CubeList([rearranged_cube, cube])
    difference = misc.difference(cubes)
    assert isinstance(difference, iris.cube.Cube)
    assert difference.shape == cube.shape
    assert difference.shape != rearranged_cube.shape


def test_difference_grid_staggering_regrid(cube):
    """Test when data considered on staggered grid, so gets regridded."""
    rearranged_cube = cube.copy()
    rearranged_cube.rename("eastward_wind_at_10m")
    del cube.attributes["cset_comparison_base"]
    cubes = iris.cube.CubeList([rearranged_cube, cube])
    difference = misc.difference(cubes)
    assert isinstance(difference, iris.cube.Cube)
    assert difference.shape == cube.shape


def test_difference_different_model_types(cube):
    """Other cube is flipped when model types differ."""
    flipped = cube.copy()
    flipped_coord = flipped.coord("grid_latitude")
    flipped_coord.points = np.flip(flipped_coord.points)
    flipped.data = np.flip(flipped.data, flipped_coord.cube_dims(flipped))
    del flipped.attributes["cset_comparison_base"]
    cubes = iris.cube.CubeList([cube, flipped])

    # Take difference.
    difference_cube = misc.difference(cubes)

    assert isinstance(difference_cube, iris.cube.Cube)
    # As both cubes use the same data, check the difference is zero.
    assert np.allclose(
        difference_cube.data, np.zeros_like(difference_cube.data), atol=1e-9
    )


def test_extract_common_time_points():
    """Common times are selected."""
    coord1 = iris.coords.DimCoord(
        [0, 24, 48], standard_name="time", units="hours since 1970-01-01"
    )
    coord2 = iris.coords.DimCoord(
        [0, 24, 48], standard_name="time", units="hours since 1970-01-02"
    )
    c1 = iris.cube.Cube(
        [1, 2, 3], long_name="my_var", dim_coords_and_dims=[(coord1, 0)]
    )
    c2 = iris.cube.Cube(
        [2, 3, 4], long_name="my_var", dim_coords_and_dims=[(coord2, 0)]
    )
    c1_common, c2_common = misc._extract_common_time_points(c1, c2)
    assert all(c1_common.coord("time").points == [24, 48])
    assert all(c2_common.coord("time").points == [0, 24])


def test_extract_common_time_points_hour():
    """Common hours are selected."""
    coord1 = iris.coords.DimCoord([0, 6, 12], long_name="hour", units="hours")
    coord2 = iris.coords.DimCoord([6, 12, 18], long_name="hour", units="hours")
    c1 = iris.cube.Cube(
        [1, 2, 3], long_name="my_var", dim_coords_and_dims=[(coord1, 0)]
    )
    c2 = iris.cube.Cube(
        [2, 3, 4], long_name="my_var", dim_coords_and_dims=[(coord2, 0)]
    )
    c1_common, c2_common = misc._extract_common_time_points(c1, c2)
    assert all(c1_common.coord("hour").points == [6, 12])
    assert c1_common == c2_common


def test_extract_common_time_points_no_time_coord():
    """Cubes without time coordinates are passed through unchanged."""
    coord = iris.coords.DimCoord([1, 2, 3], long_name="number", units="1")
    c1 = iris.cube.Cube([1, 2, 3], long_name="my_var", dim_coords_and_dims=[(coord, 0)])
    c2 = c1.copy()
    c1_common, c2_common = misc._extract_common_time_points(c1, c2)
    assert c1_common == c1
    assert c2_common == c2


def test_extract_common_time_points_no_overlap():
    """ValueError when there are no common times."""
    coord1 = iris.coords.DimCoord(
        [0, 6, 12], standard_name="time", units="hours since 1970-01-01"
    )
    coord2 = iris.coords.DimCoord(
        [18, 24, 30], standard_name="time", units="hours since 1970-01-01"
    )
    c1 = iris.cube.Cube(
        [1, 2, 3], long_name="my_var", dim_coords_and_dims=[(coord1, 0)]
    )
    c2 = iris.cube.Cube(
        [4, 5, 6], long_name="my_var", dim_coords_and_dims=[(coord2, 0)]
    )
    with pytest.raises(ValueError, match="No common time points found!"):
        misc._extract_common_time_points(c1, c2)
