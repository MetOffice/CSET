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


def test_additon_failure(cube):
    """Tests arrays of different shapes produces an error."""
    a = read.read_cube("tests/test_data/convection/ECFlagB.nc")
    with pytest.raises(ValueError):
        misc.addition(cube, a)


def test_subtraction(cube):
    """Subtracts one object from another one."""
    a = cube - cube
    b = misc.subtraction(cube, cube)
    assert np.allclose(b.data, a.data, atol=1e-5, equal_nan=True)


def test_subtraction_failure(cube):
    """Tests arrays of different shapes produces an error."""
    a = read.read_cube("tests/test_data/convection/ECFlagB.nc")
    with pytest.raises(ValueError):
        misc.subtraction(cube, a)


def test_division(cube):
    """Divides one object by another."""
    a = cube / cube
    b = misc.division(cube)
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
