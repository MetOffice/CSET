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

"""Test humidity operators."""

import cf_units
import iris.cube
import numpy as np

from CSET.operators import _atmospheric_constants, humidity, misc, pressure


def test_mixing_ratio_from_specific_humidity(specific_humidity_for_conversions_cube):
    """Test calculation of mixing ratio from specific humidity."""
    expected_data = specific_humidity_for_conversions_cube / (
        1 - specific_humidity_for_conversions_cube
    )
    assert np.allclose(
        expected_data.data,
        humidity.mixing_ratio_from_specific_humidity(
            specific_humidity_for_conversions_cube
        ).data,
        rtol=1e-6,
        atol=1e-2,
    )


def test_mixing_ratio_from_specific_humidity_name(
    specific_humidity_for_conversions_cube,
):
    """Test naming of mixing ratio cube."""
    expected_name = "mixing_ratio"
    assert (
        expected_name
        == humidity.mixing_ratio_from_specific_humidity(
            specific_humidity_for_conversions_cube
        ).name()
    )


def test_mixing_ratio_from_specific_humidity_unit(
    specific_humidity_for_conversions_cube,
):
    """Test units for mixing ratio."""
    expected_units = cf_units.Unit("kg/kg")
    assert (
        expected_units
        == humidity.mixing_ratio_from_specific_humidity(
            specific_humidity_for_conversions_cube
        ).units
    )


def test_mixing_ratio_from_specific_humidity_cubelist(
    specific_humidity_for_conversions_cube,
):
    """Test calculation of mixing ratio from specific humidity for a CubeList."""
    expected_data = specific_humidity_for_conversions_cube / (
        1 - specific_humidity_for_conversions_cube
    )
    expected_list = iris.cube.CubeList([expected_data, expected_data])
    input_list = iris.cube.CubeList(
        [specific_humidity_for_conversions_cube, specific_humidity_for_conversions_cube]
    )
    actual_cubelist = humidity.mixing_ratio_from_specific_humidity(input_list)
    for cube_a, cube_b in zip(expected_list, actual_cubelist, strict=True):
        assert np.allclose(cube_a.data, cube_b.data, rtol=1e-6, atol=1e-2)


def test_mixing_ratio_from_specific_humidity_using_calculated(
    mixing_ratio_for_conversions_cube,
):
    """Test mixing ratio calculation using calculated q from mixing ratio."""
    calculated_w = humidity.mixing_ratio_from_specific_humidity(
        humidity.specific_humidity_from_mixing_ratio(mixing_ratio_for_conversions_cube)
    )
    assert np.allclose(
        mixing_ratio_for_conversions_cube.data, calculated_w.data, rtol=1e-6, atol=1e-2
    )


def test_specific_humidity_from_mixing_ratio(mixing_ratio_for_conversions_cube):
    """Test specific humidity calculation from mixing ratio."""
    expected_data = mixing_ratio_for_conversions_cube / (
        1 + mixing_ratio_for_conversions_cube
    )
    assert np.allclose(
        expected_data.data,
        humidity.specific_humidity_from_mixing_ratio(
            mixing_ratio_for_conversions_cube
        ).data,
        rtol=1e-6,
        atol=1e-2,
    )


def test_specific_humidity_from_mixing_ratio_name(mixing_ratio_for_conversions_cube):
    """Test specific humidity cube is named."""
    expected_name = "specific_humidity"
    assert (
        expected_name
        == humidity.specific_humidity_from_mixing_ratio(
            mixing_ratio_for_conversions_cube
        ).name()
    )


def test_specific_humidity_from_mixing_ratio_units(mixing_ratio_for_conversions_cube):
    """Test units of specific humidity."""
    expected_units = cf_units.Unit("kg/kg")
    assert (
        expected_units
        == humidity.specific_humidity_from_mixing_ratio(
            mixing_ratio_for_conversions_cube
        ).units
    )


def test_specific_humidity_from_mixing_ratio_cubelist(
    mixing_ratio_for_conversions_cube,
):
    """Test specific humidity calculation from mixing ratio with a CuebList."""
    expected_data = mixing_ratio_for_conversions_cube / (
        1 + mixing_ratio_for_conversions_cube
    )
    expected_list = iris.cube.CubeList([expected_data, expected_data])
    input_list = iris.cube.CubeList(
        [mixing_ratio_for_conversions_cube, mixing_ratio_for_conversions_cube]
    )
    actual_cubelist = humidity.specific_humidity_from_mixing_ratio(input_list)
    for cube_a, cube_b in zip(expected_list, actual_cubelist, strict=True):
        assert np.allclose(cube_a.data, cube_b.data, rtol=1e-6, atol=1e-2)


def test_specific_humidity_from_mixing_ratio_using_calculated(
    specific_humidity_for_conversions_cube,
):
    """Test specific humidity calculation using calculated w from specific humidity."""
    calculated_q = humidity.specific_humidity_from_mixing_ratio(
        humidity.mixing_ratio_from_specific_humidity(
            specific_humidity_for_conversions_cube
        )
    )
    assert np.allclose(
        specific_humidity_for_conversions_cube.data,
        calculated_q.data,
        rtol=1e-6,
        atol=1e-2,
    )


def test_saturation_mixing_ratio(
    temperature_for_conversions_cube, pressure_for_conversions_cube
):
    """Test calculation of saturation mixing ratio."""
    expected_data = (
        _atmospheric_constants.EPSILON
        * pressure.vapour_pressure(temperature_for_conversions_cube)
    ) / (
        (misc.convert_units(pressure_for_conversions_cube, "hPa"))
        - pressure.vapour_pressure(temperature_for_conversions_cube)
    )
    assert np.allclose(
        expected_data.data,
        humidity.saturation_mixing_ratio(
            temperature_for_conversions_cube, pressure_for_conversions_cube
        ).data,
        rtol=1e-6,
        atol=1e-2,
    )


def test_saturation_mixing_ratio_name(
    temperature_for_conversions_cube, pressure_for_conversions_cube
):
    """Test naming of saturation mixing ratio cube."""
    expected_name = "saturation_mixing_ratio"
    assert (
        expected_name
        == humidity.saturation_mixing_ratio(
            temperature_for_conversions_cube, pressure_for_conversions_cube
        ).name()
    )


def test_saturation_mixing_ratio_units(
    temperature_for_conversions_cube, pressure_for_conversions_cube
):
    """Test units of saturation mixing ratio cube."""
    expected_units = cf_units.Unit("kg/kg")
    assert (
        expected_units
        == humidity.saturation_mixing_ratio(
            temperature_for_conversions_cube, pressure_for_conversions_cube
        ).units
    )


def test_saturation_mixing_ratio_cubelist(
    temperature_for_conversions_cube, pressure_for_conversions_cube
):
    """Test calculation of saturation mixing ratio as CubeList."""
    expected_data = (
        _atmospheric_constants.EPSILON
        * pressure.vapour_pressure(temperature_for_conversions_cube)
    ) / (
        (misc.convert_units(pressure_for_conversions_cube, "hPa"))
        - pressure.vapour_pressure(temperature_for_conversions_cube)
    )
    expected_list = iris.cube.CubeList([expected_data, expected_data])
    temperature_list = iris.cube.CubeList(
        [temperature_for_conversions_cube, temperature_for_conversions_cube]
    )
    pressure_list = iris.cube.CubeList(
        [pressure_for_conversions_cube, pressure_for_conversions_cube]
    )
    actual_cubelist = humidity.saturation_mixing_ratio(temperature_list, pressure_list)
    for cube_a, cube_b in zip(expected_list, actual_cubelist, strict=True):
        assert np.allclose(cube_a.data, cube_b.data, rtol=1e-6, atol=1e-2)


def test_saturation_specific_humidity(
    temperature_for_conversions_cube, pressure_for_conversions_cube
):
    """Test calculation of saturation specific humidity."""
    expected_data = (
        _atmospheric_constants.EPSILON
        * pressure.vapour_pressure(temperature_for_conversions_cube)
    ) / misc.convert_units(pressure_for_conversions_cube, "hPa")
    assert np.allclose(
        expected_data.data,
        humidity.saturation_specific_humidity(
            temperature_for_conversions_cube, pressure_for_conversions_cube
        ).data,
        rtol=1e-6,
        atol=1e-2,
    )


def test_saturation_specific_humidity_name(
    temperature_for_conversions_cube, pressure_for_conversions_cube
):
    """Test naming of saturation specific humidity cube."""
    expected_name = "saturation_specific_humidity"
    assert (
        expected_name
        == humidity.saturation_specific_humidity(
            temperature_for_conversions_cube, pressure_for_conversions_cube
        ).name()
    )


def test_saturation_specific_humidity_units(
    temperature_for_conversions_cube, pressure_for_conversions_cube
):
    """Test units of saturation specific humidity."""
    expected_units = cf_units.Unit("kg/kg")
    assert (
        expected_units
        == humidity.saturation_specific_humidity(
            temperature_for_conversions_cube, pressure_for_conversions_cube
        ).units
    )


def test_saturation_specific_humidity_cubelist(
    temperature_for_conversions_cube, pressure_for_conversions_cube
):
    """Test calculation of saturation specific humidity for a CubeList."""
    expected_data = (
        _atmospheric_constants.EPSILON
        * pressure.vapour_pressure(temperature_for_conversions_cube)
    ) / misc.convert_units(pressure_for_conversions_cube, "hPa")
    expected_list = iris.cube.CubeList([expected_data, expected_data])
    temperature_list = iris.cube.CubeList(
        [temperature_for_conversions_cube, temperature_for_conversions_cube]
    )
    pressure_list = iris.cube.CubeList(
        [pressure_for_conversions_cube, pressure_for_conversions_cube]
    )
    actual_cubelist = humidity.saturation_specific_humidity(
        temperature_list, pressure_list
    )
    for cube_a, cube_b in zip(expected_list, actual_cubelist, strict=True):
        assert np.allclose(cube_a.data, cube_b.data, rtol=1e-6, atol=1e-2)
