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


def test_maul_properties_wind_below(
    maul_mask, u_wind_maul, v_wind_maul, precalc_wind_below_maul
):
    """Ensure correct average wind below maul."""
    assert np.allclose(
        precipitation.MAUL_properties(
            maul_mask, u_wind_maul, v_wind_maul, output="wind_below"
        ).data,
        precalc_wind_below_maul.data,
        rtol=1e-2,
        atol=1e-6,
        equal_nan=True,
    )


def test_maul_properties_wind_below_name(
    maul_mask, u_wind_maul, v_wind_maul, precalc_wind_below_maul
):
    """Ensure correct average wind below maul name."""
    assert (
        precipitation.MAUL_properties(
            maul_mask, u_wind_maul, v_wind_maul, output="wind_below"
        ).name()
        == "windspeed_below_MAUL"
    )


def test_maul_properties_wind_below_units(
    maul_mask, u_wind_maul, v_wind_maul, precalc_wind_below_maul
):
    """Ensure correct average wind below maul units."""
    assert precipitation.MAUL_properties(
        maul_mask, u_wind_maul, v_wind_maul, output="wind_below"
    ).units == cf_units.Unit("m s^-1")


def test_maul_properties_wind_below_cubelist(
    maul_mask, u_wind_maul, v_wind_maul, precalc_wind_below_maul
):
    """Ensure correct average wind below maul in cubelist."""
    input_list = iris.cube.CubeList([maul_mask, maul_mask])
    v_list = iris.cube.CubeList([v_wind_maul, v_wind_maul])
    u_list = iris.cube.CubeList([u_wind_maul, u_wind_maul])
    expected_list = precipitation.MAUL_properties(
        input_list, u_list, v_list, output="wind_below"
    )
    actual_list = iris.cube.CubeList([precalc_wind_below_maul, precalc_wind_below_maul])
    for cube_a, cube_b in zip(expected_list, actual_list, strict=True):
        assert np.allclose(
            cube_a.data, cube_b.data, rtol=1e-2, atol=1e-6, equal_nan=True
        )


def test_maul_properties_wind_below_4d_realization(
    maul_mask_member,
    u_wind_maul_member,
    v_wind_maul_member,
    precalc_wind_below_maul_4d_realization,
):
    """Ensure correct wind below MAUL generated for 4D field with varying realization."""
    assert np.allclose(
        precipitation.MAUL_properties(
            maul_mask_member,
            u_wind_maul_member,
            v_wind_maul_member,
            output="wind_below",
        ).data,
        precalc_wind_below_maul_4d_realization.data,
        rtol=1e-2,
        atol=1e-6,
        equal_nan=True,
    )


def test_maul_properties_wind_below_4d_time(
    maul_mask_time,
    u_wind_maul_time,
    v_wind_maul_time,
    precalc_wind_below_maul_4d_time,
):
    """Ensure correct wind below MAUL generated for 4D field with varying time."""
    assert np.allclose(
        precipitation.MAUL_properties(
            maul_mask_time, u_wind_maul_time, v_wind_maul_time, output="wind_below"
        ).data,
        precalc_wind_below_maul_4d_time.data,
        rtol=1e-2,
        atol=1e-6,
        equal_nan=True,
    )


def test_maul_properties_wind_below_5d(
    maul_mask_all, u_wind_maul_all, v_wind_maul_all, precalc_wind_below_maul_5d
):
    """Ensure correct wind below MAUL generated for 5D field."""
    assert np.allclose(
        precipitation.MAUL_properties(
            maul_mask_all, u_wind_maul_all, v_wind_maul_all, output="wind_below"
        ).data,
        precalc_wind_below_maul_5d.data,
        rtol=1e-2,
        atol=1e-6,
        equal_nan=True,
    )
