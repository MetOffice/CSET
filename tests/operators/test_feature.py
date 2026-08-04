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
"""Tests for feature operators."""

import datetime as dt

import cf_units
import iris
import iris.coords
import iris.cube
import numpy as np
import pytest

from CSET.operators import feature


@pytest.fixture
def feature_cube() -> iris.cube.Cube:
    """Set up three timesteps of data and place into cube."""
    data_arr = np.zeros((3, 10, 10))
    data_arr[0, 2:6, 2:6] = 1
    data_arr[1, 3:7, 3:7] = 1
    data_arr[2, 4:8, 4:8] = 1

    time_units = cf_units.Unit("days since 2000-01-01 00:00:00", calendar="gregorian")
    time_start = dt.datetime(2010, 1, 1, 0, 0, 0)
    time_dt_points = [time_start + dt.timedelta(minutes=5 * idx) for idx in range(3)]
    time_points = [time_units.date2num(time_point) for time_point in time_dt_points]
    time_coord = iris.coords.DimCoord(
        points=time_points, standard_name="time", units=time_units
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

    coords = (time_coord, proj_y_coord, proj_x_coord)
    dim_coords_and_dims = [(coord, dim) for dim, coord in enumerate(coords)]
    cube = iris.cube.Cube(
        data=data_arr,
        dim_coords_and_dims=dim_coords_and_dims,
        long_name="Precipitation test",
    )
    return cube


def test_tracking_valid(feature_cube) -> None:
    """
    Test feature tracking returns same cube shape as input cube.

    Further tracking tests handled by Simple-Track dependency
    """
    test_threshold = 0.5
    min_size = 1
    tracking_cubelist = feature.track(
        feature_cube, threshold=test_threshold, min_size=min_size
    )
    outputs = ["feature_lifetime", "feature_id", "feature_init"]
    for output in outputs:
        tracking_cube = tracking_cubelist.extract_cube(output)
        assert tracking_cube.shape == feature_cube.shape


def test_tracking_lifetime_values(feature_cube) -> None:
    """Test feature tracking returns expected lifetime values."""
    test_threshold = 0.5
    min_size = 1
    tracking_cubelist = feature.track(
        feature_cube, threshold=test_threshold, min_size=min_size
    )
    tracking_cube = tracking_cubelist.extract_cube("feature_lifetime")
    # Check lifetime field values are expected, based on feature_cube data
    for time_slice_idx in range(3):
        expected_lifetime_field = np.where(
            feature_cube.data[time_slice_idx] > test_threshold, time_slice_idx + 1, 0
        )
        actual_lifetime_field = tracking_cube.data[time_slice_idx]
        np.testing.assert_array_equal(actual_lifetime_field, expected_lifetime_field)


def test_save_data(feature_cube, tmp_working_dir) -> None:
    """Test that tracking data is saved when save_data is True."""
    test_threshold = 0.5
    min_size = 1
    feature.track(
        feature_cube,
        threshold=test_threshold,
        min_size=min_size,
        save_data=True,
    )
    # Check expected lifetime field is created in output directory
    output_directory = tmp_working_dir / "tracking_data"
    expected_file = output_directory / "lifetime_20100101_0000.field"
    assert expected_file.is_file()

    # Check expected csv file is created in output directory
    expected_file = output_directory / "frame_20100101_0000.csv"
    assert expected_file.is_file()


def test_check_xy_coords_valid(feature_cube) -> None:
    """Test that _check_xy_coords does not raise an error for valid xy coordinates."""
    try:
        feature._check_xy_coords(feature_cube)
    except ValueError:
        pytest.fail("Unexpected ValueError raised for valid xy coordinates.")


def test_check_xy_coords_invalid() -> None:
    """Test that _check_xy_coords raises a ValueError for invalid latitude/longitude coordinates."""
    # Create a cube with latitude and longitude coordinates
    data_arr = np.zeros((10, 10))

    lat_coord = iris.coords.DimCoord(
        points=np.linspace(-90, 90, 10),
        standard_name="latitude",
        var_name="latitude",
        units="degrees",
    )
    lon_coord = iris.coords.DimCoord(
        points=np.linspace(-180, 180, 10),
        standard_name="longitude",
        var_name="longitude",
        units="degrees",
    )

    coords = (lat_coord, lon_coord)
    dim_coords_and_dims = [(coord, dim) for dim, coord in enumerate(coords)]
    cube = iris.cube.Cube(
        data=data_arr,
        dim_coords_and_dims=dim_coords_and_dims,
        long_name="Precipitation test",
    )

    with pytest.raises(ValueError):
        feature._check_xy_coords(cube)
