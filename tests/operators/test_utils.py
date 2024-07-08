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


@pytest.fixture(scope="session")
def transect_source_cube() -> iris.cube.Cube:
    """Get a 3D cube to test with."""
    return iris.load_cube("tests/test_data/transect_test_umpl.nc")


def test_missing_coord_get_cube_yxcoordname(source_cube):
    """Missing coordinate raises error."""
    # Missing X coordinate.
    source = source_cube.copy()
    source.remove_coord("longitude")
    with pytest.raises(ValueError):
        common_operators.get_cube_yxcoordname(source)

    # Missing Y coordinate.
    source = source_cube.copy()
    source.remove_coord("latitude")
    with pytest.raises(ValueError):
        common_operators.get_cube_yxcoordname(source)


def test_get_cube_yxcoordname(source_cube):
    """Check that function returns tuple containing horizontal dimension names."""
    assert (common_operators.get_cube_yxcoordname(source_cube)) == (
        "latitude",
        "longitude",
    )


def test_is_transect_multiplespatialcoords(source_cube):
    """Check that function returns False as more than one spatial map coord."""
    assert not common_operators.is_transect(source_cube)


def test_is_transect_noverticalcoord(transect_source_cube):
    """Check that function returns False as no vertical coord found."""
    # Retain only time and latitude coordinate, so it passes the first spatial coord test.
    transect_source_cube_slice = transect_source_cube[:, 0, :, 0]
    assert not common_operators.is_transect(transect_source_cube_slice)


def test_is_transect_correctcoord(transect_source_cube):
    """Check that function returns True as one map and vertical coord found."""
    # Retain only time and latitude coordinate, so it passes the first spatial coord test.
    transect_source_cube_slice = transect_source_cube[:, :, :, 0]
    assert common_operators.is_transect(transect_source_cube_slice)


def test_combine_singlecube_into_cubelist(source_cube):
    """Test case of single cube into cubelist."""
    cubelist = common_operators.combine_cubes_into_cubelist(source_cube)

    expected_cubelist = (
        "[<iris 'Cube' of surface_altitude / (m) (latitude: 200; longitude: 200)>]"
    )
    assert repr(cubelist) in expected_cubelist


def test_combine_singlecubelist_into_cubelist(source_cube, transect_source_cube):
    """Test case of single cubelist into cubelist."""
    cubelist = common_operators.combine_cubes_into_cubelist(
        iris.cube.CubeList([source_cube, transect_source_cube])
    )

    expected_cubelist = "[<iris 'Cube' of surface_altitude / (m) (latitude: 200; longitude: 200)>,\n<iris 'Cube' of air_temperature / (K) (time: 2; pressure: 16; latitude: 6; longitude: 6)>]"
    assert repr(cubelist) in expected_cubelist


def test_combine_single_noncompliant_into_cubelist():
    """Test case of single object which isn't cube or cubelist."""
    with pytest.raises(TypeError):
        common_operators.combine_cubes_into_cubelist("hello")


def test_combine_multiplecube_into_cubelist(source_cube, transect_source_cube):
    """Test case of multiple cube into cubelist."""
    cubelist = common_operators.combine_cubes_into_cubelist(
        source_cube, a=transect_source_cube
    )

    expected_cubelist = "[<iris 'Cube' of surface_altitude / (m) (latitude: 200; longitude: 200)>,\n<iris 'Cube' of air_temperature / (K) (time: 2; pressure: 16; latitude: 6; longitude: 6)>]"

    assert repr(cubelist) in expected_cubelist


def test_combine_multiple_cube_and_noncompliant_into_cubelist(source_cube):
    """Test case of a valid cube with some non compliant data which isn't cube or cubelist."""
    with pytest.raises(TypeError):
        common_operators.combine_cubes_into_cubelist(source_cube, a="hello")


def test_combine_multiplecube_mixed_into_cubelist(source_cube, transect_source_cube):
    """Test case of multiple cubes and cubelist into cubelist."""
    cubelist = common_operators.combine_cubes_into_cubelist(
        source_cube, a=transect_source_cube
    )
    out_cubelist = common_operators.combine_cubes_into_cubelist(
        source_cube, a=cubelist, b=transect_source_cube
    )

    expected_cubelist = "[<iris 'Cube' of surface_altitude / (m) (latitude: 200; longitude: 200)>,\n<iris 'Cube' of surface_altitude / (m) (latitude: 200; longitude: 200)>,\n<iris 'Cube' of air_temperature / (K) (time: 2; pressure: 16; latitude: 6; longitude: 6)>,\n<iris 'Cube' of air_temperature / (K) (time: 2; pressure: 16; latitude: 6; longitude: 6)>]"

    assert repr(out_cubelist) in expected_cubelist
