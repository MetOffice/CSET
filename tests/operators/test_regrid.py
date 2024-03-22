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

"""Tests regrid operator."""

import iris
import numpy as np

import CSET.operators.regrid as regrid


def test_regrid_onto_xyspacing():
    """Test regrid case where x and y spacing are specified."""
    # Test 1: Rectilinear GeogCS grid case
    test_data = iris.load_cube(
        "tests/test_data/regrid/regrid_rectilinearGeogCS.nc", "surface_altitude"
    )
    regridded_test_data = iris.load_cube(
        "tests/test_data/regrid/out_rectilinearGeogCS_0p5deg.nc"
    )

    assert np.allclose(
        regrid.regrid_onto_xyspacing(
            test_data, xspacing=0.5, yspacing=0.5, regridmethod="Linear"
        ).data.all(),
        regridded_test_data.data.all(),
        rtol=1e-02,
        atol=1e-02,
    )


def test_regrid_onto_cube():
    """Test regrid case where target cube to project onto is specified."""
    # Test 1: Rectilinear GeogCS grid case
    test_data = iris.load_cube(
        "tests/test_data/regrid/regrid_rectilinearGeogCS.nc", "surface_altitude"
    )
    regridded_test_data = iris.load_cube(
        "tests/test_data/regrid/out_rectilinearGeogCS_0p5deg.nc"
    )

    assert np.allclose(
        regrid.regrid_onto_cube(
            test_data, regridded_test_data, regridmethod="Linear"
        ).data.all(),
        regridded_test_data.data.all(),
        rtol=1e-02,
        atol=1e-02,
    )
