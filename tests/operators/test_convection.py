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

import CSET.operators.convection as convection


def test_cape_ratio():
    """Compare with precalculated ratio."""
    precalculated = iris.load_cube("tests/test_data/convection/ECFlagB.nc")
    precalculated_2 = iris.load_cube("tests/test_data/convection/ECFlagB_2.nc")
    SBCAPE = iris.load_cube("tests/test_data/convection/SBCAPE.nc")
    MUCAPE = iris.load_cube("tests/test_data/convection/MUCAPE.nc")
    MUCIN = iris.load_cube("tests/test_data/convection/MUCIN.nc")
    assert (
        convection.cape_ratio(SBCAPE, MUCAPE, MUCIN).data.all()
        == precalculated.data.all()
    )
    assert (
        convection.cape_ratio(SBCAPE, MUCAPE, MUCIN, MUCIN_thresh=-1.5).data.all()
        == precalculated_2.data.all()
    )


def test_inflow_layer_properties():
    """Compare with precalculated properties."""
    precalculated = iris.load_cube("tests/test_data/convection/ECFlagD.nc")
    EIB = iris.load_cube("tests/test_data/convection/EIB.nc")
    BLheight = iris.load_cube("tests/test_data/convection/BLheight.nc")
    Orography = iris.load_cube("tests/test_data/convection/Orography.nc")
    assert np.allclose(convection.inflow_layer_properties(EIB, BLheight, Orography).data, precalculated.data)
