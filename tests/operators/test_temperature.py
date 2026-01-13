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

"""Test temperature operators."""

import cf_units
import iris.cube
import numpy as np

from CSET.operators import _atmospheric_constants, misc, pressure, temperature


def test_dewpoint_temperature(
    temperature_for_conversions_cube, relative_humidity_for_conversions_cube
):
    """Test calculation of dewpoint temperature."""
    vp = pressure.vapour_pressure_from_relative_humidity(
        temperature_for_conversions_cube, relative_humidity_for_conversions_cube
    )
    expected_data = vp.copy()
    expected_data.data = (243.5 * np.log(vp.core_data()) - 440.8) / (
        19.48 - np.log(vp.core_data())
    )
    expected_data.data[
        temperature_for_conversions_cube.data - _atmospheric_constants.T0 < -35.0
    ] = np.nan
    expected_data.data[
        temperature_for_conversions_cube.data - _atmospheric_constants.T0 > 35.0
    ] = np.nan
    expected_data.units = "Celsius"
    expected_data = misc.convert_units(expected_data, "K")
    assert np.allclose(
        expected_data.data,
        temperature.dewpoint_temperature(
            temperature_for_conversions_cube, relative_humidity_for_conversions_cube
        ).data,
        rtol=1e-6,
        atol=1e-2,
    )


def test_dewpoint_temperature_name(
    temperature_for_conversions_cube, relative_humidity_for_conversions_cube
):
    """Test name of dewpoint temperature cube."""
    expected_name = "dewpoint_temperature"
    assert (
        expected_name
        == temperature.dewpoint_temperature(
            temperature_for_conversions_cube, relative_humidity_for_conversions_cube
        ).name()
    )


def test_dewpoint_temperature_unit(
    temperature_for_conversions_cube, relative_humidity_for_conversions_cube
):
    """Test units for dewpoint temperature cube."""
    expected_units = cf_units.Unit("K")
    assert (
        expected_units
        == temperature.dewpoint_temperature(
            temperature_for_conversions_cube, relative_humidity_for_conversions_cube
        ).units
    )


def test_dewpoint_temperature_cubelist(
    temperature_for_conversions_cube, relative_humidity_for_conversions_cube
):
    """Test calculation of dewpoint temperature for a CubeList."""
    vp = pressure.vapour_pressure_from_relative_humidity(
        temperature_for_conversions_cube, relative_humidity_for_conversions_cube
    )
    expected_data = vp.copy()
    expected_data.data = (243.5 * np.log(vp.core_data()) - 440.8) / (
        19.48 - np.log(vp.core_data())
    )
    expected_data.data[
        temperature_for_conversions_cube.data - _atmospheric_constants.T0 < -35.0
    ] = np.nan
    expected_data.data[
        temperature_for_conversions_cube.data - _atmospheric_constants.T0 > 35.0
    ] = np.nan
    expected_data.units = "Celsius"
    expected_data = misc.convert_units(expected_data, "K")
    expected_list = iris.cube.CubeList([expected_data, expected_data])
    temperature_list = iris.cube.CubeList(
        [temperature_for_conversions_cube, temperature_for_conversions_cube]
    )
    rh_list = iris.cube.CubeList(
        [relative_humidity_for_conversions_cube, relative_humidity_for_conversions_cube]
    )
    actual_cubelist = temperature.dewpoint_temperature(temperature_list, rh_list)
    for cube_a, cube_b in zip(expected_list, actual_cubelist, strict=True):
        assert np.allclose(cube_a.data, cube_b.data, rtol=1e-6, atol=1e-2)


def test_virtual_temperature(
    temperature_for_conversions_cube, mixing_ratio_for_conversions_cube
):
    """Test to calculate virtual temperature."""
    expected_data = temperature_for_conversions_cube * (
        (mixing_ratio_for_conversions_cube + _atmospheric_constants.EPSILON)
        / (_atmospheric_constants.EPSILON * (1 + mixing_ratio_for_conversions_cube))
    )
    assert np.allclose(
        expected_data.data,
        temperature.virtual_temperature(
            temperature_for_conversions_cube, mixing_ratio_for_conversions_cube
        ).data,
        rtol=1e-6,
        atol=1e-2,
    )


def test_virtual_temperature_name(
    temperature_for_conversions_cube, mixing_ratio_for_conversions_cube
):
    """Test name of virtual temperature cube."""
    expected_name = "virtual_temperature"
    assert (
        expected_name
        == temperature.virtual_temperature(
            temperature_for_conversions_cube, mixing_ratio_for_conversions_cube
        ).name()
    )


def test_virtual_temperature_units(
    temperature_for_conversions_cube, mixing_ratio_for_conversions_cube
):
    """Test units of virtual temperature cube."""
    expected_units = cf_units.Unit("K")
    assert (
        expected_units
        == temperature.virtual_temperature(
            temperature_for_conversions_cube, mixing_ratio_for_conversions_cube
        ).units
    )


def test_virtual_temperature_cubelist(
    temperature_for_conversions_cube, mixing_ratio_for_conversions_cube
):
    """Test to calculate virtual temperature for a CubeList."""
    expected_data = temperature_for_conversions_cube * (
        (mixing_ratio_for_conversions_cube + _atmospheric_constants.EPSILON)
        / (_atmospheric_constants.EPSILON * (1 + mixing_ratio_for_conversions_cube))
    )
    expected_list = iris.cube.CubeList([expected_data, expected_data])
    temperature_list = iris.cube.CubeList(
        [temperature_for_conversions_cube, temperature_for_conversions_cube]
    )
    mixing_ratio_list = iris.cube.CubeList(
        [mixing_ratio_for_conversions_cube, mixing_ratio_for_conversions_cube]
    )
    actual_cubelist = temperature.virtual_temperature(
        temperature_list, mixing_ratio_list
    )
    for cube_a, cube_b in zip(expected_list, actual_cubelist, strict=True):
        assert np.allclose(cube_a.data, cube_b.data, rtol=1e-6, atol=1e-2)


def test_wet_bulb_temperature(
    temperature_for_conversions_cube, relative_humidity_for_conversions_cube
):
    """Test to calculate wet-bulb temperature."""
    T_units = misc.convert_units(temperature_for_conversions_cube, "Celsius")
    RH_units = misc.convert_units(relative_humidity_for_conversions_cube, "%")
    TW = (
        T_units * np.arctan(0.151977 * (RH_units.core_data() + 8.313659) ** 0.5)
        + np.arctan(T_units.core_data() + RH_units.core_data())
        - np.arctan(RH_units.core_data() - 1.676331)
        + 0.00391838
        * (RH_units.core_data()) ** (3.0 / 2.0)
        * np.arctan(0.023101 * RH_units.core_data())
        - 4.686035
    )
    TW = misc.convert_units(TW, "K")
    assert np.allclose(
        TW.data,
        temperature.wet_bulb_temperature(
            temperature_for_conversions_cube, relative_humidity_for_conversions_cube
        ).data,
        rtol=1e-6,
        atol=1e-2,
    )


def test_wet_bulb_temperature_units(
    temperature_for_conversions_cube, relative_humidity_for_conversions_cube
):
    """Test units for wet bulb temperature cube."""
    expected_units = cf_units.Unit("K")
    assert (
        expected_units
        == temperature.wet_bulb_temperature(
            temperature_for_conversions_cube, relative_humidity_for_conversions_cube
        ).units
    )


def test_wet_bulb_temperature_name(
    temperature_for_conversions_cube, relative_humidity_for_conversions_cube
):
    """Test name for wet bulb temperature cube."""
    expected_name = "wet_bulb_temperature"
    assert (
        expected_name
        == temperature.wet_bulb_temperature(
            temperature_for_conversions_cube, relative_humidity_for_conversions_cube
        ).name()
    )


def test_wet_bulb_temperature_cubelist(
    temperature_for_conversions_cube, relative_humidity_for_conversions_cube
):
    """Test to calculate wet-bulb temperature for a CubeList."""
    T_units = misc.convert_units(temperature_for_conversions_cube, "Celsius")
    RH_units = misc.convert_units(relative_humidity_for_conversions_cube, "%")
    TW = (
        T_units * np.arctan(0.151977 * (RH_units.core_data() + 8.313659) ** 0.5)
        + np.arctan(T_units.core_data() + RH_units.core_data())
        - np.arctan(RH_units.core_data() - 1.676331)
        + 0.00391838
        * (RH_units.core_data()) ** (3.0 / 2.0)
        * np.arctan(0.023101 * RH_units.core_data())
        - 4.686035
    )
    TW = misc.convert_units(TW, "K")
    expected_list = iris.cube.CubeList([TW, TW])
    temperature_list = iris.cube.CubeList(
        [temperature_for_conversions_cube, temperature_for_conversions_cube]
    )
    rh_list = iris.cube.CubeList(
        [relative_humidity_for_conversions_cube, relative_humidity_for_conversions_cube]
    )
    actual_cubelist = temperature.wet_bulb_temperature(temperature_list, rh_list)
    for cube_a, cube_b in zip(expected_list, actual_cubelist, strict=True):
        assert np.allclose(cube_a.data, cube_b.data, rtol=1e-6, atol=1e-2)
