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

"""Fixtures defined in this module will be available to all tests.

https://docs.pytest.org/en/latest/reference/fixtures.html#conftest-py-sharing-fixtures-across-multiple-files
"""

from pathlib import Path

import iris.cube
import pytest

from CSET.operators import constraints, filters, read


@pytest.fixture()
def tmp_working_dir(tmp_path, monkeypatch) -> Path:
    """Change the working directory for a test."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


# Session scope fixtures, so the test data only has to be loaded from disk
# once, then make an in-memory copy whenever it is reused.
@pytest.fixture(scope="session")
def cubes_readonly():
    """Get an iris CubeList. NOT safe to modify."""
    return read.read_cubes("tests/test_data/air_temp.nc")


@pytest.fixture()
def cubes(cubes_readonly):
    """Get an iris CubeList. Safe to modify."""
    return cubes_readonly.copy()


@pytest.fixture(scope="session")
def cube_readonly(cubes_readonly):
    """Get an iris Cube. NOT safe to modify."""
    return filters.filter_cubes(
        cubes_readonly, constraints.generate_cell_methods_constraint([])
    )


@pytest.fixture()
def cube(cube_readonly):
    """Get an iris Cube. Safe to modify."""
    return cube_readonly.copy()


@pytest.fixture(scope="session")
def slammed_lfric_cube_readonly():
    """Get an iris Cube of slammed LFRic data. NOT safe to modify."""
    return read.read_cube("tests/test_data/slammed_lfric_air_temp.nc")


@pytest.fixture()
def slammed_lfric_cube(slammed_lfric_cube_readonly):
    """Get an iris Cube of slammed LFRic data. Safe to modify."""
    return slammed_lfric_cube_readonly.copy()


@pytest.fixture(scope="session")
def vertical_profile_cube_readonly():
    """Get a vertical profile Cube. It is NOT safe to modify."""
    return read.read_cube(
        "tests/test_data/air_temperature_vertical_profile_as_series.nc"
    )


@pytest.fixture()
def vertical_profile_cube(vertical_profile_cube_readonly):
    """Get a vertical profile Cube. It is safe to modify."""
    return vertical_profile_cube_readonly.copy()


@pytest.fixture(scope="session")
def vector_cubes_readonly():
    """Get vector plot cubes. It is NOT safe to modify."""
    from CSET.operators import read

    # Read the input cubes.
    in_cubes = read.read_cubes("tests/test_data/u10_v10.nc")
    # Generate constraints for the u and v components of the wind.
    var_constraint_u = constraints.generate_var_constraint("eastward_wind")
    var_constraint_v = constraints.generate_var_constraint("northward_wind")
    lev_contraint = constraints.generate_level_constraint("height", 10)
    combined_constraint_u = constraints.combine_constraints(
        a=var_constraint_u, b=lev_contraint
    )
    combined_constraint_v = constraints.combine_constraints(
        a=var_constraint_v, b=lev_contraint
    )
    # filter the cubes using the constraints.
    cube_u = filters.filter_cubes(in_cubes, combined_constraint_u)
    cube_v = filters.filter_cubes(in_cubes, combined_constraint_v)
    return iris.cube.CubeList([cube_u, cube_v])


@pytest.fixture()
def vector_cubes(vector_cubes_readonly):
    """Get vector plot cubes."""
    return vector_cubes_readonly.copy()


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


@pytest.fixture(scope="session")
def long_forecast_read_only():
    """Get long_forecast to run tests on. It is NOT safe to modify."""
    return read.read_cube(
        "tests/test_data/long_forecast_air_temp_fcst_1.nc", "air_temperature"
    )


@pytest.fixture()
def long_forecast(long_forecast_read_only):
    """Get long_forecast to run tests on. It is safe to modify."""
    return long_forecast_read_only.copy()


@pytest.fixture(scope="session")
def long_forecast_multi_day_read_only():
    """Get long_forecast_multi_day to run tests on. It is NOT safe to modify."""
    return read.read_cube(
        "tests/test_data/long_forecast_air_temp_multi_day.nc", "air_temperature"
    )


@pytest.fixture()
def long_forecast_multi_day(long_forecast_multi_day_read_only):
    """Get long_forecast_multi_day to run tests on. It is safe to modify."""
    return long_forecast_multi_day_read_only.copy()


@pytest.fixture(scope="session")
def long_forecast_many_cubes_read_only():
    """Get long_forecast_may_cubes to run tests on. It is NOT safe to modify."""
    return read.read_cubes(
        "tests/test_data/long_forecast_air_temp_fcst_*.nc", "air_temperature"
    )


@pytest.fixture()
def long_forecast_many_cubes(long_forecast_many_cubes_read_only):
    """Get long_forecast_may_cubes to run tests on. It is safe to modify."""
    return long_forecast_many_cubes_read_only.copy()


@pytest.fixture(scope="session")
def model_level_cube_read_only():
    """Get model level cube to run tests on. It is NOT safe to modify."""
    return read.read_cube("tests/test_data/model_level_test.nc")


@pytest.fixture()
def model_level_cube(model_level_cube_read_only):
    """Get model level cube to run tests on. It is safe to modify."""
    return model_level_cube_read_only.copy()


@pytest.fixture(scope="session")
def global_cube_read_only():
    """Get global cube to run tests on. It is NOT safe to modify."""
    return read.read_cube("tests/test_data/air_temperature_global.nc")


@pytest.fixture()
def global_cube(global_cube_read_only):
    """Get global cube to run tests on. It is safe to modify."""
    return global_cube_read_only.copy()


@pytest.fixture(scope="session")
def ensemble_cube_read_only():
    """Get ensemble cube to run tests on. It is NOT safe to modify."""
    return read.read_cube("tests/test_data/exeter_em*.nc")


@pytest.fixture()
def ensemble_cube(ensemble_cube_read_only):
    """Get ensemble cube to run tests on. It is safe to modify."""
    return ensemble_cube_read_only.copy()
