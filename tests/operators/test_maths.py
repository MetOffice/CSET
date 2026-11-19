# © Crown copyright, Met Office (2022-2025) and CSET contributors.
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

import iris
import iris.analysis.calculus
import iris.coords
import iris.cube
import iris.exceptions
import numpy as np
import pytest

from CSET.operators import maths, read


def test_addition(cube):
    """Adds two objects together."""
    a = cube + cube
    b = maths.addition(cube, cube)
    assert np.allclose(b.data, a.data, atol=1e-5, equal_nan=True)


def test_addition_failure(cube):
    """Tests arrays of different units produces an error."""
    a = read.read_cube("tests/test_data/convection/ECFlagB.nc")
    with pytest.raises(iris.exceptions.NotYetImplementedError):
        maths.addition(cube, a)


def test_subtraction(cube):
    """Subtracts one object from another one."""
    a = cube - cube
    b = maths.subtraction(cube, cube)
    assert np.allclose(b.data, a.data, atol=1e-5, equal_nan=True)


def test_subtraction_failure(cube):
    """Tests arrays of different units produces an error."""
    a = read.read_cube("tests/test_data/convection/ECFlagB.nc")
    with pytest.raises(iris.exceptions.NotYetImplementedError):
        maths.subtraction(cube, a)


def test_subtraction_cubelist(cube):
    """Subtracts one cubelist from another."""
    a = iris.cube.CubeList([cube, cube])
    b = maths.subtraction(a, a)
    assert isinstance(b, iris.cube.CubeList)
    assert np.allclose(b[0].data, 0.0, atol=1e-5, equal_nan=True)
    assert np.allclose(b[1].data, 0.0, atol=1e-5, equal_nan=True)


def test_subtraction_cubelist_cube(cube):
    """Subtracts a cube from a cubelist."""
    a = iris.cube.CubeList([cube, cube])
    b = maths.subtraction(a, cube)
    assert isinstance(b, iris.cube.CubeList)
    assert np.allclose(b[0].data, 0.0, atol=1e-5, equal_nan=True)
    assert np.allclose(b[1].data, 0.0, atol=1e-5, equal_nan=True)


def test_subtraction_single_cubelist_cube(cube):
    """Subtracts a cube from a cubelist with single entry."""
    a = iris.cube.CubeList([cube])
    b = maths.subtraction(a, cube)
    assert isinstance(b, iris.cube.Cube)
    assert np.allclose(b.data, 0.0, atol=1e-5, equal_nan=True)


def test_subtraction_cubelist_from_cube(cube):
    """Subtracts a cubelist from a cube."""
    a = iris.cube.CubeList([cube, cube])
    b = maths.subtraction(cube, a)
    assert isinstance(b, iris.cube.CubeList)
    assert np.allclose(b[0].data, 0.0, atol=1e-5, equal_nan=True)
    assert np.allclose(b[1].data, 0.0, atol=1e-5, equal_nan=True)


def test_division(cube):
    """Divides one object by another."""
    a = cube / cube
    b = maths.division(cube, cube)
    assert np.allclose(b.data, a.data, atol=1e-5, equal_nan=True)


def test_division_failure(cube):
    """Tests arrays of different shapes produces an error."""
    a = read.read_cube("tests/test_data/convection/ECFlagB.nc")
    with pytest.raises(ValueError):
        maths.division(cube, a)


def test_multiplication(cube):
    """Multiplies one object by another."""
    a = cube * cube
    b = maths.multiplication(cube, cube)
    assert np.allclose(b.data, a.data, atol=1e-5, equal_nan=True)


def test_multiplication_cubelist(cube):
    """Multiplies one object by another as a CubeList."""
    # First setup expected cube by using a squared approach as the simplest example.
    a = cube * cube
    # Next create a CubeList from the expected cube output, for efficiency this is kept the same.
    expected_list = iris.cube.CubeList([a, a])
    # Create a list of input cubes to be tested that will match the result from the expected.
    input_cubes = iris.cube.CubeList([cube, cube])
    # Use the operator and test match with expected data.
    actual_cubelist = maths.multiplication(input_cubes, input_cubes)
    for cube_a, cube_b in zip(expected_list, actual_cubelist, strict=True):
        assert np.allclose(
            cube_a.data, cube_b.data, rtol=1e-6, atol=1e-2, equal_nan=True
        )


def test_multiplication_rename(cube):
    """Tests renaming of multiplication cube."""
    expected_name = f"{cube.name()}_x_{cube.name()}"
    assert expected_name == maths.multiplication(cube, cube).name()


def test_multiplication_failure(cube):
    """Tests arrays of different shapes produces an error."""
    a = read.read_cube("tests/test_data/convection/ECFlagB.nc")
    with pytest.raises(ValueError):
        maths.multiplication(cube, a)


def test_differentitate(vertical_profile_cube):
    """Test a differentitation of a vertical profile cube."""
    expected_cube = iris.analysis.calculus.differentiate(
        vertical_profile_cube, "pressure"
    )
    actual_cube = maths.differentiate(vertical_profile_cube, coordinate="pressure")
    assert np.allclose(actual_cube.data, expected_cube.data, rtol=1e-6, atol=1e-2)


def test_differentitate_cubelist(long_forecast):
    """Test a differentiation of a CubeList."""
    # Create input CubeList.
    input_cubes = iris.cube.CubeList([long_forecast, long_forecast])
    # Create expected cube and then convert to a CubeList
    expectedcube = iris.analysis.calculus.differentiate(long_forecast, "time")
    expected_cubelist = iris.cube.CubeList([expectedcube, expectedcube])
    new_cubelist = maths.differentiate(input_cubes, "time")
    for actual, expected in zip(new_cubelist, expected_cubelist, strict=True):
        assert np.allclose(actual.data, expected.data, rtol=1e-6, atol=1e-2)


def test_round_data_rounds_values_1_dec_place():
    """Data is rounded to the requested number of decimals."""
    data = np.array([[1.234, 5.678], [-2.345, 9.999]])
    cb = iris.cube.Cube(data, var_name="test_field")
    result = maths.round_data(cb, decimals=1)
    expected = np.array([[1.2, 5.7], [-2.3, 10.0]])
    np.testing.assert_allclose(result.data, expected)


def test_round_data_rounds_values_2_dec_place():
    """Data is rounded to the requested number of decimals."""
    data = np.array([[1.234, 5.678], [-2.345, 9.999]])
    cb = iris.cube.Cube(data, var_name="test_field")
    result = maths.round_data(cb, decimals=2)
    expected = np.array([[1.23, 5.68], [-2.35, 10.0]])
    np.testing.assert_allclose(result.data, expected)


def test_round_data_rounds_values_fail_bad_decimal():
    """Data is rounded to the requested number of decimals."""
    data = np.array([[1.234, 5.678], [-2.345, 9.999]])
    cb = iris.cube.Cube(data, var_name="test_field")
    with pytest.raises(TypeError, match="decimals must be an integer, got float: 1.1"):
        maths.round_data(cb, decimals=1.1)


def test_round_data_preserves_nans():
    """NaNs are left as NaN."""
    data = np.array([[1.234, np.nan], [-2.345, 9.999]])
    cb = iris.cube.Cube(data, var_name="test_field")
    result = maths.round_data(cb, decimals=1)
    assert np.isnan(result.data[0, 1])
    np.testing.assert_allclose(result.data[0, 0], 1.2)


def test_round_data_preserves_mask():
    """Masked points stay masked."""
    data = np.array([[1.234, np.nan], [-2.345, 9.999]])
    cb = iris.cube.Cube(data, var_name="test_field")
    mask = np.array([[False, True], [False, False]])
    cb.data = np.ma.masked_array(cb.data, mask=mask)
    result = maths.round_data(cb, decimals=1)
    assert np.ma.isMaskedArray(result.data)
    np.testing.assert_array_equal(result.data.mask, mask)
