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

"""Test pressure operators."""

import cf_units
import iris.cube
import numpy as np

from CSET.operators import pressure


def test_vapour_pressure(temperature_for_conversions_cube):
    """Test calculation of vapour pressure for a cube."""
    expected_data = temperature_for_conversions_cube.copy()
    exponent = (
        17.27
        * (temperature_for_conversions_cube - 273.16)
        / (temperature_for_conversions_cube - 35.86)
    )
    expected_data.data = 6.1078 * np.exp(exponent.core_data())
    assert np.allclose(
        expected_data.data,
        pressure.vapour_pressure(temperature_for_conversions_cube).data,
        rtol=1e-6,
        atol=1e-2,
    )


def test_vapour_pressure_name(temperature_for_conversions_cube):
    """Test renaming of vapour pressure cube."""
    expected_name = "vapour_pressure"
    assert (
        expected_name
        == pressure.vapour_pressure(temperature_for_conversions_cube).name()
    )


def test_vapour_pressure_units(temperature_for_conversions_cube):
    """Test units for vapour pressure cube."""
    expected_units = cf_units.Unit("hPa")
    assert (
        expected_units
        == pressure.vapour_pressure(temperature_for_conversions_cube).units
    )


def test_vapour_pressure_cube_list(temperature_for_conversions_cube):
    """Test calculation of vapour pressure for a CubeList."""
    expected_data = temperature_for_conversions_cube.copy()
    exponent = (
        17.27
        * (temperature_for_conversions_cube - 273.16)
        / (temperature_for_conversions_cube - 35.86)
    )
    expected_data.data = 6.1078 * np.exp(exponent.core_data())
    expected_list = iris.cube.CubeList([expected_data, expected_data])
    input_cubelist = iris.cube.CubeList(
        [temperature_for_conversions_cube, temperature_for_conversions_cube]
    )
    actual_cubelist = pressure.vapour_pressure(input_cubelist)
    for cube_a, cube_b in zip(expected_list, actual_cubelist, strict=True):
        assert np.allclose(cube_a.data, cube_b.data, rtol=1e-6, atol=1e-2)


def test_relative_humidity_to_vapour_pressure(
    temperature_for_conversions_cube, relative_humidity_for_conversions_cube
):
    """Test calculation of vapour pressure from relative humidity."""
    expected_data = pressure.vapour_pressure(temperature_for_conversions_cube) * (
        relative_humidity_for_conversions_cube / 100.0
    )
    assert np.allclose(
        expected_data.data,
        pressure.relative_humidity_to_vapour_pressure(
            temperature_for_conversions_cube, relative_humidity_for_conversions_cube
        ).data,
        rtol=1e-6,
        atol=1e-2,
    )


def test_relative_humidity_to_vapour_pressure_name(
    temperature_for_conversions_cube, relative_humidity_for_conversions_cube
):
    """Test naming of vapour pressure cube."""
    expected_name = "vapour_pressure"
    assert (
        expected_name
        == pressure.relative_humidity_to_vapour_pressure(
            temperature_for_conversions_cube, relative_humidity_for_conversions_cube
        ).name()
    )


def test_relative_humidity_to_vapour_pressure_units(
    temperature_for_conversions_cube, relative_humidity_for_conversions_cube
):
    """Test units of vapour pressure cube."""
    expected_units = cf_units.Unit("hPa")
    assert (
        expected_units
        == pressure.relative_humidity_to_vapour_pressure(
            temperature_for_conversions_cube, relative_humidity_for_conversions_cube
        ).units
    )


def test_relative_humidity_to_vapour_pressure_cubelist(
    temperature_for_conversions_cube, relative_humidity_for_conversions_cube
):
    """Test calculation of vapour pressure from relative humidity as a CubeList."""
    expected_data = pressure.vapour_pressure(temperature_for_conversions_cube) * (
        relative_humidity_for_conversions_cube / 100.0
    )
    expected_list = iris.cube.CubeList([expected_data, expected_data])
    temperature_input_list = iris.cube.CubeList(
        [temperature_for_conversions_cube, temperature_for_conversions_cube]
    )
    relative_humidity_input_list = iris.cube.CubeList(
        [relative_humidity_for_conversions_cube, relative_humidity_for_conversions_cube]
    )
    actual_cubelist = pressure.relative_humidity_to_vapour_pressure(
        temperature_input_list, relative_humidity_input_list
    )
    for cube_a, cube_b in zip(expected_list, actual_cubelist, strict=True):
        assert np.allclose(cube_a.data, cube_b.data, rtol=1e-6, atol=1e-2)
