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

import iris
import iris.cube
import numpy as np
import pytest

from CSET.operators import dfss


@pytest.mark.filterwarnings("ignore: Warning")
def test_dfss_basic_functioning(dfss_ensemble_cube):
    """Test basic functionality of the main dfss function."""
    fc_time_npoints = dfss_ensemble_cube.shape[1]
    neighbourhood_lengths = [1, 2, 3]

    dfss_cube, dfss_stdev_cube = dfss.calculate_dfss(
        dfss_ensemble_cube,
        neighbourhood_lengths=neighbourhood_lengths,
        centile=95,
        run_parallel=False,
    )

    assert dfss_cube.data.shape == (fc_time_npoints, np.size(neighbourhood_lengths))
    assert dfss_stdev_cube.data.shape == (
        fc_time_npoints,
        np.size(neighbourhood_lengths),
    )

    dfss_cube, dfss_stdev_cube = dfss.calculate_dfss(
        dfss_ensemble_cube,
        neighbourhood_lengths=neighbourhood_lengths,
        centile_or_threshold="threshold",
        threshold=1,
        run_parallel=False,
    )

    assert dfss_cube.data.shape == (fc_time_npoints, np.size(neighbourhood_lengths))
    assert dfss_stdev_cube.data.shape == (
        fc_time_npoints,
        np.size(neighbourhood_lengths),
    )


def test_dfss_one_realisation_exception(dfss_ensemble_cube):
    """Test handling of non-ensemble data."""
    one_realisation_dfss_ensemble_cube = dfss_ensemble_cube.extract(
        iris.Constraint(realization=1)
    )
    with pytest.raises(ValueError, match=r"dFSS is only valid for an ensemble"):
        dfss.calculate_dfss(
            one_realisation_dfss_ensemble_cube,
            neighbourhood_lengths=[0, 1, 2],
            centile=95,
            run_parallel=False,
        )


def test_calc_fss(dfss_ensemble_cube):
    """Test the calc_fss function."""
    cube_a_in = dfss_ensemble_cube[1, :, :, :]
    cube_b_in = dfss_ensemble_cube[2, :, :, :]
    fss = dfss._calc_fss(cube_a_in, cube_b_in, neighbourhood_length=2, centile=95)
    assert type(fss) is float


def test_calc_dfss(dfss_ensemble_cube):
    """Test calc_dfss function."""
    for time_slice in dfss_ensemble_cube.slices_over("time"):
        time_point = time_slice.coord("time")
        dfss_cube, dfss_stdev_cube = dfss._calc_dfss(
            time_slice, [1], time_point, centile=95
        )
        assert type(dfss_cube) is iris.cube.Cube
        assert type(dfss_stdev_cube) is iris.cube.Cube


def test_serial_calculate_dfss(dfss_ensemble_cube):
    """Test serial_calculate_dfss function."""
    outlist = dfss._serial_calculate_dfss(dfss_ensemble_cube, [1], centile=95)
    assert type(outlist) is iris.cube.CubeList
    assert type(outlist[0]) is iris.cube.Cube
    assert type(outlist[1]) is iris.cube.Cube


def test_parallel_calculate_dfss(dfss_ensemble_cube):
    """Test parallel_calculate_dfss function."""
    outlist_centile = dfss._parallel_calculate_dfss(dfss_ensemble_cube, [1], centile=95)
    assert type(outlist_centile) is iris.cube.CubeList
    assert type(outlist_centile[0]) is iris.cube.Cube
    assert type(outlist_centile[1]) is iris.cube.Cube
    outlist_threshold = dfss._parallel_calculate_dfss(
        dfss_ensemble_cube, [1], centile_or_threshold="threshold", threshold=2
    )
    assert type(outlist_threshold) is iris.cube.CubeList
    assert type(outlist_threshold[0]) is iris.cube.Cube
    assert type(outlist_threshold[1]) is iris.cube.Cube


def test_dfss_on_slice(dfss_ensemble_cube):
    """Test dfss_on_slice."""
    for time_slice in dfss_ensemble_cube.slices_over("time"):
        dfss_cube, dfss_stdev_cube = dfss._dfss_on_slice(
            time_slice, [1], "centile", 95, None
        )
        assert type(dfss_cube) is iris.cube.Cube
        assert type(dfss_stdev_cube) is iris.cube.Cube
    for time_slice in dfss_ensemble_cube.slices_over("time"):
        dfss_cube, dfss_stdev_cube = dfss._dfss_on_slice(
            time_slice, [1], "threshold", None, 2
        )
        assert type(dfss_cube) is iris.cube.Cube
        assert type(dfss_stdev_cube) is iris.cube.Cube


def test_calc_fss_two_fields():
    """Test calc_fss_two_fields."""
    data_arr1 = np.zeros((3, 3, 10, 10))
    data_arr1[2:6, 2:6] = 9
    data_arr1[3:7, 3:7] = 3
    data_arr1[4:8, 4:8] = 6

    data_arr2 = np.zeros((10, 10))
    data_arr2[2:6, 2:6] = 3
    data_arr2[3:7, 3:7] = 5
    data_arr2[4:8, 4:8] = 6

    fss = dfss._calc_fss_two_fields(data_arr1, data_arr2)
    assert fss == pytest.approx(0.1773628938156359)


def test_get_spatial_coords(dfss_ensemble_cube):
    """Test get_spatial_coords."""
    x, y = dfss._get_spatial_coords(dfss_ensemble_cube)
    assert x.name() == "projection_x_coordinate"
    assert y.name() == "projection_y_coordinate"
    assert x.shape == (10,)
    assert y.shape == (10,)
    assert x.units.name == "meter"
    assert y.units.name == "meter"


def test_regrid_lat_lon_cube_to_xy_cube(dfss_ensemble_cube):
    """Test regrid_lat_lon_cube_to_xy_cube."""
    cube = dfss._regrid_lat_lon_cube_to_xy_cube(dfss_ensemble_cube)
    assert type(cube) is iris.cube.Cube
