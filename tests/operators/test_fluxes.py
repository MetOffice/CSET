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

"""Test turbulent flux operators."""

import iris
import iris.coords
import iris.cube
import numpy as np
import pytest
from cf_units import Unit

from CSET.operators import fluxes


def _make_scalar_cube(
    value,
    var_name,
    units=None,
):
    """Make tiny 1x1 cube with var_name and units."""
    data = np.array([[value]], dtype=np.float64)
    lat = iris.coords.DimCoord([0.0], standard_name="latitude", units="degrees")
    lon = iris.coords.DimCoord([0.0], standard_name="longitude", units="degrees")

    cube = iris.cube.Cube(
        data,
        dim_coords_and_dims=[(lat, 0), (lon, 1)],
        units=units if units is not None else Unit("unknown"),
    )
    cube.var_name = var_name
    return cube


def test_sensible_heat_units_requires_WT_Varnames():
    """Must provide WT_VARNAMES kwarg."""
    wT = _make_scalar_cube(0.1, "wt_covariance_2m", units=Unit("K m s-1"))
    t = _make_scalar_cube(20.0, "air_temperature_rtd_1p2m", units=Unit("degC"))
    p = _make_scalar_cube(1000.0, "pressure_barometric", units=Unit("hPa"))
    with pytest.raises(ValueError, match="requires WT_VARNAMES"):
        fluxes.sensible_heat_units([wT, t, p])


def test_sensible_heat_units_missing_required_inputs():
    """If any of the specified inputs are missing, raise."""
    wT = _make_scalar_cube(0.1, "wt_covariance_2m", units=Unit("K m s-1"))
    t = _make_scalar_cube(20.0, "air_temperature_rtd_1p2m", units=Unit("degC"))
    # pressure missing
    kwargs = {
        "WT_VARNAMES": "wt_covariance_2m,air_temperature_rtd_1p2m,pressure_barometric"
    }
    with pytest.raises(ValueError, match="missing inputs"):
        fluxes.sensible_heat_units([wT, t], **kwargs)


def test_sensible_heat_units():
    """Test that core calculation works."""
    wT = _make_scalar_cube(0.1, "wt_covariance_2m", units=Unit("K m s-1"))
    temp = _make_scalar_cube(20.0, "air_temperature_rtd_1p2m", units=Unit("degC"))
    press = _make_scalar_cube(1000.0, "pressure_barometric", units=Unit("hPa"))

    kwargs = {
        "WT_VARNAMES": "wt_covariance_2m,air_temperature_rtd_1p2m,pressure_barometric",
    }
    out = fluxes.sensible_heat_units([wT, temp, press], **kwargs)
    arr = out.data
    if hasattr(arr, "compute"):
        arr = arr.compute()

    Cp = 1004.67
    Rd = 287.05
    T = 20.0 + 273.15
    pPa = 1000.0 * 100.0
    rho = pPa / (Rd * T)
    expected = Cp * rho * 0.1
    assert np.isclose(arr[0, 0], expected)


def test_sensible_heat_units_returns_cube_when_only_shf_remains():
    """If no cubes remain, function should return single Cube."""
    wT = _make_scalar_cube(0.1, "wt_covariance_2m", units=Unit("K m s-1"))
    temp = _make_scalar_cube(20.0, "air_temperature_rtd_1p2m", units=Unit("degC"))
    press = _make_scalar_cube(1000.0, "pressure_barometric", units=Unit("hPa"))

    kwargs = {
        "WT_VARNAMES": "wt_covariance_2m,air_temperature_rtd_1p2m,pressure_barometric"
    }

    out = fluxes.sensible_heat_units([wT, temp, press], **kwargs)
    assert isinstance(out, iris.cube.Cube)
    assert out.var_name == "surface_upward_sensible_heat_flux"
    assert out.units == "W m-2"


def test_sensible_heat_units_passthrough_and_filtering():
    """Ensure input cubes are removed whilst others are kept."""
    wT = _make_scalar_cube(0.1, "wt_covariance_2m")
    temp = _make_scalar_cube(20.0, "air_temperature_rtd_1p2m")
    press = _make_scalar_cube(1000.0, "pressure_barometric")
    extra = _make_scalar_cube(5.0, "other_var")
    kwargs = {
        "WT_VARNAMES": "wt_covariance_2m,air_temperature_rtd_1p2m,pressure_barometric",
    }

    out = fluxes.sensible_heat_units([wT, temp, press, extra], **kwargs)

    assert isinstance(out, iris.cube.CubeList)
    varnames = [c.var_name for c in out]
    # input variables removed
    assert "wt_covariance_2m" not in varnames
    assert "air_temperature_rtd_1p2m" not in varnames
    assert "pressure_barometric" not in varnames
    # extra retained
    assert "other_var" in varnames
    # SHF added
    assert "surface_upward_sensible_heat_flux" in varnames


def test_latent_heat_units_conversion():
    """Test unit conversion of latent heat units."""
    wq = _make_scalar_cube(0.001, "wq_covariance", units=Unit("kg m-2 s-1"))

    out = fluxes.latent_heat_units(wq)
    arr = out.data
    if hasattr(arr, "compute"):
        arr = arr.compute()

    expected = 2.45e6 * 0.001
    assert np.isclose(arr[0, 0], expected)
    assert out.units == "W m-2"


def test_latent_heat_units_passthrough_non_convertible():
    """Test operator returns unchanged cube if not convertible."""
    cube = _make_scalar_cube(5.0, "not_flux", units=Unit("K"))
    out = fluxes.latent_heat_units(cube)
    # should be unchanged
    assert out is cube


def test_latent_heat_units_cubelist_mixed():
    """Test operator with mixed cubelist."""
    wq = _make_scalar_cube(0.001, "wq_covariance", units=Unit("kg m-2 s-1"))
    other = _make_scalar_cube(10.0, "temperature", units=Unit("K"))
    out = fluxes.latent_heat_units([wq, other])

    assert isinstance(out, iris.cube.CubeList)
    assert len(out) == 2
    # check conversion happened only for first cube
    converted = next(c for c in out if c.units == "W m-2")
    arr = converted.data
    if hasattr(arr, "compute"):
        arr = arr.compute()

    assert np.isclose(arr[0, 0], 2.45e6 * 0.001)
    assert converted.units == "W m-2"
    # check passthrough
    assert any(c is other for c in out)
