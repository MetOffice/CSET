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

"""Tests for age of air operator."""

import iris
import iris.cube
import numpy as np
import pytest

from CSET.operators import ageofair, read


@pytest.fixture()
def xwind() -> iris.cube.Cube:
    """Get regridded xwind to run tests on."""
    return read.read_cube("tests/test_data/ageofair/aoa_in_rgd.nc", "x_wind")


@pytest.fixture()
def ywind() -> iris.cube.Cube:
    """Get regridded ywind to run tests on."""
    return read.read_cube("tests/test_data/ageofair/aoa_in_rgd.nc", "y_wind")


@pytest.fixture()
def wwind() -> iris.cube.Cube:
    """Get regridded wwind to run tests on."""
    return read.read_cube(
        "tests/test_data/ageofair/aoa_in_rgd.nc", "upward_air_velocity"
    )


@pytest.fixture()
def geopot() -> iris.cube.Cube:
    """Get regridded geopotential height to run tests on."""
    return read.read_cube(
        "tests/test_data/ageofair/aoa_in_rgd.nc", "geopotential_height"
    )


@pytest.fixture()
def ens_regridded() -> iris.cube.CubeList:
    """Get regridded ensemble cubelist to run tests on."""
    return read.read_cubes("tests/test_data/ageofair/aoa_in_ens.nc")


@pytest.fixture()
def ens_regridded_out() -> iris.cube.Cube:
    """Get age of air ensemble output to check results are consistent."""
    return read.read_cube("tests/test_data/ageofair/aoa_out_ens.nc")


def test_calc_dist():
    """Test distance calculated from calc_dist in age of air calculation.

    Allow a tolerance of 20km (as we expect some error).
    """
    # London and Johannesburg coordinates to 2 decimal places.
    london_coords = (51.51, -0.13)
    johanbg_coords = (-26.21, 28.03)

    dist = ageofair._calc_dist(london_coords, johanbg_coords)
    actual_distance = 9068670  # Air line according to Google?!

    assert np.allclose(dist, actual_distance, rtol=1e-06, atol=20000)


def test_aoa_nocyclic(xwind, ywind, wwind, geopot):
    """Test case when not cyclic."""
    assert np.allclose(
        ageofair.compute_ageofair(
            xwind, ywind, wwind, geopot, plev=500, cyclic=False
        ).data,
        read.read_cube("tests/test_data/ageofair/aoa_out_nocyclic.nc").data,
        rtol=1e-06,
        atol=1e-02,
    )


def test_aoa_cyclic_parallel_processing(xwind, ywind, wwind, geopot):
    """Test case when cyclic with parallel processing."""
    assert np.allclose(
        ageofair.compute_ageofair(
            xwind,
            ywind,
            wwind,
            geopot,
            plev=500,
            cyclic=True,
            multicore=True,
        ).data,
        read.read_cube("tests/test_data/ageofair/aoa_out_cyclic.nc").data,
        rtol=1e-06,
        atol=1e-02,
    )


def test_aoa_cyclic_single_process(xwind, ywind, wwind, geopot):
    """Test case when cyclic with no parallelisation."""
    assert np.allclose(
        ageofair.compute_ageofair(
            xwind,
            ywind,
            wwind,
            geopot,
            plev=500,
            cyclic=True,
            multicore=False,
        ).data,
        read.read_cube("tests/test_data/ageofair/aoa_out_cyclic.nc").data,
        rtol=1e-06,
        atol=1e-02,
    )


def test_aoa_mismatched_size(xwind, ywind, wwind, geopot):
    """Mismatched array size raises error."""
    ywind = ywind[:, :, 1:, :]
    with pytest.raises(ValueError):
        ageofair.compute_ageofair(xwind, ywind, wwind, geopot, plev=500, cyclic=True)


def test_aoa_timefreq(xwind, ywind, wwind, geopot):
    """Variable time intervals raises NotImplemented error."""
    with pytest.raises(NotImplementedError):
        ageofair.compute_ageofair(
            xwind[[1, 2, 4, 5], :, :, :],
            ywind[[1, 2, 4, 5], :, :, :],
            wwind[[1, 2, 4, 5], :, :, :],
            geopot[[1, 2, 4, 5], :, :, :],
            plev=500,
            cyclic=True,
        )


def test_aoa_timeunits(xwind, ywind, wwind, geopot):
    """Time intervals that are not hourly raises NotImplemented error."""
    xwind.coord("time").units = "days since 1970-01-01 00:00:00"
    with pytest.raises(NotImplementedError):
        ageofair.compute_ageofair(xwind, ywind, wwind, geopot, plev=500, cyclic=True)


def test_aoa_plevreq(xwind, ywind, wwind, geopot):
    """Pressure level requested that doesn't exist raises Index error."""
    with pytest.raises(IndexError):
        ageofair.compute_ageofair(xwind, ywind, wwind, geopot, plev=123, cyclic=True)


def test_aoa_ens(ens_regridded, ens_regridded_out):
    """Test case including vertical velocity and not cyclic for ensemble data."""
    assert np.allclose(
        ageofair.compute_ageofair(
            ens_regridded.extract("x_wind")[0],
            ens_regridded.extract("y_wind")[0],
            ens_regridded.extract("upward_air_velocity")[0],
            ens_regridded.extract("geopotential_height")[0],
            plev=200,
            cyclic=False,
            multicore=False,
        ).data,
        ens_regridded_out.data,
        rtol=1e-06,
        atol=1e-02,
    )


def test_aoa_ens_multicore(ens_regridded, ens_regridded_out):
    """Test case with ensembles ensuring that single core and multicore produce identical values."""
    assert np.allclose(
        ageofair.compute_ageofair(
            ens_regridded.extract("x_wind")[0],
            ens_regridded.extract("y_wind")[0],
            ens_regridded.extract("upward_air_velocity")[0],
            ens_regridded.extract("geopotential_height")[0],
            plev=200,
            cyclic=False,
            multicore=True,
        ).data,
        ens_regridded_out.data,
        rtol=1e-06,
        atol=1e-02,
    )


def test_aoa_misordered_dims(xwind, ywind, wwind, geopot):
    """Dimensions in input cubes do not match expected ordering."""
    xwind.transpose([0, 1, 3, 2])
    ywind.transpose([0, 1, 3, 2])
    wwind.transpose([0, 1, 3, 2])
    geopot.transpose([0, 1, 3, 2])
    with pytest.raises(ValueError):
        ageofair.compute_ageofair(
            xwind,
            ywind,
            wwind,
            geopot,
            plev=500,
            cyclic=True,
        )


def test_aoa_misordered_dims_ens(ens_regridded):
    """Dimensions in input cubes do not match expected ordering."""
    xwind = ens_regridded.extract("x_wind")[0]
    ywind = ens_regridded.extract("y_wind")[0]
    wwind = ens_regridded.extract("upward_air_velocity")[0]
    geopot = ens_regridded.extract("geopotential_height")[0]
    xwind.transpose([0, 1, 2, 4, 3])
    ywind.transpose([0, 1, 2, 4, 3])
    wwind.transpose([0, 1, 2, 4, 3])
    geopot.transpose([0, 1, 2, 4, 3])
    with pytest.raises(ValueError):
        ageofair.compute_ageofair(
            xwind,
            ywind,
            wwind,
            geopot,
            plev=500,
            cyclic=True,
        )
