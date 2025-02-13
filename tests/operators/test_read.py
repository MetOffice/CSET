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

"""Reading operator tests."""

import logging

import iris
import iris.coords
import iris.cube
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
        "tests/test_data/",
        constraint=constraints.generate_stash_constraint("m01s03i236"),
        filename_pattern="exeter_em*.nc",
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


def test_fieldsfile_ensemble_naming():
    """Extracting the realization from the fields file naming convention."""
    cube = iris.cube.Cube([0])
    filename = "myfieldsfile_enuk_um_001/enukaa_pd000"
    read._ensemble_callback(cube, None, filename)
    assert cube.coord("realization").points[0] == 1


def test_read_cube():
    """Returns a Cube rather than CubeList."""
    from CSET.operators import constraints

    cube = read.read_cube(
        "tests/test_data/air_temp.nc",
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


def test_check_input_files_direct_path(tmp_path):
    """Get a iterable of a single file from a direct path as a string."""
    file_path = tmp_path / "file"
    file_path.touch()
    string_path = str(file_path)
    actual = read._check_input_files(string_path, "*")
    expected = [file_path]
    assert actual == expected


def test_check_input_files_direct_path_glob(tmp_path):
    """Get a iterable of files from a direct path containing a glob pattern."""
    file1_path = tmp_path / "file1"
    file2_path = tmp_path / "file2"
    file1_path.touch()
    file2_path.touch()
    glob_path = f"{tmp_path}/file*"
    actual = read._check_input_files(glob_path, "*")
    expected = [file1_path, file2_path]
    assert actual == expected


def test_check_input_files_direct_path_match_glob_like_file(tmp_path):
    """Get a iterable of a single file from a glob-like direct path."""
    file1_path = tmp_path / "file1"
    glob_like_path = tmp_path / "file*"
    file1_path.touch()
    glob_like_path.touch()
    actual = read._check_input_files(str(glob_like_path), "*")
    expected = [glob_like_path]
    assert actual == expected


def test_check_input_files_input_directory(tmp_path):
    """Get a iterable of files in an input directory."""
    file1_path = tmp_path / "file1"
    file2_path = tmp_path / "file2"
    file1_path.touch()
    file2_path.touch()
    actual = read._check_input_files(str(tmp_path), "*")
    expected = [file1_path, file2_path]
    assert actual == expected


def test_check_input_files_input_directory_glob(tmp_path):
    """Get a iterable of files in an input directory with a glob pattern."""
    file1_path = tmp_path / "file1"
    file2_path = tmp_path / "file2"
    file1_path.touch()
    file2_path.touch()
    actual = read._check_input_files(str(tmp_path), "*1")
    expected = [file1_path]
    assert actual == expected


def test_check_input_files_invalid_path(tmp_path):
    """Error when path doesn't exist."""
    file_path = str(tmp_path / "file")
    with pytest.raises(FileNotFoundError):
        read._check_input_files(file_path, "*")


def test_check_input_files_no_file_in_directory(tmp_path):
    """Error when input directory doesn't contain any files."""
    with pytest.raises(FileNotFoundError):
        read._check_input_files(str(tmp_path), "*")


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


def test_spatial_coord_rename_callback():
    """Check that spatial coord gets renamed if it is not grid_latitude."""
    # This cube contains 'latitude' and 'longitude'
    cube = iris.load_cube("tests/test_data/transect_test_umpl.nc")
    read._fix_spatial_coord_name_callback(cube)
    assert (
        repr(cube.coords())
        == "[<DimCoord: time / (hours since 1970-01-01 00:00:00)  [...]  shape(2,)>, <DimCoord: pressure / (hPa)  [ 100., 150., ..., 950., 1000.]  shape(16,)>, <DimCoord: grid_latitude / (degrees)  [-10.98, -10.94, ..., -10.82, -10.78]  shape(6,)>, <DimCoord: grid_longitude / (degrees)  [19.02, 19.06, ..., 19.18, 19.22]  shape(6,)>, <DimCoord: forecast_reference_time / (hours since 1970-01-01 00:00:00)  [...]>, <AuxCoord: forecast_period / (hours)  [15., 18.]  shape(2,)>]"
    )


def test_spatial_coord_not_exist_callback():
    """Check that spatial coord returns cube if cube does not contain spatial coordinates."""
    cube = iris.load_cube("tests/test_data/transect_test_umpl.nc")
    cube = cube[:, :, 0, 0]  # Remove spatial dimcoords
    read._fix_spatial_coord_name_callback(cube)
    assert (
        repr(cube.coords())
        == "[<DimCoord: time / (hours since 1970-01-01 00:00:00)  [...]  shape(2,)>, <DimCoord: pressure / (hPa)  [ 100., 150., ..., 950., 1000.]  shape(16,)>, <DimCoord: forecast_reference_time / (hours since 1970-01-01 00:00:00)  [...]>, <DimCoord: latitude / (degrees)  [-10.98]>, <DimCoord: longitude / (degrees)  [19.02]>, <AuxCoord: forecast_period / (hours)  [15., 18.]  shape(2,)>]"
    )
