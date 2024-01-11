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
import numpy as np

import CSET.operators.convection as convection


def test_cape_ratio():
    """Compare with precalculated ratio."""
    SBCAPE = iris.load_cube("tests/test_data/convection/SBCAPE.nc")
    MUCAPE = iris.load_cube("tests/test_data/convection/MUCAPE.nc")
    MUCIN = iris.load_cube("tests/test_data/convection/MUCIN.nc")
    cape_75 = convection.cape_ratio(SBCAPE, MUCAPE, MUCIN)
    precalculated_75 = iris.load_cube("tests/test_data/convection/ECFlagB.nc")
    assert np.allclose(cape_75.data, precalculated_75.data, atol=1e-5, equal_nan=True)
    # TODO: Test data clobbered by -75, so disabled until regenerated.
    cape_1p5 = convection.cape_ratio(SBCAPE, MUCAPE, MUCIN, MUCIN_thresh=-1.5)
    precalculated_1p5 = iris.load_cube("tests/test_data/convection/ECFlagB_2.nc")
    assert np.allclose(cape_1p5.data, precalculated_1p5.data, atol=1e-5, equal_nan=True)


def test_inflow_layer_properties():
    """Compare with precalculated properties."""
    EIB = iris.load_cube("tests/test_data/convection/EIB.nc")
    BLheight = iris.load_cube("tests/test_data/convection/BLheight.nc")
    Orography = iris.load_cube("tests/test_data/convection/Orography.nc")
    inflow_layer_properties = convection.inflow_layer_properties(
        EIB, BLheight, Orography
    )
    precalculated = iris.load_cube("tests/test_data/convection/ECFlagD.nc")
    assert np.allclose(inflow_layer_properties.data, precalculated.data)
