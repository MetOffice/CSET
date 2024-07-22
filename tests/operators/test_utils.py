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

import pytest

import CSET.operators._utils as operator_utils


def test_missing_coord_get_cube_yxcoordname_x(regrid_rectilinear_cube):
    """Missing X coordinate raises error."""
    regrid_rectilinear_cube.remove_coord("longitude")
    with pytest.raises(ValueError):
        operator_utils.get_cube_yxcoordname(regrid_rectilinear_cube)


def test_missing_coord_get_cube_yxcoordname_y(regrid_rectilinear_cube):
    """Missing Y coordinate raises error."""
    regrid_rectilinear_cube.remove_coord("longitude")
    with pytest.raises(ValueError):
        operator_utils.get_cube_yxcoordname(regrid_rectilinear_cube)


def test_get_cube_yxcoordname(regrid_rectilinear_cube):
    """Check that function returns tuple containing horizontal dimension names."""
    assert (operator_utils.get_cube_yxcoordname(regrid_rectilinear_cube)) == (
        "latitude",
        "longitude",
    )


def test_is_transect_multiplespatialcoords(regrid_rectilinear_cube):
    """Check that function returns False as more than one spatial map coord."""
    assert not operator_utils.is_transect(regrid_rectilinear_cube)


def test_is_transect_noverticalcoord(transect_source_cube):
    """Check that function returns False as no vertical coord found."""
    # Retain only time and latitude coordinate, so it passes the first spatial coord test.
    transect_source_cube_slice = transect_source_cube[:, 0, :, 0]
    assert not operator_utils.is_transect(transect_source_cube_slice)


def test_is_transect_correctcoord(transect_source_cube):
    """Check that function returns True as one map and vertical coord found."""
    # Retain only time and latitude coordinate, so it passes the first spatial coord test.
    transect_source_cube_slice = transect_source_cube[:, :, :, 0]
    assert operator_utils.is_transect(transect_source_cube_slice)
