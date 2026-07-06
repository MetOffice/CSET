# © Crown copyright, Met Office (2022-2026) and CSET contributors.
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

import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path
from uuid import uuid4

import iris
import iris.cube
import pytest

from CSET.operators import constraints, filters, read


@pytest.fixture
def cdl_to_nc_path(tmp_path) -> Callable[[str], Path]:
    """Get a callback that will create a temporary NetCDF file based on a CDL definition."""

    def cdl_to_nc(cdl: str) -> Path:
        """
        Convert a CDL description into a netcdf file.

        Parameters
        ----------
        name
            prefix of the output file name
        cdl
            CDL description of the data
        output
            output directory

        Returns
        -------
            Path of the created netcdf file (``{outdir}/{name}.nc``)

        Notes
        -----
        See https://docs.unidata.ucar.edu/nug/2.0-draft/cdl.html for the details of
        CDL format.
        """
        # Random UUID
        name = uuid4()

        cdl_path = tmp_path / f"{name}.cdl"
        nc_path = tmp_path / f"{name}.nc"
        with open(cdl_path, "w") as f:
            f.write(cdl)
        subprocess.run(
            ["ncgen", "-k", "nc4", "-o", str(nc_path), str(cdl_path)], check=True
        )
        return nc_path

    return cdl_to_nc


@pytest.fixture
def cdl_to_cubes(
    cdl_to_nc_path,
) -> Callable[[str, str | iris.Constraint | None], iris.cube.CubeList]:
    """Get a callback that will create CSET cubes based on a CDL definition."""

    def callback(
        cdl: str, constraint: str | iris.Constraint | None = None
    ) -> iris.cube.CubeList:
        path = cdl_to_nc_path(cdl)
        return read.read_cubes(path, constraint)  # noqa

    return callback


@pytest.fixture
def cdl_to_cube(
    cdl_to_nc_path,
) -> Callable[[str, str | iris.Constraint | None], iris.cube.Cube]:
    """Get a callback that will create a CSET cube based on a CDL definition."""

    def callback(
        cdl: str, constraint: str | iris.Constraint | None = None
    ) -> iris.cube.Cube:
        path = cdl_to_nc_path(cdl)
        return read.read_cube(path, constraint)  # noqa

    return callback


@pytest.fixture()
def tmp_working_dir(tmp_path, monkeypatch) -> Path:
    """Change the working directory for a test."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture()
def workflow(tmp_path) -> Path:
    """Extract a fresh workflow."""
    subprocess.run(["cset", "extract-workflow", str(tmp_path)], check=True)
    workflow_dir: Path = next(tmp_path.glob("cset-workflow-v*"))
    # Copy example configuration into place.
    shutil.copyfile(
        workflow_dir / "rose-suite.conf.example", workflow_dir / "rose-suite.conf"
    )
    return workflow_dir


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
    return read.read_cube(
        "tests/test_data/air_temperature_vertical_profile_as_series.nc"
    )


@pytest.fixture()
def histogram_cube(histogram_cube_readonly):
    """Get a histogram Cube."""
    return histogram_cube_readonly.copy()


@pytest.fixture(scope="session")
def field2d_cube_readonly():
    """Get a 2D Cube for testing power spectrum code. It is NOT safe to modify."""
    return read.read_cube("tests/test_data/air_temperature_lat_lon.nc")


@pytest.fixture()
def field2d_cube(field2d_cube_readonly):
    """Get a 2D cube for testing power spectrum code."""
    return field2d_cube_readonly.copy()


@pytest.fixture(scope="session")
def power_spectrum_cube_readonly():
    """Get a Cube for testing power spectrum code. It is NOT safe to modify."""
    return read.read_cube(
        "tests/test_data/power_spectrum_temperature_at_pressure_levels_pressure_250_1time.nc"
    )


@pytest.fixture()
def power_spectrum_cube(power_spectrum_cube_readonly):
    """Get a Cube for testing power spectrum code."""
    return power_spectrum_cube_readonly.copy()


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
def cardington_cube_readonly():
    """Get a 3D cube to test with. It is NOT safe to modify."""
    return read.read_cube("tests/test_data/cardington_air_temp_test.nc")


@pytest.fixture()
def cardington_cube(cardington_cube_readonly):
    """Get a 3D cube to test with. It is safe to modify."""
    return cardington_cube_readonly.copy()


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


@pytest.fixture(scope="session")
def visibility_cube_read_only():
    """Get visibility cube to run tests on. It is NOT safe to modify."""
    return read.read_cube("tests/test_data/aviation/vis_avi.nc")


@pytest.fixture()
def visibility_cube(visibility_cube_read_only):
    """Get visibility cube to run tests on. It is safe to modify."""
    return visibility_cube_read_only.copy()


@pytest.fixture(scope="session")
def cloud_base_cube_read_only():
    """Get cloud base altitude cube to run tests on. It is NOT safe to modify."""
    return read.read_cube("tests/test_data/aviation/cld_base_avi.nc")


@pytest.fixture()
def cloud_base_cube(cloud_base_cube_read_only):
    """Get cloud base altitude cube to run tests on. It is safe to modify."""
    return cloud_base_cube_read_only.copy()


@pytest.fixture(scope="session")
def orography_cube_read_only():
    """Get orography cube to run tests on. It is NOT safe to modify."""
    return read.read_cube("tests/test_data/aviation/Orography_2D_avi.nc")


@pytest.fixture()
def orography_cube(orography_cube_read_only):
    """Get orography cube to run tets on. It is safe to modify."""
    return orography_cube_read_only.copy()


@pytest.fixture(scope="session")
def orography_3D_cube_read_only():
    """Get 3D orography cube to run tests on. It is NOT safe to modify."""
    return read.read_cube("tests/test_data/aviation/Orography_3D_avi.nc")


@pytest.fixture()
def orography_3D_cube(orography_3D_cube_read_only):
    """Get 3D orography cube to run tests on. It is safe to modify."""
    return orography_3D_cube_read_only.copy()


@pytest.fixture(scope="session")
def orography_4D_cube_read_only():
    """Get 4D orography cube to run tests on. It is NOT safe to modify."""
    return read.read_cube("tests/test_data/aviation/Orography_4D_avi.nc")


@pytest.fixture()
def orography_4D_cube(orography_4D_cube_read_only):
    """Get 4D orography cube to run tests on. It is safe to modify."""
    return orography_4D_cube_read_only.copy()


@pytest.fixture()
def temperature_for_conversions_cube_read_only():
    """Get temperature cube for conversions to run tests on. It is NOT safe to modify."""
    return read.read_cube("tests/test_data/pressure/air_temperature.nc")


@pytest.fixture()
def temperature_for_conversions_cube(temperature_for_conversions_cube_read_only):
    """Get temperature cube for conversions to run tests on. It is safe to modify."""
    return temperature_for_conversions_cube_read_only.copy()


@pytest.fixture()
def pressure_for_conversions_cube_read_only():
    """Get pressure cube for conversions to run tests on. It is NOT safe to modify."""
    return read.read_cube("tests/test_data/pressure/pressure.nc")


@pytest.fixture()
def pressure_for_conversions_cube(pressure_for_conversions_cube_read_only):
    """Get pressure cube for conversions to run tests on. It is safe to modify."""
    return pressure_for_conversions_cube_read_only.copy()


@pytest.fixture()
def relative_humidity_for_conversions_cube_read_only():
    """Get relative humidity cube for conversions to run tests on. It is NOT safe to modify."""
    return read.read_cube("tests/test_data/pressure/relative_humidity.nc")


@pytest.fixture()
def relative_humidity_for_conversions_cube(
    relative_humidity_for_conversions_cube_read_only,
):
    """Get relative humidity cube for conversions to run tests on. It is safe to modify."""
    return relative_humidity_for_conversions_cube_read_only.copy()


@pytest.fixture()
def specific_humidity_for_conversions_cube_read_only():
    """Get specific humidity cube for conversions to run tests on. It is NOT safe to modify."""
    return read.read_cube("tests/test_data/humidity/specific_humidity.nc")


@pytest.fixture()
def specific_humidity_for_conversions_cube(
    specific_humidity_for_conversions_cube_read_only,
):
    """Get specific humidity cube for conversions to run tests on. It is safe to modify."""
    return specific_humidity_for_conversions_cube_read_only.copy()


@pytest.fixture()
def mixing_ratio_for_conversions_cube_read_only():
    """Get mixing ratio cube for conversions to run tests on. It is NOT safe to modify."""
    return read.read_cube("tests/test_data/humidity/mixing_ratio.nc")


@pytest.fixture()
def mixing_ratio_for_conversions_cube(
    mixing_ratio_for_conversions_cube_read_only,
):
    """Get mixing ratio cube for conversions to run tests on. It is safe to modify."""
    return mixing_ratio_for_conversions_cube_read_only.copy()


@pytest.fixture()
def maul_mask_read_only():
    """Get maul mask cube for precipitation tests. It is NOT safe to modify."""
    return read.read_cube("tests/test_data/precipitation/basic_maul_mask.nc")


@pytest.fixture()
def maul_mask(maul_mask_read_only):
    """Get maul mask cube for precipitation tests. It is safe to modify."""
    return maul_mask_read_only.copy()


@pytest.fixture()
def maul_mask_member_read_only():
    """Get maul mask cube for precipitation tests. It is NOT safe to modify."""
    return read.read_cube("tests/test_data/precipitation/basic_maul_mask_member.nc")


@pytest.fixture()
def maul_mask_member(maul_mask_member_read_only):
    """Get maul mask cube for precipitation tests. It is safe to modify."""
    return maul_mask_member_read_only.copy()


@pytest.fixture()
def maul_mask_time_read_only():
    """Get maul mask cube for precipitation tests. It is NOT safe to modify."""
    return read.read_cube("tests/test_data/precipitation/basic_maul_mask_time.nc")


@pytest.fixture()
def maul_mask_time(maul_mask_time_read_only):
    """Get maul mask cube for precipitation tests. It is safe to modify."""
    return maul_mask_time_read_only.copy()


@pytest.fixture()
def maul_mask_all_read_only():
    """Get maul mask cube for precipitation tests. It is NOT safe to modify."""
    return read.read_cube("tests/test_data/precipitation/basic_maul_mask_all.nc")


@pytest.fixture()
def maul_mask_all(maul_mask_all_read_only):
    """Get maul mask cube for precipitation tests. It is safe to modify."""
    return maul_mask_all_read_only.copy()


@pytest.fixture()
def precalc_maul_number_3d_read_only():
    """Get precalculated number of mauls for precipitation tests. It is NOT safe to modify."""
    return read.read_cube("tests/test_data/precipitation/precalc_number_3d.nc")


@pytest.fixture()
def precalc_maul_number_3d(precalc_maul_number_3d_read_only):
    """Get precalculated number of mauls for precipitation tests. It is safe to modify."""
    return precalc_maul_number_3d_read_only.copy()


@pytest.fixture()
def precalc_maul_base_3d_read_only():
    """Get precalculated base of mauls for precipitation tests. It is NOT safe to modify."""
    return read.read_cube("tests/test_data/precipitation/precalc_base_3d.nc")


@pytest.fixture()
def precalc_maul_base_3d(precalc_maul_base_3d_read_only):
    """Get precalculated base of mauls for precipitation tests. It is safe to modify."""
    return precalc_maul_base_3d_read_only.copy()


@pytest.fixture()
def precalc_maul_depth_3d_read_only():
    """Get precalculated depth of mauls for precipitation tests. It is NOT safe to modify."""
    return read.read_cube("tests/test_data/precipitation/precalc_depth_3d.nc")


@pytest.fixture()
def precalc_maul_depth_3d(precalc_maul_depth_3d_read_only):
    """Get precalculated depth of mauls for precipitation tests. It is safe to modify."""
    return precalc_maul_depth_3d_read_only.copy()


@pytest.fixture()
def precalc_maul_number_4d_time_read_only():
    """Get precalculated number for time change dimension. It is NOT safe to modify."""
    return read.read_cube("tests/test_data/precipitation/maul_time_4d_number.nc")


@pytest.fixture()
def precalc_maul_number_4d_time(precalc_maul_number_4d_time_read_only):
    """Get precalculated number for time change dimension. It is safe to modify."""
    return precalc_maul_number_4d_time_read_only.copy()


@pytest.fixture()
def precalc_maul_base_4d_time_read_only():
    """Get precalculated base for time change dimension. It is NOT safe to modify."""
    return read.read_cube("tests/test_data/precipitation/maul_time_4d_base.nc")


@pytest.fixture()
def precalc_maul_base_4d_time(precalc_maul_base_4d_time_read_only):
    """Get precalculated base for time change dimension. It is safe to modify."""
    return precalc_maul_base_4d_time_read_only.copy()


@pytest.fixture()
def precalc_maul_depth_4d_time_read_only():
    """Get precalculated depth for time change dimension. It is NOT safe to modify."""
    return read.read_cube("tests/test_data/precipitation/maul_time_4d_depth.nc")


@pytest.fixture()
def precalc_maul_depth_4d_time(precalc_maul_depth_4d_time_read_only):
    """Get precalculated depth for time change dimension. It is safe to modify."""
    return precalc_maul_depth_4d_time_read_only.copy()


@pytest.fixture()
def precalc_maul_number_4d_realization_read_only():
    """Get precalculated number for realization change dimension. It is NOT safe to modify."""
    return read.read_cube("tests/test_data/precipitation/maul_member_4d_number.nc")


@pytest.fixture()
def precalc_maul_number_4d_realization(precalc_maul_number_4d_realization_read_only):
    """Get precalculated number for realization change dimension. It is safe to modify."""
    return precalc_maul_number_4d_realization_read_only.copy()


@pytest.fixture()
def precalc_maul_base_4d_realization_read_only():
    """Get precalculated base for realization change dimension. It is NOT safe to modify."""
    return read.read_cube("tests/test_data/precipitation/maul_member_4d_base.nc")


@pytest.fixture()
def precalc_maul_base_4d_realization(precalc_maul_base_4d_realization_read_only):
    """Get precalculated base for realization change dimension. It is safe to modify."""
    return precalc_maul_base_4d_realization_read_only.copy()


@pytest.fixture()
def precalc_maul_depth_4d_realization_read_only():
    """Get precalculated depth for realization change dimension. It is NOT safe to modify."""
    return read.read_cube("tests/test_data/precipitation/maul_member_4d_depth.nc")


@pytest.fixture()
def precalc_maul_depth_4d_realization(precalc_maul_depth_4d_realization_read_only):
    """Get precalculated depth for realization change dimension. It is safe to modify."""
    return precalc_maul_depth_4d_realization_read_only.copy()


@pytest.fixture()
def precalc_maul_number_5d_read_only():
    """Get precalculated number for 5D data. It is NOT safe to modify."""
    return read.read_cube("tests/test_data/precipitation/maul_member_5d_number.nc")


@pytest.fixture()
def precalc_maul_number_5d(precalc_maul_number_5d_read_only):
    """Get precalculated number for 5D data. It is safe to modify."""
    return precalc_maul_number_5d_read_only.copy()


@pytest.fixture()
def precalc_maul_base_5d_read_only():
    """Get precalculated base for 5D data. It is NOT safe to modify."""
    return read.read_cube("tests/test_data/precipitation/maul_member_5d_base.nc")


@pytest.fixture()
def precalc_maul_base_5d(precalc_maul_base_5d_read_only):
    """Get precalculated base for 5D data. It is safe to modify."""
    return precalc_maul_base_5d_read_only.copy()


@pytest.fixture()
def precalc_maul_depth_5d_read_only():
    """Get precalculated depth for 5D data. It is NOT safe to modify."""
    return read.read_cube("tests/test_data/precipitation/maul_member_5d_depth.nc")


@pytest.fixture()
def precalc_maul_depth_5d(precalc_maul_depth_5d_read_only):
    """Get precalculated depth for 5D data. It is safe to modify."""
    return precalc_maul_depth_5d_read_only.copy()


@pytest.fixture()
def mr_3d_read_only():
    """Get mixing ratio 3D data. It is NOT safe to modify."""
    return read.read_cube("tests/test_data/humidity/mr_basic.nc")


@pytest.fixture()
def mr_3d(mr_3d_read_only):
    """Get mixing ratio 3D data. It is safe to modify."""
    return mr_3d_read_only.copy()


@pytest.fixture()
def mr_time_read_only():
    """Get mixing ratio 4D data varying in time. It is NOT safe to modify."""
    return read.read_cube("tests/test_data/humidity/mr_time.nc")


@pytest.fixture()
def mr_time(mr_time_read_only):
    """Get mixing ratio 4D data varying in time. It is safe to modify."""
    return mr_time_read_only.copy()


@pytest.fixture()
def mr_member_read_only():
    """Get mixing ratio 4D data varying in member. It is NOT safe to modify."""
    return read.read_cube("tests/test_data/humidity/mr_member.nc")


@pytest.fixture()
def mr_member(mr_member_read_only):
    """Get mixing ratio 4D data varying in member. It is safe to modify."""
    return mr_member_read_only.copy()


@pytest.fixture()
def mr_5d_read_only():
    """Get mixing ratio 5D data. It is NOT safe to modify."""
    return read.read_cube("tests/test_data/humidity/mr_all.nc")


@pytest.fixture()
def mr_5d(mr_5d_read_only):
    """Get mixing ratio 5D data. It is safe to modify."""
    return mr_5d_read_only.copy()


@pytest.fixture()
def rh_3d_read_only():
    """Get relative humidity 3D data. It is NOT safe to modify."""
    return read.read_cube("tests/test_data/humidity/rh_basic.nc")


@pytest.fixture()
def rh_3d(rh_3d_read_only):
    """Get relative humidity 3D data. It is safe to modify."""
    return rh_3d_read_only.copy()


@pytest.fixture()
def rh_time_read_only():
    """Get relative humidity 4D data varying in time. It is NOT safe to modify."""
    return read.read_cube("tests/test_data/humidity/rh_time.nc")


@pytest.fixture()
def rh_time(rh_time_read_only):
    """Get relative humidity 4D data varying in time. It is safe to modify."""
    return rh_time_read_only.copy()


@pytest.fixture()
def rh_member_read_only():
    """Get relative humidity 4D data varying in member. It is NOT safe to modify."""
    return read.read_cube("tests/test_data/humidity/rh_member.nc")


@pytest.fixture()
def rh_member(rh_member_read_only):
    """Get relative humidity 4D data varying in member. It is safe to modify."""
    return rh_member_read_only.copy()


@pytest.fixture()
def rh_5d_read_only():
    """Get relative humidity 5D data. It is NOT safe to modify."""
    return read.read_cube("tests/test_data/humidity/rh_all.nc")


@pytest.fixture()
def rh_5d(rh_5d_read_only):
    """Get relative humidity 5D data. It is safe to modify."""
    return rh_5d_read_only.copy()


@pytest.fixture()
def pw_3d_read_only():
    """Get precipitable water 3D data. It is NOT safe to modify."""
    return read.read_cube("tests/test_data/humidity/pw_basic.nc")


@pytest.fixture()
def pw_3d(pw_3d_read_only):
    """Get precipitable water 3D data. It is safe to modify."""
    return pw_3d_read_only.copy()


@pytest.fixture()
def pw_time_read_only():
    """Get precipitable water 4D data varying in time. It is NOT safe to modify."""
    return read.read_cube("tests/test_data/humidity/pw_time.nc")


@pytest.fixture()
def pw_time(pw_time_read_only):
    """Get precipitable water 4D data varying in time. It is safe to modify."""
    return pw_time_read_only.copy()


@pytest.fixture()
def pw_member_read_only():
    """Get precipitable water 4D data varying in member. It is NOT safe to modify."""
    return read.read_cube("tests/test_data/humidity/pw_member.nc")


@pytest.fixture()
def pw_member(pw_member_read_only):
    """Get precipitable water 4D data varying in member. It is safe to modify."""
    return pw_member_read_only.copy()


@pytest.fixture()
def pw_5d_read_only():
    """Get precipitable water 5D data. It is NOT safe to modify."""
    return read.read_cube("tests/test_data/humidity/pw_all.nc")


@pytest.fixture()
def pw_5d(pw_5d_read_only):
    """Get precipitable water 5D data. It is safe to modify."""
    return pw_5d_read_only.copy()


@pytest.fixture()
def spw_3d_read_only():
    """Get saturation precipitable water 3D data. It is NOT safe to modify."""
    return read.read_cube("tests/test_data/humidity/spw_basic.nc")


@pytest.fixture()
def spw_3d(spw_3d_read_only):
    """Get saturation precipitable water 3D data. It is safe to modify."""
    return spw_3d_read_only.copy()


@pytest.fixture()
def spw_time_read_only():
    """Get saturation precipitable water 4D data varying in time. It is NOT safe to modify."""
    return read.read_cube("tests/test_data/humidity/spw_time.nc")


@pytest.fixture()
def spw_time(spw_time_read_only):
    """Get saturation precipitable water 4D data varying in time. It is safe to modify."""
    return spw_time_read_only.copy()


@pytest.fixture()
def spw_member_read_only():
    """Get saturation precipitable water 4D data varying in member. It is NOT safe to modify."""
    return read.read_cube("tests/test_data/humidity/spw_member.nc")


@pytest.fixture()
def spw_member(spw_member_read_only):
    """Get saturation precipitable water 4D data varying in member. It is safe to modify."""
    return spw_member_read_only.copy()


@pytest.fixture()
def spw_5d_read_only():
    """Get saturation precipitable water 5D data. It is NOT safe to modify."""
    return read.read_cube("tests/test_data/humidity/spw_all.nc")


@pytest.fixture()
def spw_5d(spw_5d_read_only):
    """Get saturation precipitable water 5D data. It is safe to modify."""
    return spw_5d_read_only.copy()


@pytest.fixture()
def sf_3d_read_only():
    """Get saturation fraction 3D data. It is NOT safe to modify."""
    return read.read_cube("tests/test_data/humidity/sf_basic.nc")


@pytest.fixture()
def sf_3d(sf_3d_read_only):
    """Get saturation fraction 3D data. It is safe to modify."""
    return sf_3d_read_only.copy()
