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

"""Tests for the dFSS operator."""

import datetime

import cf_units
import iris
import iris.cube
import numpy as np
import pytest

from CSET.operators import dfss


@pytest.fixture
def feature_cube() -> iris.cube.Cube:
    """Set up three timesteps and three realizations of data and place into cube."""
    data_arr = np.zeros((3, 3, 10, 10))
    data_arr[0:2, 0, 2:6, 2:6] = 1
    data_arr[0:2, 1, 3:7, 3:7] = 1
    data_arr[0:2, 2, 4:8, 4:8] = 1

    realization = iris.coords.DimCoord(points=[0, 1, 2], standard_name="realization")
    time_units = cf_units.Unit("days since 2000-01-01 00:00:00", calendar="gregorian")
    time_start = datetime.datetime(2010, 1, 1, 0, 0, 0)
    time_dt_points = [
        time_start + datetime.timedelta(minutes=5 * idx) for idx in range(3)
    ]
    time_points = [time_units.date2num(time_point) for time_point in time_dt_points]
    time_coord = iris.coords.DimCoord(
        points=time_points, standard_name="time", units=time_units
    )

    forecast_period = iris.coords.AuxCoord(
        points=[0, 5, 10], standard_name="forecast_period", units="minutes"
    )

    coord_system = iris.coord_systems.TransverseMercator(
        latitude_of_projection_origin=55, longitude_of_central_meridian=0
    )
    coord_range = np.arange(0, 100, 10)
    proj_y_coord = iris.coords.DimCoord(
        points=coord_range,
        standard_name="projection_y_coordinate",
        var_name="projection_y_coordinate",
        units="m",
        coord_system=coord_system,
    )
    proj_x_coord = iris.coords.DimCoord(
        points=coord_range,
        standard_name="projection_x_coordinate",
        var_name="projection_x_coordinate",
        units="m",
        coord_system=coord_system,
    )

    proj_y_coord.guess_bounds()
    proj_x_coord.guess_bounds()

    coords = (realization, time_coord, proj_y_coord, proj_x_coord)
    dim_coords_and_dims = [(coord, dim) for dim, coord in enumerate(coords)]
    cube = iris.cube.Cube(
        data=data_arr,
        dim_coords_and_dims=dim_coords_and_dims,
        long_name="dfss test",
    )
    cube.add_aux_coord(forecast_period, data_dims=[0])
    return cube


@pytest.mark.filterwarnings("ignore: Warning")
def test_dfss_basic_functioning(feature_cube):
    """Test basic functionality of the main dfss function."""
    fc_time_npoints = feature_cube.shape[1]
    neighbourhood_lengths = [1, 2, 3]

    dfss_cube, dfss_stdev_cube = dfss.calculate_dfss(
        feature_cube,
        neighbourhood_lengths=neighbourhood_lengths,
        centile=95,
        run_parallel=False,
    )

    assert dfss_cube.data.shape == (fc_time_npoints, np.size(neighbourhood_lengths))
    assert dfss_stdev_cube.data.shape == (
        fc_time_npoints,
        np.size(neighbourhood_lengths),
    )


def test_dfss_one_realisation_exception(feature_cube):
    """Test handling of non-ensemble data."""
    one_realisation_feature_cube = feature_cube.extract(iris.Constraint(realization=1))
    with pytest.raises(ValueError, match=r"dFSS is only valid for an ensemble"):
        dfss.calculate_dfss(
            one_realisation_feature_cube,
            neighbourhood_lengths=[0, 1, 2],
            centile=95,
            run_parallel=False,
        )


def test_calc_fss(feature_cube):
    """Test the calc_fss function."""
    cube_a_in = feature_cube[1, :, :, :]
    cube_b_in = feature_cube[2, :, :, :]
    fss = dfss._calc_fss(cube_a_in, cube_b_in, neighbourhood_length=2, centile=95)
    assert type(fss) is float
