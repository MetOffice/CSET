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

"""Fixtures defined in this module will be available to all tests.

https://docs.pytest.org/en/latest/reference/fixtures.html#conftest-py-sharing-fixtures-across-multiple-files
"""

import pytest

from CSET.operators import constraints, filters, read


@pytest.fixture()
def tmp_working_dir(tmp_path, monkeypatch):
    """Change the working directory for a test."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


# Session scope fixtures, so the test data only has to be loaded once.
@pytest.fixture(scope="session")
def cubes():
    """Get an iris CubeList."""
    return read.read_cubes("tests/test_data/air_temp.nc")


@pytest.fixture(scope="session")
def cube(cubes):
    """Get an iris Cube."""
    return filters.filter_cubes(cubes, constraints.generate_cell_methods_constraint([]))


@pytest.fixture(scope="session")
def vertical_profile_cube_readonly():
    """Get a vertical profile Cube. It is NOT safe to modify."""
    from CSET.operators import read

    return read.read_cube(
        "tests/test_data/air_temperature_vertical_profile_as_series.nc"
    )


@pytest.fixture()
def vertical_profile_cube(vertical_profile_cube_readonly):
    """Get a vertical profile Cube. It is safe to modify."""
    return vertical_profile_cube_readonly.copy()


@pytest.fixture(scope="session")
def histogram_cube_readonly():
    """Get a histogram Cube. It is NOT safe to modify."""
    from CSET.operators import read

    return read.read_cube(
        "tests/test_data/air_temperature_vertical_profile_as_series.nc"
    )


@pytest.fixture()
def histogram_cube(histogram_cube_readonly):
    """Get a histogram Cube."""
    return histogram_cube_readonly.copy()


@pytest.fixture(scope="session")
def regrid_rectilinear_cube_readonly():
    """Get a cube to test with. It is NOT safe to modify."""
    return read.read_cube(
        "tests/test_data/regrid/regrid_rectilinearGeogCS.nc", "surface_altitude"
    )


@pytest.fixture()
def regrid_rectilinear_cube(regrid_rectilinear_cube_readonly):
    """Get a cube to test with. It is safe to modify."""
    return regrid_rectilinear_cube_readonly.copy()


@pytest.fixture(scope="session")
def transect_source_cube_readonly():
    """Get a 3D cube to test with. It is NOT safe to modify."""
    return read.read_cube("tests/test_data/transect_test_umpl.nc")


@pytest.fixture()
def transect_source_cube(transect_source_cube_readonly):
    """Get a 3D cube to test with. It is safe to modify."""
    return transect_source_cube_readonly.copy()
