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

"""Tests for ensemble operators."""

import iris
import iris.cube
import numpy as np
import pytest

from CSET.operators import ensembles, read


@pytest.fixture()
def xwind() -> iris.cube.Cube:
    """Get xwind to run tests on."""
    return read.read_cube("tests/test_data/ageofair/aoa_in_ens.nc", "x_wind")


@pytest.fixture()
def xwind_deterministic() -> iris.cube.Cube:
    """Get xwind to run tests on."""
    return read.read_cube("tests/test_data/ageofair/aoa_in_rgd.nc", "x_wind")


@pytest.fixture()
def ywind() -> iris.cube.Cube:
    """Get ywind to run tests on."""
    return read.read_cube("tests/test_data/ageofair/aoa_in_ens.nc", "y_wind")


@pytest.fixture()
def ywind_deterministic() -> iris.cube.Cube:
    """Get xwind to run tests on."""
    return read.read_cube("tests/test_data/ageofair/aoa_in_rgd.nc", "y_wind")


def test_DKE(xwind, ywind):
    """Test DKE calculation."""
    DKE_calc = ywind[1:, :].copy()
    DKE_calc.data[:] = 0.0
    DKE_calc.data[:] = (
        0.5 * (xwind.data[0, :] - xwind.data[1:, :]) ** 2
        + 0.5 * (ywind.data[0, :] - ywind.data[1:, :]) ** 2
    )
    assert np.allclose(
        DKE_calc.data,
        ensembles.DKE(xwind, ywind).data,
        rtol=1e-06,
        atol=1e-02,
    )


def test_DKE_no_realization_u(xwind_deterministic, ywind):
    """Test DKE fails with no realization coordinate for u."""
    with pytest.raises(ValueError):
        ensembles.DKE(xwind_deterministic, ywind)


def test_DKE_no_realization_v(xwind, ywind_deterministic):
    """Test DKE fails with no realization coordinate for v."""
    with pytest.raises(ValueError):
        ensembles.DKE(xwind, ywind_deterministic)


def test_DKE_wrong_order_u(xwind, ywind):
    """Test DKE fails when realization is not the first coordinate in u."""
    xwind.transpose([1, 0, 2, 3, 4])
    with pytest.raises(ValueError):
        ensembles.DKE(xwind, ywind)


def test_DKE_wrong_order_v(xwind, ywind):
    """Test DKE fails when realization is not the first coordinate in v."""
    ywind.transpose([1, 0, 2, 3, 4])
    with pytest.raises(ValueError):
        ensembles.DKE(xwind, ywind)


def test_DKE_shape_mismatch(xwind, ywind):
    """Test DKE fails when there is a shape mismatch between u and v."""
    xwind = xwind[:, 1:, :]
    with pytest.raises(ValueError):
        ensembles.DKE(xwind, ywind)


def test_DKE_coordinate_mismatch(xwind, ywind):
    """Test DKE fails when there is a coordinate mismatch between u and v."""
    xwind_new = iris.cube.Cube(
        xwind.data,
        dim_coords_and_dims=[
            (xwind.coord("realization"), 0),
            (xwind.coord("time"), 1),
            (xwind.coord("pressure")[::-1], 2),
            (xwind.coord("grid_latitude"), 3),
            (xwind.coord("grid_longitude"), 4),
        ],
    )
    with pytest.raises(ValueError):
        ensembles.DKE(xwind_new, ywind)
