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


def test_mixing_ratio_from_relative_humidity(
    temperature_for_conversions_cube,
    pressure_for_conversions_cube,
    relative_humidity_for_conversions_cube,
):
    """Test calculation of mixing ratio from relative humidity."""
    expected_data = humidity.saturation_mixing_ratio(
        temperature_for_conversions_cube, pressure_for_conversions_cube
    ) * misc.convert_units(relative_humidity_for_conversions_cube, "1")
    assert np.allclose(
        expected_data.data,
        humidity.mixing_ratio_from_relative_humidity(
            temperature_for_conversions_cube,
            pressure_for_conversions_cube,
            relative_humidity_for_conversions_cube,
        ).data,
        rtol=1e-6,
        atol=1e-2,
    )


def test_mixing_ratio_from_relative_humidity_name(
    temperature_for_conversions_cube,
    pressure_for_conversions_cube,
    relative_humidity_for_conversions_cube,
):
    """Test naming of mixing ratio cube."""
    expected_name = "mixing_ratio"
    assert (
        expected_name
        == humidity.mixing_ratio_from_relative_humidity(
            temperature_for_conversions_cube,
            pressure_for_conversions_cube,
            relative_humidity_for_conversions_cube,
        ).name()
    )


def test_mixing_ratio_from_relative_humidity_units(
    temperature_for_conversions_cube,
    pressure_for_conversions_cube,
    relative_humidity_for_conversions_cube,
):
    """Test units of mixing ratio cube."""
    expected_units = cf_units.Unit("kg/kg")
    assert (
        expected_units
        == humidity.mixing_ratio_from_relative_humidity(
            temperature_for_conversions_cube,
            pressure_for_conversions_cube,
            relative_humidity_for_conversions_cube,
        ).units
    )


def test_mixing_ratio_from_relative_humidity_cubelist(
    temperature_for_conversions_cube,
    pressure_for_conversions_cube,
    relative_humidity_for_conversions_cube,
):
    """Test calculation of mixing ratio from relative humidity for a CubeList."""
    expected_data = humidity.saturation_mixing_ratio(
        temperature_for_conversions_cube, pressure_for_conversions_cube
    ) * misc.convert_units(relative_humidity_for_conversions_cube, "1")
    expected_list = iris.cube.CubeList([expected_data, expected_data])
    temperature_list = iris.cube.CubeList(
        [temperature_for_conversions_cube, temperature_for_conversions_cube]
    )
    pressure_list = iris.cube.CubeList(
        [pressure_for_conversions_cube, pressure_for_conversions_cube]
    )
    rh_list = iris.cube.CubeList(
        [relative_humidity_for_conversions_cube, relative_humidity_for_conversions_cube]
    )
    actual_cubelist = humidity.mixing_ratio_from_relative_humidity(
        temperature_list, pressure_list, rh_list
    )
    for cube_a, cube_b in zip(expected_list, actual_cubelist, strict=True):
        assert np.allclose(cube_a.data, cube_b.data, rtol=1e-6, atol=1e-2)


def test_mixing_ratio_from_relative_humidity_calculated(
    temperature_for_conversions_cube,
    pressure_for_conversions_cube,
    mixing_ratio_for_conversions_cube,
):
    """Test mixing ratio from relative humidity using calculated relative humidity."""
    calculated_w = humidity.mixing_ratio_from_relative_humidity(
        temperature_for_conversions_cube,
        pressure_for_conversions_cube,
        humidity.relative_humidity_from_mixing_ratio(
            mixing_ratio_for_conversions_cube,
            temperature_for_conversions_cube,
            pressure_for_conversions_cube,
        ),
    )
    assert np.allclose(
        calculated_w.data,
        mixing_ratio_for_conversions_cube.data,
        rtol=1e-6,
        atol=1e-2,
    )


def test_specific_humidity_from_relative_humidity(
    temperature_for_conversions_cube,
    pressure_for_conversions_cube,
    relative_humidity_for_conversions_cube,
):
    """Test calculation of specific humidity from relative humidity."""
    expected_data = humidity.saturation_specific_humidity(
        temperature_for_conversions_cube, pressure_for_conversions_cube
    ) * misc.convert_units(relative_humidity_for_conversions_cube, "1")
    assert np.allclose(
        expected_data.data,
        humidity.specific_humidity_from_relative_humidity(
            temperature_for_conversions_cube,
            pressure_for_conversions_cube,
            relative_humidity_for_conversions_cube,
        ).data,
        rtol=1e-6,
        atol=1e-2,
    )


def test_specific_humidity_from_relative_humidity_name(
    temperature_for_conversions_cube,
    pressure_for_conversions_cube,
    relative_humidity_for_conversions_cube,
):
    """Test naming of specific humidity cube."""
    expected_name = "specific_humidity"
    assert (
        expected_name
        == humidity.specific_humidity_from_relative_humidity(
            temperature_for_conversions_cube,
            pressure_for_conversions_cube,
            relative_humidity_for_conversions_cube,
        ).name()
    )


def test_specific_humidity_from_relative_humidity_units(
    temperature_for_conversions_cube,
    pressure_for_conversions_cube,
    relative_humidity_for_conversions_cube,
):
    """Test units of specific humidity cube."""
    expected_units = cf_units.Unit("kg/kg")
    assert (
        expected_units
        == humidity.specific_humidity_from_relative_humidity(
            temperature_for_conversions_cube,
            pressure_for_conversions_cube,
            relative_humidity_for_conversions_cube,
        ).units
    )


def test_specific_humidity_from_relative_humidity_cubelist(
    temperature_for_conversions_cube,
    pressure_for_conversions_cube,
    relative_humidity_for_conversions_cube,
):
    """Test calculation of specific humidity from relative humidity for a CubeList."""
    expected_data = humidity.saturation_specific_humidity(
        temperature_for_conversions_cube, pressure_for_conversions_cube
    ) * misc.convert_units(relative_humidity_for_conversions_cube, "1")
    expected_list = iris.cube.CubeList([expected_data, expected_data])
    temperature_list = iris.cube.CubeList(
        [temperature_for_conversions_cube, temperature_for_conversions_cube]
    )
    pressure_list = iris.cube.CubeList(
        [pressure_for_conversions_cube, pressure_for_conversions_cube]
    )
    rh_list = iris.cube.CubeList(
        [relative_humidity_for_conversions_cube, relative_humidity_for_conversions_cube]
    )
    actual_cubelist = humidity.specific_humidity_from_relative_humidity(
        temperature_list, pressure_list, rh_list
    )
    for cube_a, cube_b in zip(expected_list, actual_cubelist, strict=True):
        assert np.allclose(cube_a.data, cube_b.data, rtol=1e-6, atol=1e-2)


def test_specific_humidity_from_relative_humidity_calculated(
    temperature_for_conversions_cube,
    pressure_for_conversions_cube,
    specific_humidity_for_conversions_cube,
):
    """Test specific humidity from relative humidity using calculated relative humidity."""
    calculated_q = humidity.specific_humidity_from_relative_humidity(
        temperature_for_conversions_cube,
        pressure_for_conversions_cube,
        humidity.relative_humidity_from_specific_humidity(
            specific_humidity_for_conversions_cube,
            temperature_for_conversions_cube,
            pressure_for_conversions_cube,
        ),
    )
    assert np.allclose(
        calculated_q.data,
        specific_humidity_for_conversions_cube.data,
        rtol=1e-6,
        atol=1e-2,
    )


def test_relative_humidity_from_mixing_ratio(
    mixing_ratio_for_conversions_cube,
    temperature_for_conversions_cube,
    pressure_for_conversions_cube,
):
    """Test calculation of relative humidity from mixing ratio."""
    expected_data = 100.0 * (
        mixing_ratio_for_conversions_cube
        / humidity.saturation_mixing_ratio(
            temperature_for_conversions_cube, pressure_for_conversions_cube
        )
    )
    assert np.allclose(
        expected_data.data,
        humidity.relative_humidity_from_mixing_ratio(
            mixing_ratio_for_conversions_cube,
            temperature_for_conversions_cube,
            pressure_for_conversions_cube,
        ).data,
        rtol=1e-6,
        atol=1e-2,
    )


def test_relative_humidity_from_mixing_ratio_calculated(
    temperature_for_conversions_cube,
    pressure_for_conversions_cube,
    relative_humidity_for_conversions_cube,
):
    """Test relative humidity from mixing ratio using calculated mixing ratio."""
    calculated_rh = humidity.relative_humidity_from_mixing_ratio(
        humidity.mixing_ratio_from_relative_humidity(
            temperature_for_conversions_cube,
            pressure_for_conversions_cube,
            relative_humidity_for_conversions_cube,
        ),
        temperature_for_conversions_cube,
        pressure_for_conversions_cube,
    )
    assert np.allclose(
        calculated_rh.data,
        relative_humidity_for_conversions_cube.data,
        rtol=1e-6,
        atol=1e-2,
    )


def test_relative_humidity_from_mixing_ratio_name(
    mixing_ratio_for_conversions_cube,
    temperature_for_conversions_cube,
    pressure_for_conversions_cube,
):
    """Test name of relative humidity cube."""
    expected_name = "relative_humidity"
    assert (
        expected_name
        == humidity.relative_humidity_from_mixing_ratio(
            mixing_ratio_for_conversions_cube,
            temperature_for_conversions_cube,
            pressure_for_conversions_cube,
        ).name()
    )


def test_relative_humidity_from_mixing_ratio_units(
    mixing_ratio_for_conversions_cube,
    temperature_for_conversions_cube,
    pressure_for_conversions_cube,
):
    """Test units of relative humidity cube."""
    expected_units = cf_units.Unit("%")
    assert (
        expected_units
        == humidity.relative_humidity_from_mixing_ratio(
            mixing_ratio_for_conversions_cube,
            temperature_for_conversions_cube,
            pressure_for_conversions_cube,
        ).units
    )


def test_relative_humidity_from_mixing_ratio_cubelist(
    mixing_ratio_for_conversions_cube,
    temperature_for_conversions_cube,
    pressure_for_conversions_cube,
):
    """Test calculation of relative humidity from mixing ratio for a CubeList."""
    expected_data = 100.0 * (
        mixing_ratio_for_conversions_cube
        / humidity.saturation_mixing_ratio(
            temperature_for_conversions_cube, pressure_for_conversions_cube
        )
    )
    expected_list = iris.cube.CubeList([expected_data, expected_data])
    mixing_ratio_list = iris.cube.CubeList(
        [mixing_ratio_for_conversions_cube, mixing_ratio_for_conversions_cube]
    )
    temperature_list = iris.cube.CubeList(
        [temperature_for_conversions_cube, temperature_for_conversions_cube]
    )
    pressure_list = iris.cube.CubeList(
        [pressure_for_conversions_cube, pressure_for_conversions_cube]
    )
    actual_cubelist = humidity.relative_humidity_from_mixing_ratio(
        mixing_ratio_list, temperature_list, pressure_list
    )
    for cube_a, cube_b in zip(expected_list, actual_cubelist, strict=True):
        assert np.allclose(cube_a.data, cube_b.data, rtol=1e-6, atol=1e-2)


def test_relative_humidity_from_specific_humidity(
    specific_humidity_for_conversions_cube,
    temperature_for_conversions_cube,
    pressure_for_conversions_cube,
):
    """Test calculation of relative humidity from specific humidity."""
    expected_data = 100.0 * (
        specific_humidity_for_conversions_cube
        / humidity.saturation_specific_humidity(
            temperature_for_conversions_cube, pressure_for_conversions_cube
        )
    )
    assert np.allclose(
        expected_data.data,
        humidity.relative_humidity_from_specific_humidity(
            specific_humidity_for_conversions_cube,
            temperature_for_conversions_cube,
            pressure_for_conversions_cube,
        ).data,
        rtol=1e-6,
        atol=1e-2,
    )


def test_relative_humidity_from_specific_humidity_calculated(
    temperature_for_conversions_cube,
    pressure_for_conversions_cube,
    relative_humidity_for_conversions_cube,
):
    """Test relative humidity from specific humidity using calculated specific humidity."""
    calculated_rh = humidity.relative_humidity_from_specific_humidity(
        humidity.specific_humidity_from_relative_humidity(
            temperature_for_conversions_cube,
            pressure_for_conversions_cube,
            relative_humidity_for_conversions_cube,
        ),
        temperature_for_conversions_cube,
        pressure_for_conversions_cube,
    )
    assert np.allclose(
        calculated_rh.data,
        relative_humidity_for_conversions_cube.data,
        rtol=1e-6,
        atol=1e-2,
    )


def test_relative_humidity_from_specific_humidity_name(
    specific_humidity_for_conversions_cube,
    temperature_for_conversions_cube,
    pressure_for_conversions_cube,
):
    """Test name of relative humidity cube."""
    expected_name = "relative_humidity"
    assert (
        expected_name
        == humidity.relative_humidity_from_specific_humidity(
            specific_humidity_for_conversions_cube,
            temperature_for_conversions_cube,
            pressure_for_conversions_cube,
        ).name()
    )


def test_relative_humidity_from_specific_humidity_units(
    specific_humidity_for_conversions_cube,
    temperature_for_conversions_cube,
    pressure_for_conversions_cube,
):
    """Test units of relative humidity cube."""
    expected_units = cf_units.Unit("%")
    assert (
        expected_units
        == humidity.relative_humidity_from_specific_humidity(
            specific_humidity_for_conversions_cube,
            temperature_for_conversions_cube,
            pressure_for_conversions_cube,
        ).units
    )


def test_relative_humidity_from_specific_humidity_cubelist(
    specific_humidity_for_conversions_cube,
    temperature_for_conversions_cube,
    pressure_for_conversions_cube,
):
    """Test calculation of relative humidity from specific humidity for a CubeList."""
    expected_data = 100.0 * (
        specific_humidity_for_conversions_cube
        / humidity.saturation_specific_humidity(
            temperature_for_conversions_cube, pressure_for_conversions_cube
        )
    )
    expected_list = iris.cube.CubeList([expected_data, expected_data])
    specific_humidity_list = iris.cube.CubeList(
        [specific_humidity_for_conversions_cube, specific_humidity_for_conversions_cube]
    )
    temperature_list = iris.cube.CubeList(
        [temperature_for_conversions_cube, temperature_for_conversions_cube]
    )
    pressure_list = iris.cube.CubeList(
        [pressure_for_conversions_cube, pressure_for_conversions_cube]
    )
    actual_cubelist = humidity.relative_humidity_from_specific_humidity(
        specific_humidity_list, temperature_list, pressure_list
    )
    for cube_a, cube_b in zip(expected_list, actual_cubelist, strict=True):
        assert np.allclose(cube_a.data, cube_b.data, rtol=1e-6, atol=1e-2)


def test_precipitable_water(mr_3d, pw_3d):
    """Test calculation of precipitable water for 3D data."""
    assert np.allclose(
        pw_3d.data, humidity.precipitable_water(mr_3d).data, rtol=1e-6, atol=1e-2
    )


def test_precipitable_water_cubelist(mr_3d, pw_3d):
    """Test calculation of precipitable water in a cubelist."""
    input_cube = iris.cube.CubeList([mr_3d, mr_3d])
    actual_cubelist = humidity.precipitable_water(input_cube)
    expected_cubelist = iris.cube.CubeList([pw_3d, pw_3d])
    for cube_a, cube_b in zip(expected_cubelist, actual_cubelist, strict=True):
        assert np.allclose(cube_a.data, cube_b.data, rtol=1e-6, atol=1e-2)


def test_precipitable_water_name(mr_3d):
    """Test name of precipitable water cube."""
    assert humidity.precipitable_water(mr_3d).name() == "precipitable_water"


def test_precipitable_water_units(mr_3d):
    """Test units of precipitable water cube."""
    assert humidity.precipitable_water(mr_3d).units == cf_units.Unit("mm")


def test_precipitable_water_time(mr_time, pw_time):
    """Test precipitable water for cube varying in time."""
    assert np.allclose(
        pw_time.data, humidity.precipitable_water(mr_time).data, rtol=1e-6, atol=1e-2
    )


def test_precipitable_water_member(mr_member, pw_member):
    """Test precipitable water for cube varying in member."""
    assert np.allclose(
        pw_member.data,
        humidity.precipitable_water(mr_member).data,
        rtol=1e-6,
        atol=1e-2,
    )


def test_precipitable_water_5d(mr_5d, pw_5d):
    """Test precipitable water for 5D data."""
    assert np.allclose(
        pw_5d.data, humidity.precipitable_water(mr_5d).data, rtol=1e-6, atol=1e-2
    )


def test_saturation_precipitable_water(mr_3d, rh_3d, spw_3d):
    """Test calculation of saturation precipitable water for 3D data."""
    assert np.allclose(
        spw_3d.data,
        humidity.saturation_precipitable_water(mr_3d, rh_3d).data,
        rtol=1e-6,
        atol=1e-2,
    )


def test_saturation_precipitable_water_cubelist(mr_3d, rh_3d, spw_3d):
    """Test calculation of saturation precipitable water in a cubelist."""
    input_cube = iris.cube.CubeList([mr_3d, mr_3d])
    input_rh = iris.cube.CubeList([rh_3d, rh_3d])
    actual_cubelist = humidity.saturation_precipitable_water(input_cube, input_rh)
    expected_cubelist = iris.cube.CubeList([spw_3d, spw_3d])
    for cube_a, cube_b in zip(expected_cubelist, actual_cubelist, strict=True):
        assert np.allclose(cube_a.data, cube_b.data, rtol=1e-6, atol=1e-2)


def test_saturation_precipitable_water_name(mr_3d, rh_3d):
    """Test name of saturation precipitable water cube."""
    assert (
        humidity.saturation_precipitable_water(mr_3d, rh_3d).name()
        == "saturation_precipitable_water"
    )


def test_saturation_precipitable_water_units(mr_3d, rh_3d):
    """Test units of saturation precipitable water cube."""
    assert humidity.saturation_precipitable_water(mr_3d, rh_3d).units == cf_units.Unit(
        "mm"
    )


def test_saturation_precipitable_water_time(mr_time, rh_time, spw_time):
    """Test saturation precipitable water for cube varying in time."""
    assert np.allclose(
        spw_time.data,
        humidity.saturation_precipitable_water(mr_time, rh_time).data,
        rtol=1e-6,
        atol=1e-2,
    )


def test_saturation_precipitable_water_member(mr_member, rh_member, spw_member):
    """Test saturation precipitable water for cube varying in member."""
    assert np.allclose(
        spw_member.data,
        humidity.saturation_precipitable_water(mr_member, rh_member).data,
        rtol=1e-6,
        atol=1e-2,
    )


def test_saturation_precipitable_water_5d(mr_5d, rh_5d, spw_5d):
    """Test saturation precipitable water for 5D data."""
    assert np.allclose(
        spw_5d.data,
        humidity.saturation_precipitable_water(mr_5d, rh_5d).data,
        rtol=1e-6,
        atol=1e-2,
    )


def test_saturation_fraction(mr_3d, rh_3d, sf_3d):
    """Test calculation of saturation fraction for 3D data."""
    assert np.allclose(
        sf_3d.data,
        humidity.saturation_fraction(mr_3d, rh_3d).data,
        rtol=1e-6,
        atol=1e-2,
    )


def test_saturation_fraction_cubelist(mr_3d, rh_3d, sf_3d):
    """Test calculation of saturation fraction in a cubelist."""
    input_cube = iris.cube.CubeList([mr_3d, mr_3d])
    input_rh = iris.cube.CubeList([rh_3d, rh_3d])
    actual_cubelist = humidity.saturation_fraction(input_cube, input_rh)
    expected_cubelist = iris.cube.CubeList([sf_3d, sf_3d])
    for cube_a, cube_b in zip(expected_cubelist, actual_cubelist, strict=True):
        assert np.allclose(cube_a.data, cube_b.data, rtol=1e-6, atol=1e-2)


def test_saturation_fraction_name(mr_3d, rh_3d):
    """Test name of saturation fraction cube."""
    assert humidity.saturation_fraction(mr_3d, rh_3d).name() == "saturation_fraction"


def test_saturation_fraction_units(mr_3d, rh_3d):
    """Test units of saturation fraction cube."""
    assert humidity.saturation_fraction(mr_3d, rh_3d).units == cf_units.Unit("1")
