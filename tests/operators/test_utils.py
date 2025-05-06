# © Crown copyright, Met Office (2022-2025) and CSET contributors.
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
import iris.coords
import iris.cube
import pytest

import CSET.operators._utils as operator_utils


def test_missing_coord_get_cube_yxcoordname_x(regrid_rectilinear_cube):
    """Missing X coordinate raises error."""
    regrid_rectilinear_cube.remove_coord("longitude")
    regrid_rectilinear_cube.remove_coord("grid_longitude")
    with pytest.raises(ValueError):
        operator_utils.get_cube_yxcoordname(regrid_rectilinear_cube)


def test_missing_coord_get_cube_yxcoordname_y(regrid_rectilinear_cube):
    """Missing Y coordinate raises error."""
    regrid_rectilinear_cube.remove_coord("latitude")
    regrid_rectilinear_cube.remove_coord("grid_latitude")
    with pytest.raises(ValueError):
        operator_utils.get_cube_yxcoordname(regrid_rectilinear_cube)


def test_get_cube_yxcoordname(regrid_rectilinear_cube):
    """Check that function returns tuple containing horizontal dimension names."""
    assert (operator_utils.get_cube_yxcoordname(regrid_rectilinear_cube)) == (
        "latitude",
        "longitude",
    )


def test_missing_coord_get_cube_coordindex(regrid_rectilinear_cube):
    """Missing coordinate name raises error."""
    with pytest.raises(ValueError):
        operator_utils.get_cube_coordindex(regrid_rectilinear_cube, "gridded_latitude")


def test_get_cube_coordindex(regrid_rectilinear_cube):
    """Check that function returns correct dimension index for latitude and longitude."""
    assert (
        operator_utils.get_cube_coordindex(regrid_rectilinear_cube, "latitude")
    ) == 0
    assert (
        operator_utils.get_cube_coordindex(regrid_rectilinear_cube, "longitude")
    ) == 1


def test_is_transect_multiple_spatial_coords(regrid_rectilinear_cube):
    """Check that function returns False as more than one spatial map coord."""
    assert not operator_utils.is_transect(regrid_rectilinear_cube)


def test_is_transect_no_vertical_coord(transect_source_cube):
    """Check that function returns False as no vertical coord found."""
    # Retain only time and latitude coordinate, so it passes the first spatial coord test.
    transect_source_cube_slice = transect_source_cube[:, 0, :, 0]
    assert not operator_utils.is_transect(transect_source_cube_slice)


def test_is_transect_correct_coord(transect_source_cube):
    """Check that function returns True as one map and vertical coord found."""
    # Retain only time and latitude coordinate, so it passes the first spatial coord test.
    transect_source_cube_slice = transect_source_cube[:, :, :, 0]
    assert operator_utils.is_transect(transect_source_cube_slice)


def test_is_spatialdim_false(transect_source_cube):
    """Check that is spatial test returns false if cube does not contain spatial coordinates."""
    cube = transect_source_cube[:, :, 0, 0]  # Remove spatial dimcoords.
    assert not operator_utils.is_spatialdim(cube)


def test_is_spatialdim_true(transect_source_cube):
    """Check that is spatial test returns true if cube contains spatial coordinates."""
    assert operator_utils.is_spatialdim(transect_source_cube)


def test_fully_equalise_attributes_remove_unique_attributes():
    """Check unique attributes are removed."""
    original = iris.cube.Cube(
        [], var_name="variable", attributes={"shared_attribute": 1}
    )
    c1 = original.copy()
    c2 = original.copy()
    c2.attributes["unique_attribute"] = 1

    fixed_cubes = operator_utils.fully_equalise_attributes([c1, c2])
    for cube in fixed_cubes:
        assert cube == original


def test_fully_equalise_attributes_remove_differing_attributes():
    """Check attributes with different values are removed."""
    original = iris.cube.Cube(
        [], var_name="variable", attributes={"shared_attribute": 1}
    )
    c1 = original.copy()
    c2 = original.copy()
    c2.attributes["shared_attribute"] = 2

    fixed_cubes = operator_utils.fully_equalise_attributes([c1, c2])
    for cube in fixed_cubes:
        assert "shared_attribute" not in cube.attributes


def test_fully_equalise_attributes_remove_unique_coords():
    """Check unique coordinates are removed."""
    foo_coord = iris.coords.DimCoord([0], var_name="foo")
    bar_coord = iris.coords.AuxCoord([0], var_name="bar")

    original = iris.cube.Cube(
        [0], var_name="variable", dim_coords_and_dims=[(foo_coord, 0)]
    )
    c1 = original.copy()
    c2 = original.copy()
    c2.add_aux_coord(bar_coord)

    fixed_cubes = operator_utils.fully_equalise_attributes([c1, c2])
    for cube in fixed_cubes:
        assert cube.coord("foo")
        assert not cube.coords("bar")


def test_fully_equalise_attributes_equalise_coords():
    """Check differing coordinates are equalised."""
    foo_coord = iris.coords.DimCoord(
        [0], var_name="foo", attributes={"shared_attribute": 1}
    )
    original = iris.cube.Cube(
        [0], var_name="variable", dim_coords_and_dims=[(foo_coord, 0)]
    )
    c1 = original.copy()
    c2 = original.copy()
    c2.coord("foo").attributes["shared_attribute"] = 2

    fixed_cubes = operator_utils.fully_equalise_attributes([c1, c2])
    for cube in fixed_cubes:
        assert "shared_attribute" not in cube.coord("foo").attributes


def test_is_time_aggregatable_False(long_forecast):
    """Check that a cube that is not time aggregatable returns False."""
    assert not operator_utils.is_time_aggregatable(long_forecast)


def test_is_time_aggregatable(long_forecast_multi_day):
    """Check that a time aggregatable cube returns True."""
    assert operator_utils.is_time_aggregatable(long_forecast_multi_day)
