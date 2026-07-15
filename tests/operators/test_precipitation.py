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

import cf_units
import iris.cube
import numpy as np
import pytest

from CSET.operators import precipitation


def test_maul_properties_wrong_output(maul_mask, u_wind_maul, v_wind_maul):
    """Ensure fails if get unexpected output argument."""
    with pytest.raises(
        ValueError,
        match="Unexpected value for output. Expected number, base, depth or wind_below. Got top.",
    ):
        precipitation.MAUL_properties(maul_mask, u_wind_maul, v_wind_maul, output="top")


def test_maul_properties_not_binary_input(maul_mask, u_wind_maul, v_wind_maul):
    """Ensure fails if get non-binary input."""
    maul_mask.data += 1.0
    with pytest.raises(
        ValueError,
        match="Data contains values that are not 0 or 1, only masked data should be used.",
    ):
        precipitation.MAUL_properties(
            maul_mask, u_wind_maul, v_wind_maul, output="number"
        )


def test_maul_properties_3D_number(
    maul_mask, u_wind_maul, v_wind_maul, precalc_maul_number_3d
):
    """Ensure correct number of MAULs generated for 3D field."""
    assert np.allclose(
        precipitation.MAUL_properties(
            maul_mask, u_wind_maul, v_wind_maul, output="number"
        ).data,
        precalc_maul_number_3d.data,
        rtol=1e-2,
        atol=1e-6,
    )


def test_maul_properties_3D_number_name(maul_mask, u_wind_maul, v_wind_maul):
    """Ensure correct name given to cube in maul properties for number of mauls."""
    expected_name = "Number_of_MAULs"
    assert (
        expected_name
        == precipitation.MAUL_properties(
            maul_mask, u_wind_maul, v_wind_maul, output="number"
        ).name()
    )


def test_maul_properties_3D_number_units(maul_mask, u_wind_maul, v_wind_maul):
    """Ensure correct units given to cube in maul properties for number of mauls."""
    expected_units = cf_units.Unit("1")
    assert (
        expected_units
        == precipitation.MAUL_properties(
            maul_mask, u_wind_maul, v_wind_maul, output="number"
        ).units
    )


def test_maul_properties_3D_base(
    maul_mask, u_wind_maul, v_wind_maul, precalc_maul_base_3d
):
    """Ensure correct base of MAULs generated for 3D field."""
    assert np.allclose(
        precipitation.MAUL_properties(
            maul_mask, u_wind_maul, v_wind_maul, output="base"
        ).data,
        precalc_maul_base_3d.data,
        rtol=1e-2,
        atol=1e-6,
        equal_nan=True,
    )


def test_maul_properties_3D_base_name(maul_mask, u_wind_maul, v_wind_maul):
    """Ensure correct name given to cube in maul properties for MAUL base."""
    expected_name = "MAUL_base_height"
    assert (
        expected_name
        == precipitation.MAUL_properties(
            maul_mask, u_wind_maul, v_wind_maul, output="base"
        ).name()
    )


def test_maul_properties_3D_base_units(maul_mask, u_wind_maul, v_wind_maul):
    """Ensure correct units given to cube in maul properties for MAUL base."""
    expected_units = cf_units.Unit("m")
    assert (
        expected_units
        == precipitation.MAUL_properties(
            maul_mask, u_wind_maul, v_wind_maul, output="base"
        ).units
    )


def test_maul_properties_3D_depth(
    maul_mask, u_wind_maul, v_wind_maul, precalc_maul_depth_3d
):
    """Ensure correct depth of MAULs generated for 3D field."""
    assert np.allclose(
        precipitation.MAUL_properties(
            maul_mask, u_wind_maul, v_wind_maul, output="depth"
        ).data,
        precalc_maul_depth_3d.data,
        rtol=1e-2,
        atol=1e-6,
        equal_nan=True,
    )


def test_maul_properties_3D_depth_name(maul_mask, u_wind_maul, v_wind_maul):
    """Ensure correct name given to cube in maul properties for MAUL depth."""
    expected_name = "MAUL_depth"
    assert (
        expected_name
        == precipitation.MAUL_properties(
            maul_mask, u_wind_maul, v_wind_maul, output="depth"
        ).name()
    )


def test_maul_properties_3D_depth_units(maul_mask, u_wind_maul, v_wind_maul):
    """Ensure correct units given to cube in maul properties for MAUL depth."""
    expected_units = cf_units.Unit("m")
    assert (
        expected_units
        == precipitation.MAUL_properties(
            maul_mask, u_wind_maul, v_wind_maul, output="depth"
        ).units
    )


def test_maul_properties_3D_number_cubelist(
    maul_mask, u_wind_maul, v_wind_maul, precalc_maul_number_3d
):
    """Ensure correct number of MAULs generated for 3D field in a cubelist."""
    input_list = iris.cube.CubeList([maul_mask, maul_mask])
    v_list = iris.cube.CubeList([v_wind_maul, v_wind_maul])
    u_list = iris.cube.CubeList([u_wind_maul, u_wind_maul])
    expected_list = precipitation.MAUL_properties(
        input_list, u_list, v_list, output="number"
    )
    actual_list = iris.cube.CubeList([precalc_maul_number_3d, precalc_maul_number_3d])
    for cube_a, cube_b in zip(expected_list, actual_list, strict=True):
        assert np.allclose(
            cube_a.data,
            cube_b.data,
            rtol=1e-2,
            atol=1e-6,
        )


def test_maul_properties_3D_base_cubelist(
    maul_mask, u_wind_maul, v_wind_maul, precalc_maul_base_3d
):
    """Ensure correct base of MAULs generated for 3D field in a cubelist."""
    input_list = iris.cube.CubeList([maul_mask, maul_mask])
    v_list = iris.cube.CubeList([v_wind_maul, v_wind_maul])
    u_list = iris.cube.CubeList([u_wind_maul, u_wind_maul])
    expected_list = precipitation.MAUL_properties(
        input_list, u_list, v_list, output="base"
    )
    actual_list = iris.cube.CubeList([precalc_maul_base_3d, precalc_maul_base_3d])
    for cube_a, cube_b in zip(expected_list, actual_list, strict=True):
        assert np.allclose(
            cube_a.data, cube_b.data, rtol=1e-2, atol=1e-6, equal_nan=True
        )


def test_maul_properties_3D_depth_cubelist(
    maul_mask, u_wind_maul, v_wind_maul, precalc_maul_depth_3d
):
    """Ensure correct depth of MAULs generated for 3D field in a cubelist."""
    input_list = iris.cube.CubeList([maul_mask, maul_mask])
    v_list = iris.cube.CubeList([v_wind_maul, v_wind_maul])
    u_list = iris.cube.CubeList([u_wind_maul, u_wind_maul])
    expected_list = precipitation.MAUL_properties(
        input_list, u_list, v_list, output="depth"
    )
    actual_list = iris.cube.CubeList([precalc_maul_depth_3d, precalc_maul_depth_3d])
    for cube_a, cube_b in zip(expected_list, actual_list, strict=True):
        assert np.allclose(
            cube_a.data, cube_b.data, rtol=1e-2, atol=1e-6, equal_nan=True
        )


def test_maul_properties_4D_time_number(
    maul_mask_time, u_wind_maul_time, v_wind_maul_time, precalc_maul_number_4d_time
):
    """Ensure correct number of MAULs generated for 4D field varying in time."""
    assert np.allclose(
        precipitation.MAUL_properties(
            maul_mask_time, u_wind_maul_time, v_wind_maul_time, output="number"
        ).data,
        precalc_maul_number_4d_time.data,
        rtol=1e-2,
        atol=1e-6,
    )


def test_maul_properties_4d_time_base(
    maul_mask_time, u_wind_maul_time, v_wind_maul_time, precalc_maul_base_4d_time
):
    """Ensure correct base of MAULs generated for 4D field varying in time."""
    assert np.allclose(
        precipitation.MAUL_properties(
            maul_mask_time, u_wind_maul_time, v_wind_maul_time, output="base"
        ).data,
        precalc_maul_base_4d_time.data,
        rtol=1e-2,
        atol=1e-6,
        equal_nan=True,
    )


def test_maul_properties_4d_time_depth(
    maul_mask_time, u_wind_maul_time, v_wind_maul_time, precalc_maul_depth_4d_time
):
    """Ensure correct depth of MAULs generated for 4D field varying in time."""
    assert np.allclose(
        precipitation.MAUL_properties(
            maul_mask_time, u_wind_maul_time, v_wind_maul_time, output="depth"
        ).data,
        precalc_maul_depth_4d_time.data,
        rtol=1e-2,
        atol=1e-6,
        equal_nan=True,
    )


def test_maul_properties_4d_realization_number(
    maul_mask_member,
    u_wind_maul_member,
    v_wind_maul_member,
    precalc_maul_number_4d_realization,
):
    """Ensure correct number of MAULs generated for 4D field varying with realization."""
    assert np.allclose(
        precipitation.MAUL_properties(
            maul_mask_member, u_wind_maul_member, v_wind_maul_member, output="number"
        ).data,
        precalc_maul_number_4d_realization.data,
        rtol=1e-2,
        atol=1e-6,
    )


def test_maul_properties_4D_realization_base(
    maul_mask_member,
    u_wind_maul_member,
    v_wind_maul_member,
    precalc_maul_base_4d_realization,
):
    """Ensure correct base of MAULs generated for 4D field with varying realization."""
    assert np.allclose(
        precipitation.MAUL_properties(
            maul_mask_member, u_wind_maul_member, v_wind_maul_member, output="base"
        ).data,
        precalc_maul_base_4d_realization.data,
        rtol=1e-2,
        atol=1e-6,
        equal_nan=True,
    )


def test_maul_properties_4D_realization_depth(
    maul_mask_member,
    u_wind_maul_member,
    v_wind_maul_member,
    precalc_maul_depth_4d_realization,
):
    """Ensure correct depth of MAULs generated for 4D field with varying realization."""
    assert np.allclose(
        precipitation.MAUL_properties(
            maul_mask_member, u_wind_maul_member, v_wind_maul_member, output="depth"
        ).data,
        precalc_maul_depth_4d_realization.data,
        rtol=1e-2,
        atol=1e-6,
        equal_nan=True,
    )


def test_maul_properties_5D_number(
    maul_mask_all, u_wind_maul_all, v_wind_maul_all, precalc_maul_number_5d
):
    """Ensure correct number of MAULs generated for 5D field."""
    assert np.allclose(
        precipitation.MAUL_properties(
            maul_mask_all, u_wind_maul_all, v_wind_maul_all, output="number"
        ).data,
        precalc_maul_number_5d.data,
        rtol=1e-2,
        atol=1e-6,
    )


def test_maul_properties_5D_base(
    maul_mask_all, u_wind_maul_all, v_wind_maul_all, precalc_maul_base_5d
):
    """Ensure correct base of MAULs generated for 5D field."""
    assert np.allclose(
        precipitation.MAUL_properties(
            maul_mask_all, u_wind_maul_all, v_wind_maul_all, output="base"
        ).data,
        precalc_maul_base_5d.data,
        rtol=1e-2,
        atol=1e-6,
        equal_nan=True,
    )


def test_maul_properties_5D_depth(
    maul_mask_all, u_wind_maul_all, v_wind_maul_all, precalc_maul_depth_5d
):
    """Ensure correct depth of MAULs generated for 5D field."""
    assert np.allclose(
        precipitation.MAUL_properties(
            maul_mask_all, u_wind_maul_all, v_wind_maul_all, output="depth"
        ).data,
        precalc_maul_depth_5d.data,
        rtol=1e-2,
        atol=1e-6,
        equal_nan=True,
    )


def _make_time_coord(points, bounds=None, units="hours since 2000-01-01 00:00:00"):
    """Make a time coordinate for rainfall tests."""
    return iris.coords.DimCoord(
        points,
        standard_name="time",
        units=units,
        bounds=bounds,
    )


def _make_cube(data, units, time_coord):
    """Make a cube for rainfall tests."""
    cube = iris.cube.Cube(data, units=units)
    cube.add_dim_coord(time_coord, 0)
    return cube


def test_convert_mass_accumulation():
    """Kg m-2 accumulations convert correctly."""
    bounds = np.array([[0, 1], [1, 2]])
    time = _make_time_coord([0.5, 1.5], bounds=bounds)
    cube = _make_cube([1.0, 2.0], "kg m-2", time)
    result = precipitation.convert_rainfall_depth_to_rate(cube)
    expected = np.array([1.0, 2.0]) / 3600.0

    np.testing.assert_allclose(result.data, expected)
    assert str(result.units) == "kg m-2 s-1"


def test_convert_basic_with_bounds():
    """Basic accumulation → rate conversion works."""
    bounds = np.array([[0, 1], [1, 2]])
    time = _make_time_coord([0.5, 1.5], bounds=bounds)
    cube = _make_cube([1.0, 2.0], "mm", time)
    result = precipitation.convert_rainfall_depth_to_rate(cube)
    expected = np.array([1.0, 2.0]) / 3600.0
    np.testing.assert_allclose(result.data, expected)


def test_convert_cm_accumulation():
    """Centimetre rainfall accumulations are scaled correctly."""
    bounds = np.array([[0, 1]])
    time = _make_time_coord([0.5], bounds=bounds)
    cube = _make_cube([1.0], "cm", time)
    result = precipitation.convert_rainfall_depth_to_rate(cube)
    expected = np.array([10.0]) / 3600.0  # 1 cm = 10 mm
    np.testing.assert_allclose(result.data, expected)


def test_skip_non_accumulation_or_rate():
    """Non-accumulation and already-rate cubes are left unchanged."""
    time = _make_time_coord([0, 1])
    rate_cube = _make_cube([0.1, 0.2], "kg m-2 s-1", time)
    temp_cube = _make_cube([280, 281], "K", time)
    out = precipitation.convert_rainfall_depth_to_rate([rate_cube, temp_cube])
    np.testing.assert_array_equal(out[0].data, rate_cube.data)
    np.testing.assert_array_equal(out[1].data, temp_cube.data)


def test_raises_without_time():
    """Raises if no time coordinate is present."""
    cube = iris.cube.Cube(np.array([1.0, 2.0]), units="mm")
    with pytest.raises(ValueError):
        precipitation.convert_rainfall_depth_to_rate(cube)


def test_convert_without_bounds_infers_duration():
    """Duration inferred correctly when bounds missing."""
    time = _make_time_coord([0, 1, 3])  # hours
    cube = _make_cube([1.0, 2.0, 3.0], "mm", time)
    result = precipitation.convert_rainfall_depth_to_rate(cube)
    # dt = [1, 2] → extended → [1, 2, 2] hours
    expected = np.array([1.0 / 3600.0, 2.0 / 7200.0, 3.0 / 7200.0])
    np.testing.assert_allclose(result.data, expected)
    assert str(result.units) == "kg m-2 s-1"


def test_raises_single_time_point_no_bounds():
    """Error if only one time point and no bounds."""
    time = _make_time_coord([0])
    cube = _make_cube([1.0], "mm", time)
    with pytest.raises(ValueError):
        precipitation.convert_rainfall_depth_to_rate(cube)


def test_raises_non_positive_duration():
    """Error if duration is zero or negative."""
    bounds = np.array([[1, 0], [2, 3]])  # first interval negative
    time = _make_time_coord([0.5, 2.5], bounds=bounds)
    cube = _make_cube([1.0, 2.0], "mm", time)
    with pytest.raises(ValueError):
        precipitation.convert_rainfall_depth_to_rate(cube)
