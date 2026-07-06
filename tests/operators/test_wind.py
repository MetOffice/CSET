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

"""Test wind operators."""

import cf_units
import iris.cube
import numpy as np
import pytest

from CSET.operators import read, wind


# read and pytest fixture is temporary until CFAD code loaded so can ensure tests work.
@pytest.fixture()
def xwind() -> iris.cube.Cube:
    """Get regridded xwind to run tests on."""
    return read.read_cube("tests/test_data/ageofair/aoa_in_rgd.nc", "x_wind")


def test_convert_to_beaufort_scale(xwind):
    """Test for converting a cube from m/s to the Beaufort scale."""
    # Calculate the windspeed on the Beaufort Scale
    xwind_expected = xwind.copy()
    xwind_expected /= 0.836
    xwind_expected.data **= 2.0 / 3.0
    xwind_expected.data = np.round(xwind_expected.data)
    assert np.allclose(
        xwind_expected.data,
        wind.convert_to_beaufort_scale(xwind).data,
        rtol=1e-06,
        atol=1e-02,
    )


def test_convert_to_beaufort_scale_cubelist(xwind):
    """Test for converting a cube list from m/s to the Beaufort scale."""
    # Calculate the windspeed on the Beaufort Scale.
    xwind_expected = xwind.copy()
    xwind_expected /= 0.836
    xwind_expected.data **= 2.0 / 3.0
    xwind_expected.data = np.round(xwind_expected.data)
    # Create a cubelist of the xwind cube.
    xwind_cube_list = iris.cube.CubeList([xwind, xwind])
    # Create an expected cubelist.
    expected_cubelist = iris.cube.CubeList([xwind_expected, xwind_expected])
    # Calculate the beaufort scale using the function as a cubelist.
    calculated_cubelist = wind.convert_to_beaufort_scale(xwind_cube_list)
    # Assert data in cubes within the cubelists are identical.
    for cube_a, cube_b in zip(expected_cubelist, calculated_cubelist, strict=True):
        assert np.allclose(cube_a.data, cube_b.data, rtol=1e-06, atol=1e-02)


def test_convert_to_beaufort_scale_name(xwind):
    """Test naming of new beaufort scale wind."""
    expected_name = f"{xwind.name()}_on_Beaufort_Scale"
    assert expected_name == wind.convert_to_beaufort_scale(xwind).name()


def test_convert_to_beaufort_scale_units(xwind):
    """Test unit conversion of beaufort scale cube."""
    expected_unit = cf_units.Unit("1")
    assert expected_unit == wind.convert_to_beaufort_scale(xwind).units


def _make_cube(data, units="m s-1"):
    """Make a tiny u,v cube from data."""
    data = np.asarray(data)
    # Your operator expects y/x coords, so keep tests 2D (lat, lon).
    if data.ndim != 2:
        raise ValueError(
            f"Expected 2D (lat, lon) data for test cube, got shape {data.shape}."
        )

    ny, nx = data.shape
    lat = iris.coords.DimCoord(np.arange(ny), standard_name="latitude", units="degrees")
    lon = iris.coords.DimCoord(
        np.arange(nx), standard_name="longitude", units="degrees"
    )

    return iris.cube.Cube(
        data,
        dim_coords_and_dims=[(lat, 0), (lon, 1)],
        units=units,
    )


def test_vector_wind():
    """Test wind speed operator."""
    u = _make_cube([[3.0, 0.0], [0.0, -3.0]])
    v = _make_cube([[4.0, 0.0], [0.0, 4.0]])

    out = wind.calculate_vector_wind(u, v)
    speed, direction = out
    # Speed.
    expected_speed = np.hypot(u.data, v.data)
    assert np.allclose(speed.data, expected_speed)
    # Direction.
    expected_direction = (np.degrees(np.arctan2(-u.data, -v.data)) + 360) % 360
    assert np.allclose(direction.data, expected_direction)


def test_vector_wind_directions():
    """Test wind direction operator."""
    u = _make_cube([[0, -1, 0, 1]])
    v = _make_cube([[-1, 0, 1, 0]])
    out = wind.calculate_vector_wind(u, v)
    _, direction = out

    expected = np.array([[0, 90, 180, 270]])
    assert np.allclose(direction.data, expected)


def test_vector_wind_cubelist():
    """Test wind operator with cubelist."""
    u_list = iris.cube.CubeList([_make_cube([[1, 1]]), _make_cube([[2, 2]])])
    v_list = iris.cube.CubeList([_make_cube([[0, 0]]), _make_cube([[0, 0]])])
    out = wind.calculate_vector_wind(u_list, v_list)
    # 2 input pairs → 4 output cubes.
    assert len(out) == 4


def test_vector_wind_mismatched_lengths():
    """Test wind operator with mismatched lengths."""
    u_list = iris.cube.CubeList([_make_cube([[1]])])
    v_list = iris.cube.CubeList([_make_cube([[1]]), _make_cube([[2]])])
    with pytest.raises(ValueError):
        wind.calculate_vector_wind(u_list, v_list)


def test_vector_wind_metadata():
    """Test wind operator with metadata."""
    u = _make_cube([[1]])
    v = _make_cube([[1]])

    out = wind.calculate_vector_wind(u, v)
    speed, direction = out
    assert speed.name() == "wind_speed"
    assert direction.name() == "wind_from_direction"
    assert direction.units == "degrees"
    assert direction.standard_name == "wind_from_direction"


def test_vector_wind_zero_wind():
    """Test wind operator with zero wind."""
    u = _make_cube([[0]])
    v = _make_cube([[0]])

    _, direction = wind.calculate_vector_wind(u, v)
    # Direction is undefined, but your formula gives 180 deg.
    assert np.isfinite(direction.data)
