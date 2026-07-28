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
from cf_units import Unit

from CSET.operators import fluxes
from CSET.operators._atmospheric_constants import CPD, LV, RD


def _make_scalar_cube(
    value,
    var_name,
    units=None,
    standard_name=None,
    long_name=None,
):
    """Make tiny 1x1 cube with metadata and units."""
    data = np.array([[value]], dtype=np.float64)
    lat = iris.coords.DimCoord([0.0], standard_name="latitude", units="degrees")
    lon = iris.coords.DimCoord([0.0], standard_name="longitude", units="degrees")

    cube = iris.cube.Cube(
        data,
        dim_coords_and_dims=[(lat, 0), (lon, 1)],
        units=units if units is not None else Unit("unknown"),
        standard_name=standard_name,
        long_name=long_name,
    )
    cube.var_name = var_name
    return cube


def test_sensible_heat_flux_core_calculation():
    """Compute sensible heat flux from covariance, temperature and pressure."""
    wT = _make_scalar_cube(
        0.1,
        "wt_covariance",
        units=Unit("K m s-1"),
    )
    temp = _make_scalar_cube(
        20.0,
        "air_temperature",
        units=Unit("degC"),
        standard_name="air_temperature",
    )
    pressure = _make_scalar_cube(
        1000.0,
        "surface_air_pressure",
        units=Unit("hPa"),
    )
    out = fluxes.sensible_heat_flux_from_covariance(
        wt_flux=wT,
        air_temperature=temp,
        pressure=pressure,
    )
    arr = out.data
    if hasattr(arr, "compute"):
        arr = arr.compute()

    T = 20.0 + 273.15
    pPa = 1000.0 * 100.0
    rho = pPa / (RD * T)

    expected = CPD * rho * 0.1
    assert np.isclose(arr[0, 0], expected)
    assert out.name() == "surface_upward_sensible_heat_flux"
    assert out.units == Unit("W m-2")


def test_sensible_heat_flux_accepts_degc_covariance():
    """DegC m s-1 covariance should be treated as K m s-1."""
    wT = _make_scalar_cube(
        0.1,
        "wt_covariance_2m",
        units=Unit("degC m s-1"),
    )
    temp = _make_scalar_cube(
        20.0,
        "air_temperature_rtd_1p2m",
        units=Unit("degC"),
    )
    pressure = _make_scalar_cube(
        1000.0,
        "surface_pressure",
        units=Unit("hPa"),
    )
    out = fluxes.sensible_heat_flux_from_covariance(
        wt_flux=wT,
        air_temperature=temp,
        pressure=pressure,
    )
    assert out.units == Unit("W m-2")


def _make_scalar_latent_cube(
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


def test_latent_heat_units_conversion():
    """Test unit conversion of latent heat units."""
    wq = _make_scalar_latent_cube(0.001, "wq_covariance", units=Unit("kg m-2 s-1"))

    out = fluxes.latent_heat_units(wq)
    arr = out.data
    if hasattr(arr, "compute"):
        arr = arr.compute()

    expected = LV * 0.001
    assert np.isclose(arr[0, 0], expected)
    assert out.units == Unit("W m-2")


def test_latent_heat_units_passthrough_non_convertible():
    """Test operator returns unchanged cube if not convertible."""
    cube = _make_scalar_latent_cube(5.0, "not_flux", units=Unit("K"))
    out = fluxes.latent_heat_units(cube)
    # should be unchanged
    assert out == cube
    assert out.units == cube.units


def test_latent_heat_units_cubelist_mixed():
    """Test operator with mixed cubelist."""
    wq = _make_scalar_latent_cube(0.001, "wq_covariance", units=Unit("kg m-2 s-1"))
    other = _make_scalar_latent_cube(10.0, "temperature", units=Unit("K"))
    out = fluxes.latent_heat_units([wq, other])

    assert isinstance(out, iris.cube.CubeList)
    assert len(out) == 2
    # check conversion happened only for first cube
    converted = [c for c in out if c.units.is_convertible("W m-2")]
    assert len(converted) == 1
    converted = converted[0]
    arr = converted.data
    if hasattr(arr, "compute"):
        arr = arr.compute()

    assert np.isclose(arr[0, 0], LV * 0.001)
    assert converted.units == "W m-2"
    # check passthrough
    assert any(c is other for c in out)


def test_latent_heat_units_unknown_units_passthrough():
    """Test operator if units unknown."""
    cube = _make_scalar_latent_cube(1.0, "unknown", units=None)
    out = fluxes.latent_heat_units(cube)
    assert out is cube
