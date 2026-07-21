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

from datetime import timedelta

import iris
import iris.coords
import iris.cube
import numpy as np
import pytest
from iris.time import PartialDateTime

import CSET.operators._utils as operator_utils


def test_pdt_fromisoformat_returns_pdt():
    """Output of the operator_utils.pdt_fromisoformat() function is a PartialDateTime."""
    pdt, offset = operator_utils.pdt_fromisoformat("2022-01-01")
    assert isinstance(pdt, PartialDateTime)
    assert offset is None


def test_year_month_day_parse_correctly():
    """The operator_utils.pdt_fromisoformat() function correctly parses out the year, month, day coordinates."""
    pdt, offset = operator_utils.pdt_fromisoformat("2022-01-01")
    assert pdt.year == 2022
    assert pdt.month == 1
    assert pdt.day == 1
    assert pdt.hour == 0
    assert pdt.minute == 0
    assert pdt.second == 0
    assert offset is None


def test_hour_parse_correctly():
    """The operator_utils.pdt_fromisoformat() function correctly parses out only the hour coordinate."""
    pdt, offset = operator_utils.pdt_fromisoformat("2022-01-01T12")
    assert pdt.year == 2022
    assert pdt.month == 1
    assert pdt.day == 1
    assert pdt.hour == 12
    assert pdt.minute == 0
    assert pdt.second == 0
    assert offset is None


def test_hour_minute_parse_correctly():
    """The operator_utils.pdt_fromisoformat() function correctly parses out only the hour and minute coordinate."""
    pdt, offset = operator_utils.pdt_fromisoformat("2022-01-01T12:30")
    assert pdt.year == 2022
    assert pdt.month == 1
    assert pdt.day == 1
    assert pdt.hour == 12
    assert pdt.minute == 30
    assert pdt.second == 0
    assert offset is None


def test_hour_minute_second_parse_correctly():
    """The operator_utils.pdt_fromisoformat() function correctly parses out hour, minute and second coordinates."""
    pdt, offset = operator_utils.pdt_fromisoformat("2022-01-01T12:30:45")
    assert pdt.year == 2022
    assert pdt.month == 1
    assert pdt.day == 1
    assert pdt.hour == 12
    assert pdt.minute == 30
    assert pdt.second == 45
    assert offset is None


def test_basic_year_month_parse_correctly():
    """The operator_utils.pdt_fromisoformat() function correctly parses out the year and month coordinates for a basic format."""
    pdt, offset = operator_utils.pdt_fromisoformat("202201")
    assert pdt.year == 2022
    assert pdt.month == 1
    assert pdt.day is None
    assert pdt.hour is None
    assert pdt.minute is None
    assert pdt.second is None
    assert offset is None


def test_basic_year_month_day_parse_correctly():
    """The operator_utils.pdt_fromisoformat() function correctly parses out the year, month, day coordinates for a basic format."""
    pdt, offset = operator_utils.pdt_fromisoformat("20220101")
    assert pdt.year == 2022
    assert pdt.month == 1
    assert pdt.day == 1
    assert pdt.hour == 0
    assert pdt.minute == 0
    assert pdt.second == 0
    assert offset is None


def test_basic_with_time_hour_minute_second_parse_correctly():
    """The operator_utils.pdt_fromisoformat() function correctly parses out hour, minute and second coordinates for a basic format."""
    pdt, offset = operator_utils.pdt_fromisoformat("20220101T123030")
    assert pdt.year == 2022
    assert pdt.month == 1
    assert pdt.day == 1
    assert pdt.hour == 12
    assert pdt.minute == 30
    assert pdt.second == 30
    assert offset is None


def test_microseconds_parse_correctly():
    """The operator_utils.pdt_fromisoformat() function correctly removes microsecond resolution."""
    pdt, offset = operator_utils.pdt_fromisoformat("2022-01-01T12:30:30.123456")
    assert pdt.year == 2022
    assert pdt.month == 1
    assert pdt.day == 1
    assert pdt.hour == 12
    assert pdt.minute == 30
    assert pdt.second == 30
    assert offset is None


def test_month_precision_parse_correctly():
    """The operator_utils.pdt_fromisoformat() function correctly parses out the year and month coordinates."""
    pdt, offset = operator_utils.pdt_fromisoformat("2022-01")
    assert pdt.year == 2022
    assert pdt.month == 1
    assert pdt.day is None
    assert pdt.hour is None
    assert pdt.minute is None
    assert pdt.second is None
    assert offset is None


def test_alternate_UTC_representation():
    """The operator_utils.pdt_fromisoformat() function correctly removes offset of +-00:00."""
    pdt, offset = operator_utils.pdt_fromisoformat("2022-01-01T12:30+00:00")
    assert pdt.year == 2022
    assert pdt.month == 1
    assert pdt.day == 1
    assert pdt.hour == 12
    assert pdt.minute == 30
    assert pdt.second == 0
    assert offset == timedelta(0)


def test_Indian_standard_time():
    """The operator_utils.pdt_fromisoformat() function correctly parses the offset."""
    pdt, offset = operator_utils.pdt_fromisoformat("2022-01-01T12:30+05:30")
    assert pdt.year == 2022
    assert pdt.month == 1
    assert pdt.day == 1
    assert pdt.hour == 12
    assert pdt.minute == 30
    assert pdt.second == 0
    assert offset == timedelta(seconds=19800)


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
    # Error when coord name isn't in cube.
    with pytest.raises(ValueError):
        operator_utils.get_cube_coordindex(regrid_rectilinear_cube, "no-existent")


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


def test_is_coordim_false(transect_source_cube):
    """Check that is coorddim test returns false if cube does not contain specified spatial coordinate."""
    assert not operator_utils.is_coorddim(transect_source_cube, "realization")


def test_is_coordim_true(transect_source_cube):
    """Check that is coorddim test returns true if cube contains specified spatial coordinate."""
    assert operator_utils.is_coorddim(transect_source_cube, "latitude")


def test_valid_stamp_coord_in_cube(cube):
    """Check that stamp coordinate remains realization as in cube."""
    # Test that realization cube is correctly identified in cube.
    assert operator_utils.check_stamp_coordinate(cube) == "realization"


def test_valid_stamp_coord_not_in_cube(cube):
    """Check that stamp coordinate defaults to realization if not in cube."""
    cube.remove_coord("realization")
    assert operator_utils.check_stamp_coordinate(cube) == "realization"


def test_valid_stamp_coord_in_cube_valid():
    """Check that alternative valid stamp coordinate identified if in cube."""
    for stamp in ["realization", "member", "pseudo_level"]:
        foo_coord = iris.coords.DimCoord([0], var_name=stamp)
        original = iris.cube.Cube(
            [0], var_name="variable", dim_coords_and_dims=[(foo_coord, 0)]
        )
        assert operator_utils.check_stamp_coordinate(original) == stamp


def test_valid_stamp_coord_in_cube_nonvalid():
    """Check that alternative nonvalid stamp coordinate defaults."""
    for stamp in ["really", "memb", "pseudo"]:
        foo_coord = iris.coords.DimCoord([0], var_name=stamp)
        original = iris.cube.Cube(
            [0], var_name="variable", dim_coords_and_dims=[(foo_coord, 0)]
        )
        assert operator_utils.check_stamp_coordinate(original) == "realization"


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


def test_slice_over_maybe_False():
    """Check that a missing cube returns None."""
    assert operator_utils.slice_over_maybe(None, "time", 0) is None


def test_slice_over_deterministic(long_forecast):
    """Check that a sliced cube is returned."""
    assert operator_utils.slice_over_maybe(long_forecast, "time", 0) == long_forecast[0]
    assert (
        operator_utils.slice_over_maybe(long_forecast, "time", 10) == long_forecast[10]
    )


def test_slice_over_ensemble(long_forecast):
    """Check that a slice cube is returned from multi-time ensemble inputs."""
    ensemble_cube_em01 = long_forecast.copy()
    ensemble_cube_em02 = long_forecast.copy()
    ensemble_cube_em02.coord("realization").points = 1
    ensemble_cube_4d = iris.cube.CubeList(
        [ensemble_cube_em01, ensemble_cube_em02]
    ).merge_cube()
    # Attempt to extract time slice index 20 from 4D ensemble cube
    assert (
        operator_utils.slice_over_maybe(ensemble_cube_4d, "time", 20)
        == ensemble_cube_4d[:, 20, :, :]
    )
    # Attempt to extract realization index 1 from 4D ensemble cube
    assert (
        operator_utils.slice_over_maybe(ensemble_cube_4d, "realization", 1)
        == ensemble_cube_4d[1, :, :, :]
    )


def test_slice_over_non_coorddim():
    """Check that slice over without coordinate dimension leaves input unaffected."""
    foo_coord = iris.coords.AuxCoord(
        [0], var_name="foo", attributes={"shared_attribute": 1}
    )
    cube = iris.cube.Cube(
        [0], var_name="variable", aux_coords_and_dims=[(foo_coord, 0)]
    )
    assert operator_utils.slice_over_maybe(cube, "foo", 0) == cube


def test_is_time_aggregatable_False(cardington_cube):
    """Check that a cube that is not time aggregatable returns False."""
    assert not operator_utils.is_time_aggregatable(cardington_cube)


def test_is_time_aggregatable(long_forecast_multi_day):
    """Check that a time aggregatable cube returns True."""
    assert operator_utils.is_time_aggregatable(long_forecast_multi_day)


def test_get_common_time_cubes(transect_source_cube):
    """Check that only common time points are returned."""
    cubelist = iris.cube.CubeList(
        [transect_source_cube[1:], transect_source_cube[:]]
    ).extract_overlapping("time")
    assert cubelist[0].coord("time").points == np.array([449472.0])


def test_check_single_cube():
    """Conversion to a single cube, and rejection where not possible."""
    cube = iris.cube.Cube([0.0])
    cubelist = iris.cube.CubeList([cube])
    long_cubelist = iris.cube.CubeList([cube, cube])
    non_cube = 1
    assert operator_utils.check_single_cube(cube) == cube
    assert operator_utils.check_single_cube(cubelist) == cube
    with pytest.raises(ValueError, match="CubeList did not contain a single cube."):
        operator_utils.check_single_cube(long_cubelist)
    with pytest.raises(
        TypeError,
        match="check_single_cube requires a Cube or CubeList of a single cube.",
    ):
        operator_utils.check_single_cube(non_cube)


def test_get_num_models_single_cube_with_model_name():
    """Test get_num_models with a single cube containing a model name."""
    cube = iris.cube.Cube([0.0])
    cube.attributes["model_name"] = "model_1"
    assert operator_utils.get_num_models(cube) == 1


def test_get_num_models_single_cube_without_model_name():
    """Test get_num_models with a single cube without a model name."""
    cube = iris.cube.Cube([0.0])
    assert operator_utils.get_num_models(cube) == 1


def test_get_num_models_cubelist_multiple_models():
    """Test get_num_models with a CubeList containing multiple models."""
    cube1 = iris.cube.Cube([0.0])
    cube1.attributes["model_name"] = "model_1"
    cube2 = iris.cube.Cube([1.0])
    cube2.attributes["model_name"] = "model_2"
    cubelist = iris.cube.CubeList([cube1, cube2])
    assert operator_utils.get_num_models(cubelist) == 2


def test_get_num_models_cubelist_duplicate_model_names():
    """Test get_num_models with a CubeList containing duplicate model names."""
    cube1 = iris.cube.Cube([0.0])
    cube1.attributes["model_name"] = "model_1"
    cube2 = iris.cube.Cube([1.0])
    cube2.attributes["model_name"] = "model_1"
    cubelist = iris.cube.CubeList([cube1, cube2])
    assert operator_utils.get_num_models(cubelist) == 1


def test_get_num_models_cubelist_mixed_with_none():
    """Test get_num_models with a CubeList where some cubes lack model names."""
    cube1 = iris.cube.Cube([0.0])
    cube1.attributes["model_name"] = "model_1"
    cube2 = iris.cube.Cube([1.0])
    # cube2 has no model_name attribute
    cubelist = iris.cube.CubeList([cube1, cube2])
    assert operator_utils.get_num_models(cubelist) == 2


def test_get_num_models_cubelist_all_none():
    """Test get_num_models with a CubeList where no cubes have model names."""
    cube1 = iris.cube.Cube([0.0])
    cube2 = iris.cube.Cube([1.0])
    cubelist = iris.cube.CubeList([cube1, cube2])
    assert operator_utils.get_num_models(cubelist) == 1


def test_get_num_models_cubelist_three_models():
    """Test get_num_models with a CubeList containing three different models."""
    cube1 = iris.cube.Cube([0.0])
    cube1.attributes["model_name"] = "model_A"
    cube2 = iris.cube.Cube([1.0])
    cube2.attributes["model_name"] = "model_B"
    cube3 = iris.cube.Cube([2.0])
    cube3.attributes["model_name"] = "model_C"
    cubelist = iris.cube.CubeList([cube1, cube2, cube3])
    assert operator_utils.get_num_models(cubelist) == 3


def test_validate_cube_shape_single_cube_matches():
    """Test _validate_cube_shape when a single cube matches num_models=1."""
    cube = iris.cube.Cube([0.0])
    # Should not raise any exception
    operator_utils.validate_cube_shape(cube, 1)


def test_validate_cube_shape_cubelist_matches():
    """Test _validate_cube_shape when CubeList length matches num_models."""
    cube1 = iris.cube.Cube([0.0])
    cube2 = iris.cube.Cube([1.0])
    cubelist = iris.cube.CubeList([cube1, cube2])
    # Should not raise any exception
    operator_utils.validate_cube_shape(cubelist, 2)


def test_validate_cube_shape_cubelist_mismatch():
    """Test _validate_cube_shape when CubeList length does not match num_models."""
    cube1 = iris.cube.Cube([0.0])
    cube2 = iris.cube.Cube([1.0])
    cubelist = iris.cube.CubeList([cube1, cube2])
    # Should raise ValueError because 2 cubes != 3 models
    with pytest.raises(
        ValueError,
        match=r"The number of model names \(3\) should equal the number of cubes \(2\).",
    ):
        operator_utils.validate_cube_shape(cubelist, 3)


def test_validate_cube_shape_cubelist_more_cubes_than_models():
    """Test _validate_cube_shape when CubeList has more cubes than models."""
    cube1 = iris.cube.Cube([0.0])
    cube2 = iris.cube.Cube([1.0])
    cube3 = iris.cube.Cube([2.0])
    cubelist = iris.cube.CubeList([cube1, cube2, cube3])
    # Should raise ValueError because 3 cubes != 1 model
    with pytest.raises(
        ValueError,
        match=r"The number of model names \(1\) should equal the number of cubes \(3\).",
    ):
        operator_utils.validate_cube_shape(cubelist, 1)


def test_validate_cube_shape_cubelist_zero_models():
    """Test _validate_cube_shape when num_models is zero."""
    cube1 = iris.cube.Cube([0.0])
    cubelist = iris.cube.CubeList([cube1])
    # Should raise ValueError because 1 cube != 0 models
    with pytest.raises(
        ValueError,
        match=r"The number of model names \(0\) should equal the number of cubes \(1\).",
    ):
        operator_utils.validate_cube_shape(cubelist, 0)


def test_validate_cubes_coords_matching_lengths():
    """Test _validate_cubes_coords when number of cubes matches number of coords."""
    cube1 = iris.cube.Cube([0.0])
    cube2 = iris.cube.Cube([1.0])
    cubes = iris.cube.CubeList([cube1, cube2])

    coord1 = iris.coords.DimCoord([1, 2, 3], standard_name="time")
    coord2 = iris.coords.DimCoord([4, 5, 6], standard_name="time")
    coords = [coord1, coord2]

    # Should not raise any exception
    operator_utils.validate_cubes_coords(cubes, coords)


def test_validate_cubes_coords_mismatch_more_cubes():
    """Test _validate_cubes_coords when there are more cubes than coords."""
    cube1 = iris.cube.Cube([0.0])
    cube2 = iris.cube.Cube([1.0])
    cube3 = iris.cube.Cube([2.0])
    cubes = iris.cube.CubeList([cube1, cube2, cube3])

    coord1 = iris.coords.DimCoord([1, 2, 3], standard_name="time")
    coord2 = iris.coords.DimCoord([4, 5, 6], standard_name="time")
    coords = [coord1, coord2]

    # Should raise ValueError because 3 cubes != 2 coords
    with pytest.raises(ValueError, match="should equal the number"):
        operator_utils.validate_cubes_coords(cubes, coords)


def test_validate_cubes_coords_mismatch_more_coords():
    """Test _validate_cubes_coords when there are more coords than cubes."""
    cube1 = iris.cube.Cube([0.0])
    cube2 = iris.cube.Cube([1.0])
    cubes = iris.cube.CubeList([cube1, cube2])

    coord1 = iris.coords.DimCoord([1, 2, 3], standard_name="time")
    coord2 = iris.coords.DimCoord([4, 5, 6], standard_name="time")
    coord3 = iris.coords.DimCoord([7, 8, 9], standard_name="time")
    coords = [coord1, coord2, coord3]

    # Should raise ValueError because 2 cubes != 3 coords
    with pytest.raises(ValueError, match="should equal the number"):
        operator_utils.validate_cubes_coords(cubes, coords)


def test_validate_cubes_coords_single_cube_single_coord():
    """Test _validate_cubes_coords with a single cube and single coord."""
    cube = iris.cube.Cube([0.0])
    cubes = iris.cube.CubeList([cube])

    coord = iris.coords.DimCoord([1, 2, 3], standard_name="time")
    coords = [coord]

    # Should not raise any exception
    operator_utils.validate_cubes_coords(cubes, coords)


def test_validate_cubes_coords_empty_lists():
    """Test _validate_cubes_coords with empty lists."""
    cubes = iris.cube.CubeList([])
    coords = []

    # Should not raise any exception
    operator_utils.validate_cubes_coords(cubes, coords)


def test_validate_cubes_coords_large_matching_lists():
    """Test _validate_cubes_coords with larger matching lists."""
    cubes = iris.cube.CubeList([iris.cube.Cube([float(i)]) for i in range(5)])
    coords = [
        iris.coords.DimCoord([1, 2, 3], standard_name="time"),
        iris.coords.DimCoord([4, 5, 6], standard_name="time"),
        iris.coords.DimCoord([7, 8, 9], standard_name="time"),
        iris.coords.DimCoord([10, 11, 12], standard_name="time"),
        iris.coords.DimCoord([13, 14, 15], standard_name="time"),
    ]

    # Should not raise any exception
    operator_utils.validate_cubes_coords(cubes, coords)


def test_validate_cubes_coords_error_message_format():
    """Test that _validate_cubes_coords error message contains correct counts."""
    cube1 = iris.cube.Cube([0.0])
    cube2 = iris.cube.Cube([1.0])
    cubes = iris.cube.CubeList([cube1, cube2])

    coord = iris.coords.DimCoord([1, 2, 3], standard_name="time")
    coords = [coord]

    # Check error message contains both counts
    with pytest.raises(
        ValueError,
        match=r"The number of CubeList entries \(2\) should equal the number of sequence coordinates \(1\)",
    ):
        operator_utils.validate_cubes_coords(cubes, coords)


def test_validate_cubes_coords_error_message_includes_advice():
    """Test that error message includes advice about time averaging."""
    cube1 = iris.cube.Cube([0.0])
    cube2 = iris.cube.Cube([1.0])
    cube3 = iris.cube.Cube([2.0])
    cubes = iris.cube.CubeList([cube1, cube2, cube3])

    coord1 = iris.coords.DimCoord([1, 2, 3], standard_name="time")
    coord2 = iris.coords.DimCoord([4, 5, 6], standard_name="time")
    coords = [coord1, coord2]

    # Check error message includes advice about time entries
    with pytest.raises(ValueError, match="Check that number of time entries"):
        operator_utils.validate_cubes_coords(cubes, coords)


def test_valid_sequence_coord_in_cube(cube):
    """Check that sequence coordinate found in cube in cube."""
    # Test that realization cube is correctly identified in cube.
    operator_utils.check_sequence_coordinate(cube, "time")


def test_valid_sequence_coord_not_in_cube(cube):
    """Check that error raised if sequence coordinate not in cube."""
    with pytest.raises(ValueError, match="Cube must have a dummy coordinate"):
        operator_utils.check_sequence_coordinate(cube, "dummy")


def test_check_if_cylc_workflow_true(monkeypatch, tmp_path):
    """Check that running in Cylc returns True and Path."""
    # Create mock environment variable
    monkeypatch.setenv("ROSE_DATAC", str(tmp_path))

    assert operator_utils.check_if_cylc_workflow() == tmp_path


def test_check_if_cylc_workflow_no_dir(monkeypatch, tmp_path):
    """Test ROSE_DATAC present but no dir."""
    # Create mock environment variable
    monkeypatch.setenv("ROSE_DATAC", str(tmp_path) + "/foo/")

    assert operator_utils.check_if_cylc_workflow() is None


def test_check_if_cylc_workflow_false(monkeypatch, tmp_path):
    """Test no ROSE_DATAC present."""
    assert operator_utils.check_if_cylc_workflow() is None
