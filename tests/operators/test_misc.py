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

"""Test miscellaneous operators."""

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
    cube = cube.copy()
    assert "STASH" in cube.attributes
    cube = misc.remove_attribute(cube, "STASH")[0]
    assert "STASH" not in cube.attributes


def test_remove_attribute_cubelist(cubes):
    """Remove attribute from a CubeList."""
    cubes = cubes.copy()
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


def test_combine_singlecube_into_cubelist(source_cube):
    """Test case of single cube into cubelist."""
    cubelist = misc.combine_cubes_into_cubelist(source_cube)

    expected_cubelist = (
        "[<iris 'Cube' of surface_altitude / (m) (latitude: 200; longitude: 200)>]"
    )
    assert repr(cubelist) in expected_cubelist


def test_combine_singlecubelist_into_cubelist(source_cube, transect_source_cube):
    """Test case of single cubelist into cubelist."""
    cubelist = misc.combine_cubes_into_cubelist(
        iris.cube.CubeList([source_cube, transect_source_cube])
    )

    expected_cubelist = "[<iris 'Cube' of surface_altitude / (m) (latitude: 200; longitude: 200)>,\n<iris 'Cube' of air_temperature / (K) (time: 2; pressure: 16; latitude: 6; longitude: 6)>]"
    assert repr(cubelist) in expected_cubelist


def test_combine_single_noncompliant_into_cubelist():
    """Test case of single object which isn't cube or cubelist."""
    with pytest.raises(TypeError):
        misc.combine_cubes_into_cubelist("hello")


def test_combine_multiplecube_into_cubelist(source_cube, transect_source_cube):
    """Test case of multiple cube into cubelist."""
    cubelist = misc.combine_cubes_into_cubelist(source_cube, a=transect_source_cube)

    expected_cubelist = "[<iris 'Cube' of surface_altitude / (m) (latitude: 200; longitude: 200)>,\n<iris 'Cube' of air_temperature / (K) (time: 2; pressure: 16; latitude: 6; longitude: 6)>]"

    assert repr(cubelist) in expected_cubelist


def test_combine_multiple_cube_and_noncompliant_into_cubelist(source_cube):
    """Test case of a valid cube with some non compliant data which isn't cube or cubelist."""
    with pytest.raises(TypeError):
        misc.combine_cubes_into_cubelist(source_cube, a="hello")


def test_combine_multiplecube_mixed_into_cubelist(source_cube, transect_source_cube):
    """Test case of multiple cubes and cubelist into cubelist."""
    cubelist = misc.combine_cubes_into_cubelist(source_cube, a=transect_source_cube)
    out_cubelist = misc.combine_cubes_into_cubelist(
        source_cube, a=cubelist, b=transect_source_cube
    )

    expected_cubelist = "[<iris 'Cube' of surface_altitude / (m) (latitude: 200; longitude: 200)>,\n<iris 'Cube' of surface_altitude / (m) (latitude: 200; longitude: 200)>,\n<iris 'Cube' of air_temperature / (K) (time: 2; pressure: 16; latitude: 6; longitude: 6)>,\n<iris 'Cube' of air_temperature / (K) (time: 2; pressure: 16; latitude: 6; longitude: 6)>]"

    assert repr(out_cubelist) in expected_cubelist
