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

"""Reading operator tests."""

import datetime
import logging

import iris
import iris.coord_systems
import iris.coords
import iris.cube
import numpy as np
import pytest

from CSET.operators import read


def test_read_cubes():
    """Read cube and verify."""
    cubes = read.read_cubes("tests/test_data/air_temp.nc")
    assert len(cubes) == 3
    expected_cubes = [
        "<iris 'Cube' of air_temperature / (K) (time: 2; grid_latitude: 17; grid_longitude: 13)>",
        "<iris 'Cube' of air_temperature / (K) (time: 3; grid_latitude: 17; grid_longitude: 13)>",
    ]
    for cube in cubes:
        assert repr(cube) in expected_cubes


def test_read_cubes_no_cubes_warning():
    """Warning emitted when constraint gives no cubes."""
    with pytest.warns(UserWarning, match="No cubes loaded"):
        cubes = read.read_cubes("tests/test_data/air_temp.nc", "non-existent")
    assert len(cubes) == 0


def test_read_cubes_ensemble_with_realization_coord():
    """Read ensemble data from a single file with a realization dimension."""
    cubes = read.read_cubes("tests/test_data/exeter_ensemble_single_file.nc")
    # Check ensemble members have been merged into a single cube.
    assert len(cubes) == 1
    cube = cubes[0]
    # Check realization is an integer.
    for point in cube.coord("realization").points:
        assert isinstance(int(point), int)


def test_read_cubes_ensemble_separate_files():
    """Read ensemble from multiple files with the member number in filename."""
    from CSET.operators import constraints

    cubes = read.read_cubes(
        "tests/test_data/exeter_em*.nc",
        constraint=constraints.generate_stash_constraint("m01s03i236"),
    )
    # Check ensemble members have been merged into a single cube.
    assert len(cubes) == 1
    cube = cubes[0]
    # Check realization is an integer.
    for point in cube.coord("realization").points:
        assert isinstance(int(point), int)


def test_read_cubes_verify_comparison_base():
    """Read two paths for cubes, and check only the first is marked as base."""
    paths = [
        "tests/test_data/air_temp.nc",  # UM 11.9
        "tests/test_data/exeter_em01.nc",  # UM 13.0
    ]
    cubes = read.read_cubes(paths)
    for cube in cubes.extract(iris.AttributeConstraint(um_version="11.9")):
        assert cube.attributes["cset_comparison_base"] == 1
    for cube in cubes.extract(iris.AttributeConstraint(um_version="13.0")):
        assert "cset_comparison_base" not in cube.attributes


def test_read_cubes_incorrect_number_of_model_names():
    """Error raised when number of models names doesn't match number of paths."""
    with pytest.raises(
        ValueError,
        match=r"The number of model names \(2\) should equal the number of paths given \(1\)\.",
    ):
        read.read_cubes(
            "tests/test_data/air_temp.nc", model_names=["Model 1", "Model 2"]
        )


def test_fieldsfile_ensemble_naming():
    """Extracting the realization from the fields file naming convention."""
    cube = iris.cube.Cube([0])
    filename = "myfieldsfile_enuk_um_001/enukaa_pd000"
    read._ensemble_callback(cube, None, filename)
    assert cube.coord("realization").points[0] == 1


def test_read_cube():
    """Returns a Cube rather than CubeList."""
    from CSET.operators import constraints

    # Rotated [grid_latitude, grid_longitude] example file
    cube = read.read_cube(
        "tests/test_data/air_temp.nc",
        constraint=constraints.generate_cell_methods_constraint([]),
    )
    assert isinstance(cube, iris.cube.Cube)

    # Global [latitude, longitude] example file
    cube = read.read_cube(
        "tests/test_data/air_temperature_global.nc",
        constraint=constraints.generate_cell_methods_constraint([]),
    )
    assert isinstance(cube, iris.cube.Cube)

    # Regional [latitude, longitude] example file
    cube = read.read_cube(
        "tests/test_data/air_temperature_lat_lon.nc",
        constraint=constraints.generate_cell_methods_constraint([]),
    )
    assert isinstance(cube, iris.cube.Cube)

    # Regional [lat, lon] example across dateline
    cube = read.read_cube(
        "tests/test_data/air_temperature_dateline.nc",
        constraint=constraints.generate_cell_methods_constraint([]),
    )
    assert isinstance(cube, iris.cube.Cube)


def test_read_cube_unconstrained():
    """Error for multiple cubes read."""
    with pytest.raises(ValueError):
        read.read_cube("tests/test_data/air_temp.nc")


def test_read_cube_merge_concatenate():
    """Cubes are combined after callbacks have been applied."""
    cube = read.read_cube("tests/test_data/concat_after_fix_[12].nc")
    assert isinstance(cube, iris.cube.Cube)


def test_load_model_add_model_name():
    """Model name correctly added when given."""
    cubes = read._load_model("tests/test_data/air_temp.nc", "Test", None)
    for cube in cubes:
        assert cube.attributes["model_name"] == "Test"


def test_check_input_files_direct_path(tmp_path):
    """Get a iterable of a single file from a direct path as a string."""
    file_path = tmp_path / "file"
    file_path.touch()
    string_path = str(file_path)
    actual = read._check_input_files(string_path)
    expected = [file_path]
    assert actual == expected


def test_check_input_files_direct_path_glob(tmp_path):
    """Get a iterable of files from a direct path containing a glob pattern."""
    file1_path = tmp_path / "file1"
    file2_path = tmp_path / "file2"
    file1_path.touch()
    file2_path.touch()
    glob_path = f"{tmp_path}/file*"
    actual = read._check_input_files(glob_path)
    expected = [file1_path, file2_path]
    assert actual == expected


def test_check_input_files_direct_path_match_glob_like_file(tmp_path):
    """Get a iterable of a single file from a glob-like direct path."""
    file1_path = tmp_path / "file1"
    glob_like_path = tmp_path / "file*"
    file1_path.touch()
    glob_like_path.touch()
    actual = read._check_input_files(str(glob_like_path))
    expected = [glob_like_path]
    assert actual == expected


def test_check_input_files_input_directory(tmp_path):
    """Get a iterable of files in an input directory."""
    file1_path = tmp_path / "file1"
    file2_path = tmp_path / "file2"
    file1_path.touch()
    file2_path.touch()
    actual = read._check_input_files(str(tmp_path))
    expected = [file1_path, file2_path]
    assert actual == expected


def test_check_input_files_invalid_path(tmp_path):
    """Error when path doesn't exist."""
    file_path = str(tmp_path / "file")
    with pytest.raises(FileNotFoundError):
        read._check_input_files(file_path)


def test_check_input_files_no_file_in_directory(tmp_path):
    """Error when input directory doesn't contain any files."""
    with pytest.raises(FileNotFoundError):
        read._check_input_files(str(tmp_path))


def test_um_normalise_callback_rename_stash(cube):
    """Correctly translate from STASH to LFRic variable name."""
    read._um_normalise_callback(cube, None, None)
    actual = cube.long_name
    expected = "temperature_at_screen_level"
    assert actual == expected


def test_um_normalise_callback_missing_entry(cube, caplog):
    """Warning when STASH dictionary doesn't contain stash."""
    cube.attributes["STASH"] = "m00s00i000"
    read._um_normalise_callback(cube, None, None)
    _, level, message = caplog.record_tuples[0]
    assert level == logging.WARNING


def test_lfric_normalise_callback_remove_attrs(cube):
    """Correctly remove unneeded attributes."""
    cube.attributes["uuid"] = "87096862-89c3-4749-9c6c-0be91c2a7954"
    cube.attributes["timeStamp"] = "2024-May-20 12:29:21 GMT"
    read._lfric_normalise_callback(cube, None, None)
    assert "uuid" not in cube.attributes
    assert "timeStamp" not in cube.attributes


def test_lfric_normalise_callback_sort_stash(cube):
    """Correctly sort STASH code lists."""
    cube.attributes["um_stash_source"] = "['m01s03i025', 'm01s00i025']"
    read._lfric_normalise_callback(cube, None, None)
    actual = cube.attributes["um_stash_source"]
    expected = "['m01s00i025', 'm01s03i025']"
    assert actual == expected


def test_lfric_time_coord_fix_callback():
    """Correctly convert time from AuxCoord to DimCoord."""
    time_coord = iris.coords.AuxCoord([0, 1, 2], standard_name="time")
    cube = iris.cube.Cube([0, 0, 0], aux_coords_and_dims=[(time_coord, 0)])
    read._lfric_time_coord_fix_callback(cube, None, None)
    assert isinstance(cube.coord("time"), iris.coords.DimCoord)
    assert cube.coord_dims("time") == (0,)


def test_lfric_time_coord_fix_callback_scalar_time():
    """Correctly convert time from AuxCoord to DimCoord for scalar time."""
    length_coord = iris.coords.DimCoord([0, 1, 2], var_name="length")
    time_coord = iris.coords.AuxCoord([0], standard_name="time")
    cube = iris.cube.Cube([0, 0, 0], aux_coords_and_dims=[(length_coord, 0)])
    cube.add_aux_coord(time_coord)
    read._lfric_time_coord_fix_callback(cube, None, None)
    assert isinstance(cube.coord("time"), iris.coords.AuxCoord)
    assert cube.coord_dims("time") == ()


def test_lfric_time_coord_fix_callback_no_time():
    """Don't do anything if no time coordinate present."""
    length_coord = iris.coords.DimCoord([0, 1, 2], var_name="length")
    cube = iris.cube.Cube([0, 0, 0], aux_coords_and_dims=[(length_coord, 0)])
    read._lfric_time_coord_fix_callback(cube, None, None)
    assert len(cube.coords("time")) == 0


def test_pressure_coord_name_fix_callback(transect_source_cube):
    """Check that pressure_level is renamed to pressure if it exists."""
    cube = transect_source_cube.copy()
    cube.coord("pressure").rename("pressure_level")
    read._fix_pressure_coord_callback(cube)
    assert "pressure" in [coord.name() for coord in cube.coords()]


def test_pressure_coord_unit_fix_callback(transect_source_cube):
    """Check that pressure level units are hPa."""
    cube = transect_source_cube.copy()
    cube.coord("pressure").convert_units("Pa")
    read._fix_pressure_coord_callback(cube)
    assert str(cube.coord("pressure").units) == "hPa"
    assert cube.coord("pressure").points[0] == 100


def test_fix_um_radtime(cube):
    """Check times that are N minute past are rounded to the whole hour."""
    # Offset times by one minute.
    time_coord = cube.coord("time")
    times = time_coord.units.num2pydate(time_coord.points) + datetime.timedelta(
        minutes=1
    )
    time_coord.points = time_coord.units.date2num(times)
    # Check all times are offset.
    for time in times:
        assert time.minute == 1
    # Also offset forecast_period by one minute.
    cube.coord("forecast_period").points += 1.0 / 60.0

    # Give cube a radiation STASH code.
    cube.attributes["STASH"] = "m01s01i208"

    # Apply fix.
    read._fix_um_radtime(cube)

    # Ensure radiation times are fixed.
    rad_time_coord = cube.coord("time")
    rad_times = rad_time_coord.units.num2pydate(rad_time_coord.points)
    # Check all times are fixed.
    assert rad_times[0] == datetime.datetime(2022, 9, 21, 3, 0)
    for time in rad_times:
        assert time.minute == 0

    # Ensure radiation forecast_period values are fixed.
    rad_time_coord = cube.coord("forecast_period")
    # Check all times are fixed.
    assert rad_time_coord.points[0] == 0
    for time in rad_time_coord.points:
        assert time.dtype == int


def test_fix_um_radtime_posthour_no_fp(cube):
    """Check times that are 1 minute past are rounded, if no forecast_period."""
    # Offset times by one minute.
    time_coord = cube.coord("time")
    times = time_coord.units.num2pydate(time_coord.points) + datetime.timedelta(
        minutes=1
    )
    time_coord.points = time_coord.units.date2num(times)
    # Check all times are offset.
    for time in times:
        assert time.minute == 1
    # Remove forecast_period from input cube.
    cube.remove_coord("forecast_period")

    # Give cube a radiation STASH code.
    cube.attributes["STASH"] = "m01s01i208"

    # Apply fix.
    read._fix_um_radtime(cube)

    # Ensure radiation times are fixed.
    rad_time_coord = cube.coord("time")
    rad_times = rad_time_coord.units.num2pydate(rad_time_coord.points)
    # Check all times are fixed.
    assert rad_times[0] == datetime.datetime(2022, 9, 21, 3, 0)
    for time in rad_times:
        assert time.minute == 0
        assert time.second == 0


def test_fix_um_radtime_seconds(cube):
    """Check times that are N minute past are rounded to the whole hour."""
    # Offset times by 50 seconds.
    time_coord = cube.coord("time")
    times = time_coord.units.num2pydate(time_coord.points) + datetime.timedelta(
        seconds=50
    )
    time_coord.points = time_coord.units.date2num(times)
    # Check all times are offset.
    for time in times:
        assert time.second == 50

    # Give cube a radiation STASH code.
    cube.attributes["STASH"] = "m01s01i208"

    # Apply fix.
    read._fix_um_radtime(cube)

    # Ensure radiation times are fixed.
    rad_time_coord = cube.coord("time")
    rad_times = rad_time_coord.units.num2pydate(rad_time_coord.points)
    # Check all times are fixed.
    assert rad_times[0] == datetime.datetime(2022, 9, 21, 3, 0)
    for time in rad_times:
        assert time.minute == 0
        assert time.second == 0


def test_fix_um_radtime_skip_non_radiation(cube):
    """Check non-radiation times are NOT fixed."""
    # Offset times by one minute.
    time_coord = cube.coord("time")
    times = time_coord.units.num2pydate(time_coord.points) + datetime.timedelta(
        minutes=1
    )
    time_coord.points = time_coord.units.date2num(times)
    # Check all times are offset.
    for time in times:
        assert time.minute == 1

    # Apply fix.
    read._fix_um_radtime(cube)

    # Ensure that non-radiation cubes are unchanged.
    non_rad_time_coord = cube.coord("time")
    non_rad_times = non_rad_time_coord.units.num2pydate(non_rad_time_coord.points)
    for nrt, t in zip(non_rad_times, times, strict=True):
        assert nrt == t


def test_fix_um_radtime_skip_non_offset(cube):
    """Check radiation times NOT offset by 1 minute are not fixed."""
    time_coord = cube.coord("time")
    times = time_coord.units.num2pydate(time_coord.points)
    # Check all times are not offset.
    for time in times:
        assert time.minute == 0

    # Give cube a radiation STASH code.
    cube.attributes["STASH"] = "m01s01i208"

    # Apply fix.
    read._fix_um_radtime(cube)

    # Ensure that non-offset cubes are unchanged.
    non_offset_time_coord = cube.coord("time")
    non_offset_times = non_offset_time_coord.units.num2pydate(
        non_offset_time_coord.points
    )
    for nt, t in zip(non_offset_times, times, strict=True):
        assert nt == t


def test_fix_um_radtime_no_time_coordinate():
    """Check cubes without time coordinates are skipped without error."""
    # Create a cube with no time coordinate.
    cube = iris.cube.Cube([0], var_name="data")
    # Apply fix.
    read._fix_um_radtime(cube)
    # Check unchanged.
    assert cube == iris.cube.Cube([0], var_name="data")


def test_fix_um_radtime_prehour(cube):
    """Check times that are 1 minute ahead are rounded to the whole hour."""
    # Offset times by one minute.
    time_coord = cube.coord("time")
    times = time_coord.units.num2pydate(time_coord.points) - datetime.timedelta(
        minutes=1
    )
    time_coord.points = time_coord.units.date2num(times)
    # Check all times are offset.
    for time in times:
        assert time.minute == 59
    # Offset forecast_period by one minute.
    cube.coord("forecast_period").points -= 1.0 / 60.0

    # Give cube a radiation STASH code.
    cube.attributes["STASH"] = "m01s01i207"

    # Apply fix.
    read._fix_um_radtime(cube)

    # Ensure radiation times are fixed.
    rad_time_coord = cube.coord("time")
    rad_times = rad_time_coord.units.num2pydate(rad_time_coord.points)
    # Check all times are fixed.
    assert rad_times[0] == datetime.datetime(2022, 9, 21, 3, 0)
    for time in rad_times:
        assert time.minute == 0

    # Ensure radiation forecast_periods are fixed.
    rad_time_coord = cube.coord("forecast_period")
    # Check all times are fixed.
    assert rad_time_coord.points[0] == 0
    for time in rad_time_coord.points:
        assert time.dtype == int


def test_fix_um_radtime_prehour_no_fp(cube):
    """Check times that are 1 minute ahead are rounded, without forecast_period."""
    # Offset times by one minute.
    time_coord = cube.coord("time")
    times = time_coord.units.num2pydate(time_coord.points) - datetime.timedelta(
        minutes=1
    )
    time_coord.points = time_coord.units.date2num(times)
    # Check all times are offset.
    for time in times:
        assert time.minute == 59
    # Remove forecast_period from input.
    cube.remove_coord("forecast_period")

    # Give cube a radiation STASH code.
    cube.attributes["STASH"] = "m01s01i207"

    # Apply fix.
    read._fix_um_radtime(cube)

    # Ensure radiation times are fixed.
    rad_time_coord = cube.coord("time")
    rad_times = rad_time_coord.units.num2pydate(rad_time_coord.points)
    # Check all times are fixed.
    assert rad_times[0] == datetime.datetime(2022, 9, 21, 3, 0)
    for time in rad_times:
        assert time.minute == 0


def test_fix_um_radtime_prehour_seconds(cube):
    """Check times that are 58.50 minutes past are rounded to the whole hour."""
    # Offset times by one minute.
    time_coord = cube.coord("time")
    times = (
        time_coord.units.num2pydate(time_coord.points)
        - datetime.timedelta(minutes=1)
        - datetime.timedelta(seconds=10)
    )
    time_coord.points = time_coord.units.date2num(times)
    # Check all times are offset.
    for time in times:
        assert time.minute == 58
        assert time.second == 50

    # Give cube a radiation STASH code.
    cube.attributes["STASH"] = "m01s01i207"

    # Apply fix.
    read._fix_um_radtime(cube)

    # Ensure radiation times are fixed.
    rad_time_coord = cube.coord("time")
    rad_times = rad_time_coord.units.num2pydate(rad_time_coord.points)
    # Check all times are fixed.
    assert rad_times[0] == datetime.datetime(2022, 9, 21, 3, 0)
    for time in rad_times:
        assert time.minute == 0
        assert time.second == 0


def test_fix_um_radtime_prehour_skip_non_radiation(cube):
    """Check non-radiation times are NOT fixed."""
    # Offset times by one minute.
    time_coord = cube.coord("time")
    times = time_coord.units.num2pydate(time_coord.points) - datetime.timedelta(
        minutes=1
    )
    time_coord.points = time_coord.units.date2num(times)
    # Check all times are offset.
    for time in times:
        assert time.minute == 59

    # Apply fix.
    read._fix_um_radtime(cube)

    # Ensure that non-radiation cubes are unchanged.
    non_rad_time_coord = cube.coord("time")
    non_rad_times = non_rad_time_coord.units.num2pydate(non_rad_time_coord.points)
    for nrt, t in zip(non_rad_times, times, strict=True):
        assert nrt == t


def test_fix_cell_methods_lightning(cube):
    """Check cell_methods are adjusted."""
    # Add UM lightning STASH code.
    cube.attributes["STASH"] = "m01s21i104"
    # Set assumed time-averaged lightning diagnostic cell_method.
    cube.cell_methods = ()
    cube.add_cell_method(iris.coords.CellMethod("mean", coords="time"))
    # Apply fix.
    read._fix_cell_methods(cube)
    # Check sum cell method now applied to accumulated diagnostic.
    assert cube.cell_methods[0] == iris.coords.CellMethod(
        method="sum", coords=("time",), intervals=(), comments=()
    )


def test_fix_cell_methods_instantaneous(cube):
    """Check non aggregated inputs have CellMethod added."""
    # Remove any cell methods from input.
    cube.cell_methods = ()
    # Apply fix.
    read._fix_cell_methods(cube)
    # Check that output cell method is non-aggregated.
    assert cube.cell_methods == ()


def test_spatial_coord_auxcoord_callback():
    """Check that additional spatial aux coord grid_latitude gets added."""
    # This cube contains 'latitude' and 'longitude'
    cube = iris.load_cube("tests/test_data/transect_test_umpl.nc")
    read._fix_spatial_coords_callback(cube)
    assert (
        repr(cube.coords())
        == "[<DimCoord: time / (hours since 1970-01-01 00:00:00)  [...]  shape(2,)>, <DimCoord: pressure / (hPa)  [ 100., 150., ..., 950., 1000.]  shape(16,)>, <DimCoord: latitude / (degrees)  [-10.98, -10.94, ..., -10.82, -10.78]  shape(6,)>, <DimCoord: longitude / (degrees)  [19.02, 19.06, ..., 19.18, 19.22]  shape(6,)>, <DimCoord: forecast_reference_time / (hours since 1970-01-01 00:00:00)  [...]>, <AuxCoord: forecast_period / (hours)  [15., 18.]  shape(2,)>, <AuxCoord: grid_latitude / (degrees)  [-10.98, -10.94, ..., -10.82, -10.78]  shape(6,)>, <AuxCoord: grid_longitude / (degrees)  [19.02, 19.06, ..., 19.18, 19.22]  shape(6,)>]"
    )


def test_spatial_coord_not_exist_callback():
    """Check that spatial coord returns cube if cube does not contain spatial coordinates."""
    cube = iris.load_cube("tests/test_data/transect_test_umpl.nc")
    cube = cube[:, :, 0, 0]  # Remove spatial dimcoords
    read._fix_spatial_coords_callback(cube)
    assert (
        repr(cube.coords())
        == "[<DimCoord: time / (hours since 1970-01-01 00:00:00)  [...]  shape(2,)>, <DimCoord: pressure / (hPa)  [ 100., 150., ..., 950., 1000.]  shape(16,)>, <DimCoord: forecast_reference_time / (hours since 1970-01-01 00:00:00)  [...]>, <DimCoord: latitude / (degrees)  [-10.98]>, <DimCoord: longitude / (degrees)  [19.02]>, <AuxCoord: forecast_period / (hours)  [15., 18.]  shape(2,)>]"
    )


def test_lfric_time_callback_forecast_reference_time(slammed_lfric_cube):
    """Check that read callback creates an appropriate forecast_reference_time coord."""
    slammed_lfric_cube.remove_coord("forecast_reference_time")
    assert not slammed_lfric_cube.coords("forecast_reference_time")
    slammed_lfric_cube.coord("time").attributes["time_origin"] = "2022-01-01 00:00:00"

    read._lfric_time_callback(slammed_lfric_cube)

    ref_time_coord = slammed_lfric_cube.coord("forecast_reference_time")
    assert ref_time_coord.standard_name == "forecast_reference_time"
    assert ref_time_coord.long_name == "forecast_reference_time"
    assert ref_time_coord.var_name is None
    assert str(ref_time_coord.units) == "hours since 1970-01-01 00:00:00"
    assert all(ref_time_coord.points == [455832])


def test_lfric_time_callback_forecast_period(slammed_lfric_cube):
    """Check that read callback creates an appropriate forecast_period dimension."""
    slammed_lfric_cube.remove_coord("forecast_period")
    assert not slammed_lfric_cube.coords("forecast_period")

    read._lfric_time_callback(slammed_lfric_cube)

    fc_period_coord = slammed_lfric_cube.coord("forecast_period")
    assert fc_period_coord.standard_name == "forecast_period"
    assert fc_period_coord.long_name == "forecast_period"
    assert fc_period_coord.var_name is None
    assert str(fc_period_coord.units) == "hours"
    assert all(fc_period_coord.points == [1, 2, 3, 4, 5, 6])


def test_lfric_time_callback_hours(slammed_lfric_cube):
    """Check hours are set as forecast_period units."""
    slammed_lfric_cube.remove_coord("forecast_period")
    assert not slammed_lfric_cube.coords("forecast_period")
    slammed_lfric_cube.coord("time").convert_units("hours since 1970-01-01 00:00:00")

    read._lfric_time_callback(slammed_lfric_cube)

    fc_period_coord = slammed_lfric_cube.coord("forecast_period")
    assert str(fc_period_coord.units) == "hours"
    assert all(fc_period_coord.points == [1, 2, 3, 4, 5, 6])


def test_lfric_time_callback_unknown_units(slammed_lfric_cube, caplog):
    """Error when forecast_period units cannot be determined."""
    slammed_lfric_cube.remove_coord("forecast_period")
    assert not slammed_lfric_cube.coords("forecast_period")
    slammed_lfric_cube.coord("time").units = None

    with pytest.raises(iris.exceptions.UnitConversionError):
        read._lfric_time_callback(slammed_lfric_cube)
        _, level, message = caplog.record_tuples[0]
        assert level == logging.ERROR
        assert message == "Unrecognised base time unit: unknown"


def test_fix_lfric_cloud_base_altitude():
    """Check that lfric cloud_base_altitude callback applies mask."""
    cube = iris.cube.Cube(np.arange(151), long_name="cloud_base_altitude")
    assert np.max(cube.data) == 150.0
    # Apply fix callback to mask > 144kft.
    read._fix_lfric_cloud_base_altitude(cube)
    assert np.max(cube.data) == 144.0


def test_fix_lfric_cloud_base_altitude_non_cloud_var():
    """Check that lfric cloud_base_altitude callback has no impact on other variables."""
    cube = iris.cube.Cube(np.arange(151), long_name="air_temperature")
    assert np.max(cube.data) == 150.0
    # Apply fix callback.
    read._fix_lfric_cloud_base_altitude(cube)
    assert np.max(cube.data) == 150.0


def test_normalise_var0_varname(model_level_cube):
    """Check that read callback renames the model level var name."""
    model_level_cube.coord("model_level_number").var_name = "model_level_number_0"
    read._normalise_var0_varname(model_level_cube)
    assert model_level_cube.coord("model_level_number").var_name == "model_level_number"


def test_lfric_forecast_period_standard_name_callback(cube):
    """Ensure forecast period coordinates have a standard name."""
    cube.coord("forecast_period").standard_name = None
    read._lfric_forecast_period_standard_name_callback(cube)
    assert cube.coord("forecast_period").standard_name == "forecast_period"


def test_read_cubes_extract_cells():
    """Read cube and ensure appropriate number of cells are trimmed from domain edges."""
    cube = read.read_cubes(
        "tests/test_data/air_temperature_1000_hpa_level_histogram_plot.nc"
    )[0]
    assert cube.shape == (420, 380)

    # Test not trimming any cells.
    cube_full = read.read_cubes(
        "tests/test_data/air_temperature_1000_hpa_level_histogram_plot.nc",
        subarea_type="gridcells",
        subarea_extent=[0, 0, 0, 0],
    )[0]
    assert cube_full.shape == (420, 380)

    # Test trimming same number of grid points in all directions
    cube_all = read.read_cubes(
        "tests/test_data/air_temperature_1000_hpa_level_histogram_plot.nc",
        subarea_type="gridcells",
        subarea_extent=[10, 10, 10, 10],
    )[0]
    assert cube_all.shape == (400, 360)
    assert round(cube_all.data[0, 0], 2) == round(cube.data[10, 10], 2)
    assert round(cube_all.data[-1, -1], 2) == round(cube.data[409, 369], 2)

    # Test trimming lower and upper edges only
    cube_tb = read.read_cubes(
        "tests/test_data/air_temperature_1000_hpa_level_histogram_plot.nc",
        subarea_type="gridcells",
        subarea_extent=[15, 0, 15, 0],
    )[0]
    assert cube_tb.shape == (390, 380)
    assert round(cube_tb.data[0, 0], 2) == round(cube.data[15, 0], 2)
    assert round(cube_tb.data[-1, -1], 2) == round(cube.data[389, 379], 2)

    # Test trimming left and right edges only
    cube_lr = read.read_cubes(
        "tests/test_data/air_temperature_1000_hpa_level_histogram_plot.nc",
        subarea_type="gridcells",
        subarea_extent=[0, 15, 0, 15],
    )[0]
    assert cube_lr.shape == (420, 350)
    assert round(cube_lr.data[0, 0], 2) == round(cube.data[0, 15], 2)
    assert round(cube_lr.data[-1, -1], 2) == round(cube.data[419, 364], 2)

    # Test trimming lower-side only
    cube_lo = read.read_cubes(
        "tests/test_data/air_temperature_1000_hpa_level_histogram_plot.nc",
        subarea_type="gridcells",
        subarea_extent=[100, 0, 0, 0],
    )[0]
    assert cube_lo.shape == (320, 380)
    assert round(cube_lo.data[0, 0], 2) == round(cube.data[100, 0], 2)
    assert round(cube_lo.data[-1, -1], 2) == round(cube.data[419, 379], 2)


def test_read_cubes_extract_subarea():
    """Read cube and ensure appropriate subarea is extracted."""
    # All cubes are on same grid, and vary by cell method.
    cube = read.read_cubes("tests/test_data/air_temp.nc")[0]
    assert cube.coord("grid_latitude").coord_system == iris.coord_systems.RotatedGeogCS(
        37.5, 177.5, ellipsoid=iris.coord_systems.GeogCS(6371229.0)
    )
    assert round(cube.coord("grid_latitude").points[0], 2) == -3.76
    assert round(cube.coord("grid_latitude").points[-1], 2) == 7.04
    assert round(cube.coord("grid_longitude").points[0], 2) == -5.06
    assert round(cube.coord("grid_longitude").points[-1], 2) == 3.04

    # Now load the cube and extract model relative latitude bound -2 to 0, and
    # longitude bound -2 to 0 The data is coarse, so the intersection will bring
    # the nearest grid point to the cutout, hence edge coordinates do not match
    # bounds.
    cube_mr = read.read_cubes(
        "tests/test_data/air_temp.nc",
        subarea_type="modelrelative",
        subarea_extent=[-2, 0, -2, 0],
    )[0]

    # Repeat for real world coordinates, using latitude bound 50.5 to 52.5 and
    # longitude bound -4.5 to -2.5 We know from above the rotated pole is 37.5N,
    # so we need to add 52.5 to the model relative latitudes to extract the same
    # latitude band.
    cube_rw = read.read_cubes(
        "tests/test_data/air_temp.nc",
        subarea_type="realworld",
        subarea_extent=[50.5, 52.5, -4.5, -2.5],
    )[0]

    # Compare the latitude coordinates to check its extracted same region. We
    # use latitude as there is little difference in spacing from the equator to
    # pole, but longitude varies (converges to zero at pole).
    assert np.array_equal(
        cube_mr.coord("grid_latitude").points, cube_rw.coord("grid_latitude").points
    )
    # Check we actually extracted an area.
    assert not np.array_equal(
        cube_rw.coord("grid_latitude").points, cube.coord("grid_latitude").points
    )


def test_read_cubes_extract_subarea_latlon():
    """Read cube with latlon coord and ensure appropriate subarea is extracted."""
    # Read in global test data
    cube = read.read_cubes("tests/test_data/air_temperature_global.nc")[0]
    assert cube.coord("latitude").coord_system == iris.coord_systems.GeogCS(6371229.0)

    # Cutout real world coordinates, using latitude bound -30.0 to 30.0 and
    # longitude bound -4.5 to -2.5
    cube_rw = read.read_cubes(
        "tests/test_data/air_temperature_global.nc",
        subarea_type="realworld",
        subarea_extent=[-30.0, 30.0, -4.5, -2.5],
    )[0]
    assert isinstance(cube_rw, iris.cube.Cube)

    # Compare the latitude coordinates to check it has extracted same region. We
    # use latitude as there is little difference in spacing from the equator to
    # pole, but longitude varies (converges to zero at pole).
    assert not np.array_equal(
        cube_rw.coord("latitude").points, cube.coord("latitude").points
    )

    # Ensure extracted region has required coordinates
    assert round(cube_rw.coord("latitude").points[0], 2) == -28.08
    assert round(cube_rw.coord("latitude").points[-1], 2) == 28.17
    assert np.size(cube_rw.coord("longitude")) == 1
    assert round(cube_rw.coord("longitude").points[0], 2) == -2.74


def test_read_cubes_extract_subarea_outside_bounds():
    """Read cube requesting subarea outside +/-180 and wrap request within bounds."""
    cube = read.read_cubes("tests/test_data/air_temperature_global.nc")[0]
    cube_rw = read.read_cubes(
        "tests/test_data/air_temperature_global.nc",
        subarea_type="realworld",
        subarea_extent=[-30.0, 30.0, -544.5, -542.5],
    )[0]
    assert isinstance(cube_rw, iris.cube.Cube)

    # Compare the latitude coordinates to check it has extracted same region. We
    # use latitude as there is little difference in spacing from the equator to
    # pole, but longitude varies (converges to zero at pole).
    assert not np.array_equal(
        cube_rw.coord("latitude").points, cube.coord("latitude").points
    )

    # Ensure extracted region has required coordinates
    assert round(cube_rw.coord("latitude").points[0], 2) == -28.08
    assert round(cube_rw.coord("latitude").points[-1], 2) == 28.17
    assert np.size(cube_rw.coord("longitude")) == 1
    assert round(cube_rw.coord("longitude").points[0], 2) == -2.74


def test_read_cubes_extract_subarea_dateline():
    """Read cube with latlon coord across dateline and ensure appropriate subarea is extracted."""
    cube = read.read_cubes("tests/test_data/air_temperature_dateline.nc")[0]
    assert cube.coord("latitude").coord_system == iris.coord_systems.GeogCS(6371229.0)

    # Cutout real world coordinates, using latitude bound -40.0 to -35.0 and
    # longitude bound 175.0 to 181.0
    cube_rw = read.read_cubes(
        "tests/test_data/air_temperature_dateline.nc",
        subarea_type="realworld",
        subarea_extent=[-40.0, -35.0, 175.0, 181.0],
    )[0]
    assert isinstance(cube_rw, iris.cube.Cube)

    # Compare the longitude coordinates to check it has extracted a region.
    assert not np.array_equal(
        cube_rw.coord("latitude").points, cube.coord("latitude").points
    )

    # Ensure extracted region has required coordinates
    assert round(cube_rw.coord("latitude").points[0], 2) == -39.83
    assert round(cube_rw.coord("latitude").points[-1], 2) == -35.24
    assert round(cube_rw.coord("longitude").points[0], 2) == -4.83
    assert round(cube_rw.coord("longitude").points[-1], 2) == 0.84

    # Cutout real world coordinates, using latitude bound -40.0 to -35.0 and
    # longitude bound -5.0 to 1.0
    cube_rw_2 = read.read_cubes(
        "tests/test_data/air_temperature_dateline.nc",
        subarea_type="realworld",
        subarea_extent=[-40.0, -35.0, -5.0, 1.0],
    )[0]
    assert isinstance(cube_rw_2, iris.cube.Cube)

    # Compare the longitude coordinates to check it has extracted a region.
    assert not np.array_equal(
        cube_rw_2.coord("latitude").points, cube.coord("latitude").points
    )

    # Ensure extracted region has required coordinates
    assert round(cube_rw_2.coord("latitude").points[0], 2) == -39.83
    assert round(cube_rw_2.coord("latitude").points[-1], 2) == -35.24
    assert round(cube_rw_2.coord("longitude").points[0], 2) == -4.83
    assert round(cube_rw_2.coord("longitude").points[-1], 2) == 0.84


def test_read_cubes_outofbounds_subarea():
    """Ensure correct failure if subarea outside cube extent."""
    with pytest.raises(
        ValueError,
        match=r"Cutout region requested should be within data area. "
        "Check and update SUBAREA_EXTENT.",
    ):
        read.read_cubes(
            "tests/test_data/air_temp.nc",
            subarea_type="realworld",
            subarea_extent=[-5.5, 5.5, -125.5, 125.5],
        )[0]

    with pytest.raises(
        ValueError,
        match=r"Cutout region requested should be within data area. "
        "Check and update SUBAREA_EXTENT.",
    ):
        read.read_cubes(
            "tests/test_data/air_temperature_dateline.nc",
            subarea_type="realworld",
            subarea_extent=[-5.5, 5.5, -125.5, 125.5],
        )[0]


def test_read_cubes_unknown_subarea_method():
    """Ensure correct failure if invalid subarea method requested."""
    with pytest.raises(
        ValueError,
        match=r"('Unknown subarea_type:', 'any_old_method')",
    ):
        read.read_cubes(
            "tests/test_data/air_temp.nc",
            subarea_type="any_old_method",
            subarea_extent=[-5.5, 5.5, -125.5, 125.5],
        )[0]
