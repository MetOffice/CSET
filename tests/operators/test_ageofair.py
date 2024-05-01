# Copyright 2024 Met Office and contributors.
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

"""Tests age of air operators."""

import iris
import iris.cube
import numpy as np
import pytest

import CSET.operators.ageofair as ageofair


def test_calc_dist():
    """
    Test distance calculated from calc_dist in age of air calculation.

    Allow a tolerance of 20km (TBD, expect some error).
    """
    # London and Johannesburg coordinates to 2 decimal places.
    london_coords = (51.51, -0.13)
    johanbg_coords = (-26.21, 28.03)

    dist = ageofair.calc_dist(london_coords, johanbg_coords)
    actual_distance = 9068670  # Air line according to Google?!

    assert np.allclose(dist, actual_distance, rtol=1e-06, atol=20000)


def get_xwind() -> iris.cube.Cube:
    """Get regridded xwind to run tests on."""
    return iris.load_cube("tests/test_data/ageofair/aoa_in_rgd.nc", "x_wind")


def get_ywind() -> iris.cube.Cube:
    """Get regridded ywind to run tests on."""
    return iris.load_cube("tests/test_data/ageofair/aoa_in_rgd.nc", "y_wind")


def get_wwind() -> iris.cube.Cube:
    """Get regridded wwind to run tests on."""
    return iris.load_cube(
        "tests/test_data/ageofair/aoa_in_rgd.nc", "upward_air_velocity"
    )


def get_geopot() -> iris.cube.Cube:
    """Get regridded geopotential height to run tests on."""
    return iris.load_cube(
        "tests/test_data/ageofair/aoa_in_rgd.nc", "geopotential_height"
    )


def test_aoa_noincW_nocyclic(
    xwind=get_xwind, ywind=get_ywind, wwind=get_wwind, geopot=get_geopot
):
    """Test case no vertical velocity and not cyclic."""
    assert np.allclose(
        ageofair.compute_ageofair(
            xwind(), ywind(), wwind(), geopot(), plev=500, incW=False, cyclic=False
        ).data,
        iris.load_cube("tests/test_data/ageofair/aoa_out.nc").data,
        rtol=1e-06,
        atol=1e-02,
    )


def test_aoa_incW_nocyclic(
    xwind=get_xwind, ywind=get_ywind, wwind=get_wwind, geopot=get_geopot
):
    """Test case including vertical velocity and not cyclic."""
    assert np.allclose(
        ageofair.compute_ageofair(
            xwind(), ywind(), wwind(), geopot(), plev=500, incW=True, cyclic=False
        ).data,
        iris.load_cube("tests/test_data/ageofair/aoa_out_incW.nc").data,
        rtol=1e-06,
        atol=1e-02,
    )


def test_aoa_noincW_cyclic(
    xwind=get_xwind, ywind=get_ywind, wwind=get_wwind, geopot=get_geopot
):
    """Test case no vertical velocity and cyclic."""
    assert np.allclose(
        ageofair.compute_ageofair(
            xwind(), ywind(), wwind(), geopot(), plev=500, incW=False, cyclic=True
        ).data,
        iris.load_cube("tests/test_data/ageofair/aoa_out_cyclic.nc").data,
        rtol=1e-06,
        atol=1e-02,
    )


def test_aoa_incW_cyclic(
    xwind=get_xwind, ywind=get_ywind, wwind=get_wwind, geopot=get_geopot
):
    """Test case including vertical velocity and cyclic."""
    assert np.allclose(
        ageofair.compute_ageofair(
            xwind(), ywind(), wwind(), geopot(), plev=500, incW=True, cyclic=True
        ).data,
        iris.load_cube("tests/test_data/ageofair/aoa_out_incW_cyclic.nc").data,
        rtol=1e-06,
        atol=1e-02,
    )


def test_aoa_mismatched_size(
    xwind=get_xwind, ywind=get_ywind, wwind=get_wwind, geopot=get_geopot
):
    """Mismatched array size raises error."""
    ywind = ywind()[:, :, 1:, :]
    with pytest.raises(ValueError):
        ageofair.compute_ageofair(
            xwind(), ywind, wwind(), geopot(), plev=500, incW=True, cyclic=True
        )


def test_aoa_timefreq(
    xwind=get_xwind, ywind=get_ywind, wwind=get_wwind, geopot=get_geopot
):
    """Variable time intervals raises NotImplemented error."""
    xwind = xwind()
    # Sample time non-uniform.
    xwind = xwind[[1, 2, 4, 5], :, :, :]
    with pytest.raises(NotImplementedError):
        ageofair.compute_ageofair(
            xwind, ywind(), wwind(), geopot(), plev=500, incW=True, cyclic=True
        )


def test_aoa_timeunits(
    xwind=get_xwind, ywind=get_ywind, wwind=get_wwind, geopot=get_geopot
):
    """Time intervals that are not hourly raises NotImplemented error."""
    xwind = xwind()
    xwind.coord("time").units = "days since 1970-01-01 00:00:00"
    with pytest.raises(NotImplementedError):
        ageofair.compute_ageofair(
            xwind, ywind(), wwind(), geopot(), plev=500, incW=True, cyclic=True
        )


def test_aoa_plevreq(
    xwind=get_xwind, ywind=get_ywind, wwind=get_wwind, geopot=get_geopot
):
    """Pressure level requested that doesn't exist raises Value error."""
    with pytest.raises(ValueError):
        ageofair.compute_ageofair(
            xwind(), ywind(), wwind(), geopot(), plev=123, incW=True, cyclic=True
        )
