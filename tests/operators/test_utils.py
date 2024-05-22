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

"""Tests for common operator functionality across CSET."""

import iris
import iris.cube
import pytest

import CSET.operators._utils as common_operators


# Session scope fixtures, so the test data only has to be loaded once.
@pytest.fixture(scope="session")
def source_cube() -> iris.cube.Cube:
    """Get a cube to test with."""
    return iris.load_cube(
        "tests/test_data/regrid/regrid_rectilinearGeogCS.nc", "surface_altitude"
    )


def test_missing_coord_get_cube_xycoordname(source_cube):
    """Missing coordinate raises error."""
    # Missing X coordinate.
    source = source_cube.copy()
    source.remove_coord("longitude")
    with pytest.raises(ValueError):
        common_operators.get_cube_xycoordname(source)

    # Missing Y coordinate.
    source = source_cube.copy()
    source.remove_coord("latitude")
    with pytest.raises(ValueError):
        common_operators.get_cube_xycoordname(source)


def test_get_cube_xycoordname(source_cube):
    """Check that function returns tuple containing horizontal dimension names."""
    assert (common_operators.get_cube_xycoordname(source_cube)) == (
        "latitude",
        "longitude",
    )
