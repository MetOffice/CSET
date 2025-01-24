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

"""Tests for convection diagnostics."""

import iris
import iris.cube
import numpy as np
import pytest

from CSET.operators import convection, read


@pytest.fixture
def SBCAPE() -> iris.cube.Cube:
    """Get a SBCAPE cube."""
    return read.read_cube("tests/test_data/convection/SBCAPE.nc")


@pytest.fixture
def MUCAPE() -> iris.cube.Cube:
    """Get an MUCAPE cube."""
    return read.read_cube("tests/test_data/convection/MUCAPE.nc")


@pytest.fixture
def MUCIN() -> iris.cube.Cube:
    """Get a MUCIN cube."""
    return read.read_cube("tests/test_data/convection/MUCIN.nc")


@pytest.fixture
def EIB() -> iris.cube.Cube:
    """Get an EIB cube."""
    return read.read_cube("tests/test_data/convection/EIB.nc")


@pytest.fixture
def BLheight() -> iris.cube.Cube:
    """Get a BLheight cube."""
    return read.read_cube("tests/test_data/convection/BLheight.nc")


@pytest.fixture
def orography_2D() -> iris.cube.Cube:
    """Get a 2D Orography cube."""
    return read.read_cube("tests/test_data/convection/Orography2D.nc")


@pytest.fixture
def orography_3D() -> iris.cube.Cube:
    """Get a 3D Orography cube (time)."""
    return read.read_cube("tests/test_data/convection/Orography3D.nc")


@pytest.fixture
def orography_3D_ens() -> iris.cube.Cube:
    """Get a 3D Orography cube (realization)."""
    return read.read_cube("tests/test_data/convection/Orography3D_ens.nc")


@pytest.fixture
def orography_4D() -> iris.cube.Cube:
    """Get a 4D Orography cube (time and realization)."""
    return read.read_cube("tests/test_data/convection/Orography4D.nc")


def test_cape_ratio(SBCAPE, MUCAPE, MUCIN):
    """Compare with precalculated ratio KGOs."""
    # Calculate the diagnostic.
    cape_75 = convection.cape_ratio(SBCAPE, MUCAPE, MUCIN)
    # Compare with KGO.
    precalculated_75 = read.read_cube("tests/test_data/convection/ECFlagB.nc")
    assert np.allclose(cape_75.data, precalculated_75.data, atol=1e-5, equal_nan=True)

    # Calculate the diagnostic.
    cape_1p5 = convection.cape_ratio(SBCAPE, MUCAPE, MUCIN, MUCIN_thresh=-1.5)
    # Compare with KGO.
    precalculated_1p5 = read.read_cube("tests/test_data/convection/ECFlagB_2.nc")
    assert np.allclose(cape_1p5.data, precalculated_1p5.data, atol=1e-5, equal_nan=True)


def test_cape_ratio_non_masked_arrays(SBCAPE, MUCAPE, MUCIN):
    """Calculate with non-masked arrays and compare with precalculated ratio."""
    # Replace masked values with NaNs.
    SBCAPE.data = SBCAPE.data.filled(np.nan)
    MUCAPE.data = MUCAPE.data.filled(np.nan)
    MUCIN.data = MUCIN.data.filled(np.nan)

    # Calculate the diagnostic.
    cape_75 = convection.cape_ratio(SBCAPE, MUCAPE, MUCIN)

    # Compare with KGO.
    precalculated_75 = read.read_cube("tests/test_data/convection/ECFlagB.nc")
    assert np.allclose(cape_75.data, precalculated_75.data, atol=1e-5, equal_nan=True)


def test_inflow_layer_properties(EIB, BLheight, orography_2D):
    """Compare with precalculated properties."""
    inflow_layer_properties = convection.inflow_layer_properties(
        EIB, BLheight, orography_2D
    )
    precalculated = read.read_cube("tests/test_data/convection/ECFlagD.nc")
    assert np.allclose(inflow_layer_properties.data, precalculated.data)


def test_inflow_layer_properties_non_masked_arrays(EIB, BLheight, orography_2D):
    """Use non-masked data and compare with precalculated properties."""
    # Unmask the data.
    EIB.data = EIB.data.filled(np.nan)
    inflow_layer_properties = convection.inflow_layer_properties(
        EIB, BLheight, orography_2D
    )
    precalculated = read.read_cube("tests/test_data/convection/ECFlagD.nc")
    assert np.allclose(inflow_layer_properties.data, precalculated.data)


def test_inflow_layer_properties_3D_orography_time(EIB, BLheight, orography_3D):
    """Reduce a 3D orography (time) field down to 2D."""
    inflow_layer_properties = convection.inflow_layer_properties(
        EIB, BLheight, orography_3D
    )
    precalculated = read.read_cube("tests/test_data/convection/ECFlagD.nc")
    assert np.allclose(inflow_layer_properties.data, precalculated.data)


def test_inflow_layer_properties_3D_orography_ensemble(EIB, BLheight, orography_3D_ens):
    """Reduce a 3D orography (realisation) field down to 2D."""
    inflow_layer_properties = convection.inflow_layer_properties(
        EIB, BLheight, orography_3D_ens
    )
    precalculated = read.read_cube("tests/test_data/convection/ECFlagD.nc")
    assert np.allclose(inflow_layer_properties.data, precalculated.data)


def test_inflow_layer_properties_4D_orography(EIB, BLheight, orography_4D):
    """Reduce a 4D orography (time and realisation) field down to 2D."""
    inflow_layer_properties = convection.inflow_layer_properties(
        EIB, BLheight, orography_4D
    )
    precalculated = read.read_cube("tests/test_data/convection/ECFlagD.nc")
    assert np.allclose(inflow_layer_properties.data, precalculated.data)
