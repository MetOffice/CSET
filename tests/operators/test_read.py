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
    # TODO: Warning doesn't reach pytest for some reason.
    # with pytest.warns(Warning, match="No cubes loaded"):
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
