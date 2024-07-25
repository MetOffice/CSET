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
import iris.coord_systems
import iris.cube
import numpy as np
import pytest

import CSET.operators.regrid as regrid


# Session scope fixtures, so the test data only has to be loaded once.
@pytest.fixture(scope="session")
def regrid_source_cube() -> iris.cube.Cube:
    """Get a cube to regrid."""
    return iris.load_cube(
        "tests/test_data/regrid/regrid_rectilinearGeogCS.nc", "surface_altitude"
    )


@pytest.fixture(scope="session")
def regrid_test_cube() -> iris.cube.Cube:
    """Get a regridded cube to compare."""
    return iris.load_cube("tests/test_data/regrid/out_rectilinearGeogCS_0p5deg.nc")


def test_regrid_onto_cube(regrid_source_cube, regrid_test_cube):
    """Test regrid case where target cube to project onto is specified."""
    # Test 1: Rectilinear GeogCS grid case
    assert np.allclose(
        regrid.regrid_onto_cube(
            regrid_source_cube, regrid_test_cube, method="Linear"
        ).data,
        regrid_test_cube.data,
        rtol=1e-06,
        atol=1e-02,
    )


def test_regrid_onto_cube_cubes(regrid_source_cube, regrid_test_cube):
    """Test regrid case where target cube to project onto is specified for multiple cubes."""
    # Create cubelist with multiple cubes.
    cubelist_to_regrid = iris.cube.CubeList([regrid_source_cube, regrid_source_cube])
    regridded_cubes = regrid.regrid_onto_cube(
        cubelist_to_regrid, regrid_test_cube, method="Linear"
    )
    expected_cubelist = "[<iris 'Cube' of surface_altitude / (m) (latitude: 16; longitude: 16)>,\n<iris 'Cube' of surface_altitude / (m) (latitude: 16; longitude: 16)>]"
    assert repr(regridded_cubes) in expected_cubelist


def test_regrid_onto_xyspacing_cubes(regrid_source_cube, regrid_test_cube):
    """Test regrid case where xyspacing to project onto is specified for multiple cubes."""
    # Create cubelist with multiple cubes
    cubelist_to_regrid = iris.cube.CubeList([regrid_source_cube, regrid_source_cube])

    regridded_cubes = regrid.regrid_onto_xyspacing(
        cubelist_to_regrid, xspacing=0.5, yspacing=0.5, method="Linear"
    )

    expected_cubelist = "[<iris 'Cube' of surface_altitude / (m) (latitude: 16; longitude: 16)>,\n<iris 'Cube' of surface_altitude / (m) (latitude: 16; longitude: 16)>]"

    assert repr(regridded_cubes) in expected_cubelist


def test_regrid_onto_cube_unknown_crs(regrid_source_cube, regrid_test_cube):
    """Coordinate reference system is unrecognised."""
    # Exchange X to unsupported coordinate system.
    source_changed_x = regrid_source_cube.copy()
    source_changed_x.coord("longitude").coord_system = iris.coord_systems.OSGB()
    with pytest.raises(NotImplementedError):
        regrid.regrid_onto_cube(source_changed_x, regrid_test_cube, method="Linear")

    # Exchange Y to unsupported coordinate system.
    source_changed_y = regrid_source_cube.copy()
    source_changed_y.coord("latitude").coord_system = iris.coord_systems.OSGB()
    with pytest.raises(NotImplementedError):
        regrid.regrid_onto_cube(source_changed_y, regrid_test_cube, method="Linear")


def test_regrid_onto_cube_non_callable_method(regrid_source_cube, regrid_test_cube):
    """Method exists but is not callable."""
    with pytest.raises(NotImplementedError):
        regrid.regrid_onto_cube(regrid_source_cube, regrid_test_cube, method="maths")


def test_regrid_onto_cube_unknown_method(regrid_source_cube, regrid_test_cube):
    """Method does not exist."""
    with pytest.raises(NotImplementedError):
        regrid.regrid_onto_cube(
            regrid_source_cube, regrid_test_cube, method="nonexistent"
        )


def test_regrid_onto_xyspacing(regrid_source_cube, regrid_test_cube):
    """Test regrid case where x and y spacing are specified."""
    # Test 1: Rectilinear GeogCS grid case
    assert np.allclose(
        regrid.regrid_onto_xyspacing(
            regrid_source_cube, xspacing=0.5, yspacing=0.5, method="Linear"
        ).data,
        regrid_test_cube.data,
        rtol=1e-06,
        atol=1e-02,
    )


def test_regrid_onto_xyspacing_unknown_crs(regrid_source_cube):
    """Coordinate reference system is unrecognised."""
    # Exchange X to unsupported coordinate system.
    source_changed_x = regrid_source_cube.copy()
    source_changed_x.coord("longitude").coord_system = iris.coord_systems.OSGB()
    with pytest.raises(NotImplementedError):
        regrid.regrid_onto_xyspacing(
            source_changed_x, xspacing=0.5, yspacing=0.5, method="Linear"
        )

    # Exchange Y to unsupported coordinate system.
    source_changed_y = regrid_source_cube.copy()
    source_changed_y.coord("latitude").coord_system = iris.coord_systems.OSGB()
    with pytest.raises(NotImplementedError):
        regrid.regrid_onto_xyspacing(
            source_changed_y, xspacing=0.5, yspacing=0.5, method="Linear"
        )


def test_regrid_onto_xyspacing_non_callable_method(regrid_source_cube):
    """Method exists but is not callable."""
    with pytest.raises(NotImplementedError):
        regrid.regrid_onto_xyspacing(
            regrid_source_cube, xspacing=0.5, yspacing=0.5, method="maths"
        )


def test_regrid_onto_xyspacing_unknown_method(regrid_source_cube):
    """Method does not exist."""
    with pytest.raises(NotImplementedError):
        regrid.regrid_onto_xyspacing(
            regrid_source_cube, xspacing=0.5, yspacing=0.5, method="nonexistent"
        )
