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
from iris.cube import Cube, CubeList

from CSET.operators import constraints, filters, read


@pytest.fixture()
def tmp_working_dir(tmp_path, monkeypatch):
    """Change the working directory for a test."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


# For speed only load the data from disk once, then make an in-memory copy
# whenever it is reused.
@pytest.fixture(scope="session")
def cubes_readonly():
    """Get an iris CubeList. It is NOT safe to modify."""
    return read.read_cubes("tests/test_data/air_temp.nc")


@pytest.fixture(scope="session")
def cube_readonly(cubes_readonly):
    """Get an iris Cube. It is NOT safe to modify."""
    return filters.filter_cubes(
        cubes_readonly, constraints.generate_cell_methods_constraint([])
    )


@pytest.fixture()
def cubes(cubes_readonly: CubeList) -> CubeList:
    """Get an iris CubeList. It is safe to modify."""
    return cubes_readonly.copy()


@pytest.fixture()
def cube(cube_readonly: Cube) -> Cube:
    """Get an iris Cube. It is safe to modify."""
    return cube_readonly.copy()
