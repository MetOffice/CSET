# Copyright 2023 Met Office and contributors.
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

"""Tests for convection diagnostics."""

import iris
import iris.cube
import numpy as np
import pytest

import CSET.operators.convection as convection


@pytest.fixture
def SBCAPE() -> iris.cube.Cube:
    """Get a SBCAPE cube."""
    return iris.load_cube("tests/test_data/convection/SBCAPE.nc")


@pytest.fixture
def MUCAPE() -> iris.cube.Cube:
    """Get an MUCAPE cube."""
    return iris.load_cube("tests/test_data/convection/MUCAPE.nc")


@pytest.fixture
def MUCIN() -> iris.cube.Cube:
    """Get a MUCIN cube."""
    return iris.load_cube("tests/test_data/convection/MUCIN.nc")


@pytest.fixture
def EIB() -> iris.cube.Cube:
    """Get an EIB cube."""
    return iris.load_cube("tests/test_data/convection/EIB.nc")


@pytest.fixture
def BLheight() -> iris.cube.Cube:
    """Get a BLheight cube."""
    return iris.load_cube("tests/test_data/convection/BLheight.nc")


@pytest.fixture
def orography_2D() -> iris.cube.Cube:
    """Get a 2D Orography cube."""
    return iris.load_cube("tests/test_data/convection/Orography2D.nc")


def test_cape_ratio(SBCAPE, MUCAPE, MUCIN):
    """Compare with precalculated ratio KGOs."""
    # Calculate the diagnostic.
    cape_75 = convection.cape_ratio(SBCAPE, MUCAPE, MUCIN)
    # Compare with KGO.
    precalculated_75 = iris.load_cube("tests/test_data/convection/ECFlagB.nc")
    assert np.allclose(cape_75.data, precalculated_75.data, atol=1e-5, equal_nan=True)

    # Calculate the diagnostic.
    cape_1p5 = convection.cape_ratio(SBCAPE, MUCAPE, MUCIN, MUCIN_thresh=-1.5)
    # Compare with KGO.
    precalculated_1p5 = iris.load_cube("tests/test_data/convection/ECFlagB_2.nc")
    assert np.allclose(cape_1p5.data, precalculated_1p5.data, atol=1e-5, equal_nan=True)


def test_inflow_layer_properties(EIB, BLheight, orography_2D):
    """Compare with precalculated properties."""
    inflow_layer_properties = convection.inflow_layer_properties(
        EIB, BLheight, orography_2D
    )
    precalculated = iris.load_cube("tests/test_data/convection/ECFlagD.nc")
    assert np.allclose(inflow_layer_properties.data, precalculated.data)
