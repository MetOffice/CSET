# © Crown copyright, Met Office (2022-2026) and CSET contributors.
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

"""Test precipitation operators."""

from pathlib import Path

import cf_units
import iris.cube
import numpy as np
import pytest

from CSET.operators import precipitation

DATA_DIR = Path(__file__).resolve().parent.parent / "test_data" / "rainfall"


def test_maul_properties_wrong_output(maul_mask):
    """Ensure fails if get unexpected output argument."""
    with pytest.raises(
        ValueError,
        match="Unexpected value for output. Expected number, depth or base. Got top.",
    ):
        precipitation.MAUL_properties(maul_mask, output="top")


def test_maul_properties_not_binary_input(maul_mask):
    """Ensure fails if get non-binary input."""
    maul_mask.data += 1.0
    with pytest.raises(
        ValueError,
        match="Data contains values that are not 0 or 1, only masked data should be used.",
    ):
        precipitation.MAUL_properties(maul_mask, output="number")


def test_maul_properties_3D_number(maul_mask, precalc_maul_number_3d):
    """Ensure correct number of MAULs generated for 3D field."""
    assert np.allclose(
        precipitation.MAUL_properties(maul_mask, output="number").data,
        precalc_maul_number_3d.data,
        rtol=1e-2,
        atol=1e-6,
    )


def test_maul_properties_3D_number_name(maul_mask):
    """Ensure correct name given to cube in maul properties for number of mauls."""
    expected_name = "Number_of_MAULs"
    assert (
        expected_name
        == precipitation.MAUL_properties(maul_mask, output="number").name()
    )


def test_maul_properties_3D_number_units(maul_mask):
    """Ensure correct units given to cube in maul properties for number of mauls."""
    expected_units = cf_units.Unit("1")
    assert (
        expected_units
        == precipitation.MAUL_properties(maul_mask, output="number").units
    )


def test_maul_properties_3D_base(maul_mask, precalc_maul_base_3d):
    """Ensure correct base of MAULs generated for 3D field."""
    assert np.allclose(
        precipitation.MAUL_properties(maul_mask, output="base").data,
        precalc_maul_base_3d.data,
        rtol=1e-2,
        atol=1e-6,
        equal_nan=True,
    )


def test_maul_properties_3D_base_name(maul_mask):
    """Ensure correct name given to cube in maul properties for MAUL base."""
    expected_name = "MAUL_base_height"
    assert (
        expected_name == precipitation.MAUL_properties(maul_mask, output="base").name()
    )


def test_maul_properties_3D_base_units(maul_mask):
    """Ensure correct units given to cube in maul properties for MAUL base."""
    expected_units = cf_units.Unit("m")
    assert (
        expected_units == precipitation.MAUL_properties(maul_mask, output="base").units
    )


def test_maul_properties_3D_depth(maul_mask, precalc_maul_depth_3d):
    """Ensure correct depth of MAULs generated for 3D field."""
    assert np.allclose(
        precipitation.MAUL_properties(maul_mask, output="depth").data,
        precalc_maul_depth_3d.data,
        rtol=1e-2,
        atol=1e-6,
        equal_nan=True,
    )


def test_maul_properties_3D_depth_name(maul_mask):
    """Ensure correct name given to cube in maul properties for MAUL depth."""
    expected_name = "MAUL_depth"
    assert (
        expected_name == precipitation.MAUL_properties(maul_mask, output="depth").name()
    )


def test_maul_properties_3D_depth_units(maul_mask):
    """Ensure correct units given to cube in maul properties for MAUL depth."""
    expected_units = cf_units.Unit("m")
    assert (
        expected_units == precipitation.MAUL_properties(maul_mask, output="depth").units
    )


def test_maul_properties_3D_number_cubelist(maul_mask, precalc_maul_number_3d):
    """Ensure correct number of MAULs generated for 3D field in a cubelist."""
    input_list = iris.cube.CubeList([maul_mask, maul_mask])
    expected_list = precipitation.MAUL_properties(input_list, output="number")
    actual_list = iris.cube.CubeList([precalc_maul_number_3d, precalc_maul_number_3d])
    for cube_a, cube_b in zip(expected_list, actual_list, strict=True):
        assert np.allclose(
            cube_a.data,
            cube_b.data,
            rtol=1e-2,
            atol=1e-6,
        )


def test_maul_properties_3D_base_cubelist(maul_mask, precalc_maul_base_3d):
    """Ensure correct base of MAULs generated for 3D field in a cubelist."""
    input_list = iris.cube.CubeList([maul_mask, maul_mask])
    expected_list = precipitation.MAUL_properties(input_list, output="base")
    actual_list = iris.cube.CubeList([precalc_maul_base_3d, precalc_maul_base_3d])
    for cube_a, cube_b in zip(expected_list, actual_list, strict=True):
        assert np.allclose(
            cube_a.data, cube_b.data, rtol=1e-2, atol=1e-6, equal_nan=True
        )


def test_maul_properties_3D_depth_cubelist(maul_mask, precalc_maul_depth_3d):
    """Ensure correct depth of MAULs generated for 3D field in a cubelist."""
    input_list = iris.cube.CubeList([maul_mask, maul_mask])
    expected_list = precipitation.MAUL_properties(input_list, output="depth")
    actual_list = iris.cube.CubeList([precalc_maul_depth_3d, precalc_maul_depth_3d])
    for cube_a, cube_b in zip(expected_list, actual_list, strict=True):
        assert np.allclose(
            cube_a.data, cube_b.data, rtol=1e-2, atol=1e-6, equal_nan=True
        )


def test_maul_properties_4D_time_number(maul_mask_time, precalc_maul_number_4d_time):
    """Ensure correct number of MAULs generated for 4D field varying in time."""
    assert np.allclose(
        precipitation.MAUL_properties(maul_mask_time, output="number").data,
        precalc_maul_number_4d_time.data,
        rtol=1e-2,
        atol=1e-6,
    )


def test_maul_properties_4d_time_base(maul_mask_time, precalc_maul_base_4d_time):
    """Ensure correct base of MAULs generated for 4D field varying in time."""
    assert np.allclose(
        precipitation.MAUL_properties(maul_mask_time, output="base").data,
        precalc_maul_base_4d_time.data,
        rtol=1e-2,
        atol=1e-6,
        equal_nan=True,
    )


def test_maul_properties_4d_time_depth(maul_mask_time, precalc_maul_depth_4d_time):
    """Ensure correct depth of MAULs generated for 4D field varying in time."""
    assert np.allclose(
        precipitation.MAUL_properties(maul_mask_time, output="depth").data,
        precalc_maul_depth_4d_time.data,
        rtol=1e-2,
        atol=1e-6,
        equal_nan=True,
    )


def test_maul_properties_4d_realization_number(
    maul_mask_member, precalc_maul_number_4d_realization
):
    """Ensure correct number of MAULs generated for 4D field varying with realization."""
    assert np.allclose(
        precipitation.MAUL_properties(maul_mask_member, output="number").data,
        precalc_maul_number_4d_realization.data,
        rtol=1e-2,
        atol=1e-6,
    )


def test_maul_properties_4D_realization_base(
    maul_mask_member, precalc_maul_base_4d_realization
):
    """Ensure correct base of MAULs generated for 4D field with varying realization."""
    assert np.allclose(
        precipitation.MAUL_properties(maul_mask_member, output="base").data,
        precalc_maul_base_4d_realization.data,
        rtol=1e-2,
        atol=1e-6,
        equal_nan=True,
    )


def test_maul_properties_4D_realization_depth(
    maul_mask_member, precalc_maul_depth_4d_realization
):
    """Ensure correct depth of MAULs generated for 4D field with varying realization."""
    assert np.allclose(
        precipitation.MAUL_properties(maul_mask_member, output="depth").data,
        precalc_maul_depth_4d_realization.data,
        rtol=1e-2,
        atol=1e-6,
        equal_nan=True,
    )


def test_maul_properties_5D_number(maul_mask_all, precalc_maul_number_5d):
    """Ensure correct number of MAULs generated for 5D field."""
    assert np.allclose(
        precipitation.MAUL_properties(maul_mask_all, output="number").data,
        precalc_maul_number_5d.data,
        rtol=1e-2,
        atol=1e-6,
    )


def test_maul_properties_5D_base(maul_mask_all, precalc_maul_base_5d):
    """Ensure correct base of MAULs generated for 5D field."""
    assert np.allclose(
        precipitation.MAUL_properties(maul_mask_all, output="base").data,
        precalc_maul_base_5d.data,
        rtol=1e-2,
        atol=1e-6,
        equal_nan=True,
    )


def test_maul_properties_5D_depth(maul_mask_all, precalc_maul_depth_5d):
    """Ensure correct depth of MAULs generated for 5D field."""
    assert np.allclose(
        precipitation.MAUL_properties(maul_mask_all, output="depth").data,
        precalc_maul_depth_5d.data,
        rtol=1e-2,
        atol=1e-6,
        equal_nan=True,
    )


def test_rain_amount_to_rate_with_bounds():
    """Test conversion works with time bounds."""
    cube_in = iris.load_cube(DATA_DIR / "rain_amount_bounds.nc")
    cube = cube_in.copy()
    out = precipitation.convert_rainfall_amount_to_rate(cube)
    assert out.units.is_convertible("kg m-2 s-1")
    expected = np.asarray(cube_in.data, dtype=float) / 1800.0
    assert np.allclose(out.data, expected, rtol=0.0, atol=1e-12)


def test_rain_amount_to_rate_without_bounds_uses_time_points():
    """Test conversion works without time bounds."""
    cube_in = iris.load_cube(DATA_DIR / "rain_amount_no_bounds.nc")
    cube = cube_in.copy()
    out = precipitation.convert_rainfall_amount_to_rate(cube)
    assert out.units.is_convertible("kg m-2 s-1")
    expected = np.asarray(cube_in.data, dtype=float) / 1800.0
    assert np.allclose(out.data, expected, rtol=0.0, atol=1e-12)


def test_rain_rate_is_left_untouched():
    """Test that rainfall rate is left untouched."""
    cube_in = iris.load_cube(DATA_DIR / "rain_rate.nc")
    cube = cube_in.copy()
    out = precipitation.convert_rainfall_amount_to_rate(cube)
    assert out.units == cube_in.units
    assert np.allclose(out.data, cube_in.data, rtol=0.0, atol=0.0)


def test_non_rainfall_units_are_skipped():
    """Test that non-rainfall units are skipped."""
    cube_in = iris.load_cube(DATA_DIR / "not_rainfall_units.nc")
    cube = cube_in.copy()
    out = precipitation.convert_rainfall_amount_to_rate(cube)
    assert out.units == cube_in.units
    assert np.allclose(out.data, cube_in.data, rtol=0.0, atol=0.0)


def test_raises_if_no_time_coordinate():
    """Test that error raised if no time coordinate."""
    cube = iris.load_cube(DATA_DIR / "no_time.nc")
    with pytest.raises(ValueError, match="No time coordinate"):
        precipitation.convert_rainfall_amount_to_rate(cube)


def test_raises_if_single_time_point_no_bounds():
    """Test that error raised if only one time available."""
    cube = iris.load_cube(DATA_DIR / "single_time.nc")
    with pytest.raises(ValueError, match="single time point"):
        precipitation.convert_rainfall_amount_to_rate(cube)


def test_raises_if_nonpositive_interval_from_bounds():
    """Test that error raised if time interval is negative."""
    cube = iris.load_cube(DATA_DIR / "bad_bounds_zero.nc")
    with pytest.raises(ValueError, match="Non-positive rainfall accumulation interval"):
        precipitation.convert_rainfall_amount_to_rate(cube)
