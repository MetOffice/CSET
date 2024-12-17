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

"""Tests for ensemble operators."""

import iris
import iris.cube
import numpy as np
import pytest

import CSET.operators.ensembles as ensembles


@pytest.fixture()
def xwind() -> iris.cube.Cube:
    """Get xwind to run tests on."""
    return iris.load_cube("tests/test_data/ageofair/aoa_in_ens.nc", "x_wind")


@pytest.fixture()
def ywind() -> iris.cube.Cube:
    """Get ywind to run tests on."""
    return iris.load_cube("tests/test_data/ageofair/aoa_in_ens.nc", "y_wind")


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
