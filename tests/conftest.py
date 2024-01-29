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


@pytest.fixture()
def tmp_working_dir(tmp_path, monkeypatch):
    """Change the working directory for a test."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture(scope="session")
def cubes():
    """Get an iris CubeList."""
    import CSET.operators.read as read

    return read.read_cubes("tests/test_data/air_temp.nc")


@pytest.fixture(scope="session")
def cube(cubes):
    """Get an iris Cube."""
    from CSET.operators import constraints, filters

    return filters.filter_cubes(cubes, constraints.generate_cell_methods_constraint([]))
