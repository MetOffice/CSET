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

"""Tests regrid operator."""

import iris
import iris.coord_systems
import iris.cube
import numpy as np
import pytest

import CSET.operators.read as read
import CSET.operators.regrid as regrid
from CSET.operators.regrid import BoundaryWarning


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


def test_regrid_to_single_point_east(cube):
    """Test extracting a single point.

    Test that the grid latitude rotation works when the
    centre of the grid is too far east (that is, the centre
    of the longitude range is further east than 180 deg).
    """
    cube_fix = read._longitude_fix_callback(cube, None, None)
    regrid_cube = regrid.regrid_to_single_point(
        cube_fix, 0.5, -1.5, "Nearest", boundary_margin=1
    )
    expected_cube = "<iris 'Cube' of air_temperature / (K) (time: 3)>"
    assert repr(regrid_cube) == expected_cube


def test_regrid_to_single_point_west(cube):
    """Test extracting a single point.

    Test that the grid latitude rotation works when the
    centre of the grid is too far west (that is, the centre
    of the longitude range is further west than -180 deg).
    """
    long_coord = cube.coord("grid_longitude").points.copy()
    long_coord -= 720.0
    cube.coord("grid_longitude").points = long_coord
    cube_fix = read._longitude_fix_callback(cube, None, None)
    regrid_cube = regrid.regrid_to_single_point(
        cube_fix, 0.5, -1.5, "Nearest", boundary_margin=1
    )
    expected_cube = "<iris 'Cube' of air_temperature / (K) (time: 3)>"
    assert repr(regrid_cube) == expected_cube


def test_regrid_to_single_point_longitude_transform_1(cube):
    """Test extracting a single point.

    Test that, if a longitude selection is made that is too
    far east (further east than 180 deg), the code corrects it
    back into the standard range (-180 deg to 180 deg).
    """
    regrid_cube = regrid.regrid_to_single_point(
        cube, 0.5, 358.5, "Nearest", boundary_margin=1
    )
    expected_cube = "<iris 'Cube' of air_temperature / (K) (time: 3)>"
    assert repr(regrid_cube) == expected_cube


def test_regrid_to_single_point_longitude_transform_2(cube):
    """Test extracting a single point.

    Test that, if a longitude selection is made that is too
    far west (further west than -180 deg), the code corrects it
    back into the standard range (-180 deg to 180 deg).
    """
    regrid_cube = regrid.regrid_to_single_point(
        cube, 0.5, -361.5, "Nearest", boundary_margin=1
    )
    expected_cube = "<iris 'Cube' of air_temperature / (K) (time: 3)>"
    assert repr(regrid_cube) == expected_cube


def test_regrid_to_single_point_missing_coord(cube):
    """Missing coordinate raises error."""
    # Missing X coordinate.
    source = cube.copy()
    source.remove_coord("grid_longitude")
    with pytest.raises(ValueError):
        regrid.regrid_to_single_point(source, 0.5, 358.5, "Nearest", boundary_margin=1)

    # Missing Y coordinate.
    source = cube.copy()
    source.remove_coord("grid_latitude")
    with pytest.raises(ValueError):
        regrid.regrid_to_single_point(source, 0.5, 358.5, "Nearest")


def test_longitude_fix_callback_missing_coord(cube):
    """Missing coordinate raises error."""
    # Missing X coordinate.
    source = cube.copy()
    source.remove_coord("grid_longitude")
    cube_fix = read._longitude_fix_callback(source.copy(), None, None)
    assert cube_fix == source

    # Missing Y coordinate.
    source = cube.copy()
    source.remove_coord("grid_latitude")
    cube_fix = read._longitude_fix_callback(source.copy(), None, None)
    assert cube_fix == source


def test_regrid_to_single_point_unknown_crs_x(cube):
    """X coordinate reference system is unrecognised."""
    # Exchange to unsupported coordinate system.
    cube.coord("grid_longitude").coord_system = iris.coord_systems.OSGB()
    with pytest.raises(NotImplementedError):
        regrid.regrid_to_single_point(cube, 0.5, 358.5, "Nearest")


def test_regrid_to_single_point_unknown_crs_y(cube):
    """Y coordinate reference system is unrecognised."""
    # Exchange to unsupported coordinate system.
    cube.coord("grid_latitude").coord_system = iris.coord_systems.OSGB()
    with pytest.raises(NotImplementedError):
        regrid.regrid_to_single_point(cube, 0.5, 358.5, "Nearest")


def test_regrid_to_single_point_outside_domain_longitude(regrid_source_cube):
    """Error if coordinates are outside the model domain."""
    with pytest.raises(ValueError):
        regrid.regrid_to_single_point(regrid_source_cube, 0.5, 178.5, "Nearest")


def test_regrid_to_single_point_outside_domain_latitude(regrid_source_cube):
    """Error if coordinates are outside the model domain."""
    with pytest.raises(ValueError):
        regrid.regrid_to_single_point(regrid_source_cube, 80.5, 358.5, "Nearest")


@pytest.mark.filterwarnings("ignore:Selected point is within")
def test_regrid_to_single_point_unknown_method(cube):
    """Method does not exist."""
    with pytest.raises(NotImplementedError):
        regrid.regrid_to_single_point(cube, 0.5, 358.5, method="nonexistent")


@pytest.mark.filterwarnings(
    "ignore:this date/calendar/year zero convention is not supported by CF"
)
def test_boundary_warning(regrid_source_cube):
    """Ensures a warning is raised when chosen point is too close to boundary."""
    with pytest.warns(
        BoundaryWarning, match="Selected point is within 8 gridlengths"
    ) as warning:
        regrid.regrid_to_single_point(regrid_source_cube, -0.9, 393.0, "Nearest")

    assert len(warning) == 1
    assert issubclass(warning[-1].category, BoundaryWarning)
