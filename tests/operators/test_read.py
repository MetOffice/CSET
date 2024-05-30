# Copyright 2022 Met Office and contributors.
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


def test_check_input_files_direct_path(tmp_path):
    """Get a iterable of a single file from a direct path."""
    file_path = tmp_path / "file"
    file_path.touch()
    read._check_input_files(file_path, "*")
    actual = read._check_input_files(file_path, "*")
    expected = (file_path,)
    assert actual == expected


def test_check_input_files_direct_path_as_string(tmp_path):
    """Get a iterable of a single file from a direct path as a string."""
    file_path = tmp_path / "file"
    file_path.touch()
    string_path = str(file_path)
    actual = read._check_input_files(string_path, "*")
    expected = (file_path,)
    assert actual == expected


def test_check_input_files_direct_path_glob(tmp_path):
    """Get a iterable of files from a direct path containing a glob pattern."""
    file1_path = tmp_path / "file1"
    file2_path = tmp_path / "file2"
    file1_path.touch()
    file2_path.touch()
    glob_path = tmp_path / "file*"
    actual = read._check_input_files(glob_path, "*")
    expected = (file1_path, file2_path)
    assert actual == expected


def test_check_input_files_direct_path_match_glob_like_file(tmp_path):
    """Get a iterable of a single file from a glob-like direct path."""
    file1_path = tmp_path / "file1"
    glob_like_path = tmp_path / "file*"
    file1_path.touch()
    glob_like_path.touch()
    actual = read._check_input_files(glob_like_path, "*")
    expected = (glob_like_path,)
    assert actual == expected


def test_check_input_files_input_directory(tmp_path):
    """Get a iterable of files in an input directory."""
    file1_path = tmp_path / "file1"
    file2_path = tmp_path / "file2"
    file1_path.touch()
    file2_path.touch()
    actual = read._check_input_files(tmp_path, "*")
    expected = (file1_path, file2_path)
    assert actual == expected


def test_check_input_files_input_directory_glob(tmp_path):
    """Get a iterable of files in an input directory with a glob pattern."""
    file1_path = tmp_path / "file1"
    file2_path = tmp_path / "file2"
    file1_path.touch()
    file2_path.touch()
    actual = read._check_input_files(tmp_path, "*1")
    expected = (file1_path,)
    assert actual == expected


def test_check_input_files_invalid_path(tmp_path):
    """Error when path doesn't exist."""
    file_path = tmp_path / "file"
    with pytest.raises(FileNotFoundError):
        read._check_input_files(file_path, "*")


def test_check_input_files_no_file_in_directory(tmp_path):
    """Error when input directory doesn't contain any files."""
    with pytest.raises(FileNotFoundError):
        read._check_input_files(tmp_path, "*")


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
