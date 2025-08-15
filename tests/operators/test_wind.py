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
    expected_name = "wind_speed_on_Beaufort_Scale"
    assert expected_name == wind.convert_to_beaufort_scale(xwind).name()


def test_convert_to_beaufort_scale_units(xwind):
    """Test unit conversion of beaufort scale cube."""
    expected_unit = cf_units.Unit("1")
    assert expected_unit == wind.convert_to_beaufort_scale(xwind).units
