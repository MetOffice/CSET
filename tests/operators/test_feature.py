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
import os

import cf_units
import iris
import iris.coords
import iris.cube
import numpy as np
import pytest
from simpletrack import Tracker
from simpletrack.frame import Timeline

from CSET.operators import feature


@pytest.fixture(scope="session")
def feature_cube() -> iris.cube.Cube:
    """Set up three timesteps of data and place into cube."""
    data_arr = np.zeros((3, 10, 10))
    data_arr[0, 2:6, 2:6] = 5
    data_arr[1, 3:7, 3:7] = 10
    data_arr[2, 4:8, 4:8] = 20

    time_units = cf_units.Unit("days since 2000-01-01 00:00:00", calendar="gregorian")
    time_start = dt.datetime(2010, 1, 1, 0, 0, 0)
    time_dt_points = [time_start + dt.timedelta(minutes=5 * idx) for idx in range(3)]
    time_points = [time_units.date2num(time_point) for time_point in time_dt_points]
    time_coord = iris.coords.DimCoord(
        points=time_points, standard_name="time", units=time_units
    )
    fcst_ref_coord = iris.coords.AuxCoord(
        points=time_start, standard_name="forecast_reference_time", units=time_units
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
    attributes = {"title": "Precipitation test"}
    cube = iris.cube.Cube(
        data=data_arr,
        dim_coords_and_dims=dim_coords_and_dims,
        long_name="Precipitation test",
        attributes=attributes,
        aux_coords_and_dims=[(fcst_ref_coord, None)],
    )
    return cube


@pytest.fixture(scope="session")
def cell_stats_timeline(feature_cube) -> Timeline:
    """Run feature tracking on feature_cube and return Timeline object."""
    # Setup config
    tracker_config = {
        "FEATURE": {
            "threshold": 1,
            "under_threshold": False,
            "min_size": 4,
        },
        "OUTPUT": {
            "save_data": False,
            "experiment_name": "feature_tracking",
            "path": f"{os.getcwd()}/model/cell-stats_data",
            "skip_tracking": True,
        },
    }

    # Get cube data into a dict to pass to Tracker
    times = feature_cube.coord("time").points
    time_units = feature_cube.coord("time").units
    times_dt = [time_units.num2pydate(t) for t in times]
    cube_dict = {
        time: cube_slice.data
        for time, cube_slice in zip(
            times_dt, feature_cube.slices_over("time"), strict=True
        )
    }

    # Run tracking, returning Timeline object
    timeline = Tracker(tracker_config).run(cube_dict)
    return timeline


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
    output_directory = f"{tmp_working_dir}/tracking_data"
    expected_file = f"{output_directory}/lifetime_20100101_0000.field"
    assert os.path.isfile(expected_file)

    # Check expected csv file is created in output directory
    expected_file = f"{output_directory}/frame_20100101_0000.csv"
    assert os.path.isfile(expected_file)


def test_cell_stats_operator(feature_cube, tmp_working_dir):
    """
    Test the cell_stats operator returns expected size, mean, and max values.

    The expected values are based on the feature_cube data and the threshold of 0.5.
    """
    threshold = 0.5
    min_size = 1
    cubelist = feature.cell_stats(
        cubes=feature_cube, threshold=threshold, min_size=min_size, save_data=True
    )

    # Extract data from cubelist, squeeze since there is only one feature per timestep
    # in this test case
    size_data = np.squeeze(cubelist.extract_cube("feature_size").data)
    mean_data = np.squeeze(cubelist.extract_cube("feature_mean").data)
    max_data = np.squeeze(cubelist.extract_cube("feature_max").data)
    effective_radius_data = np.squeeze(
        cubelist.extract_cube("feature_effective_radius").data
    )

    # Expected values based on the feature_cube data
    expected_size_data = np.array([16, 16, 16])  # Each feature is a 4x4 square
    expected_mean_data = np.array([5.0, 10.0, 20.0])  # Mean values of each feature
    expected_max_data = np.array([5.0, 10.0, 20.0])  # Max values of each feature

    grid_spacing = 10  # Assuming grid spacing is 10 meters from test setup
    expected_radius_data = np.sqrt(expected_size_data * grid_spacing**2 / np.pi)
    # Convert to km
    expected_radius_data = expected_radius_data / 1000

    np.testing.assert_array_equal(size_data, expected_size_data)
    np.testing.assert_array_equal(mean_data, expected_mean_data)
    np.testing.assert_array_equal(max_data, expected_max_data)
    np.testing.assert_array_almost_equal(effective_radius_data, expected_radius_data)
    output_directory = tmp_working_dir / "None/cell-stats_data"
    expected_file = output_directory / "lifetime_20100101_0000.field"
    assert expected_file.is_file()

    # Check expected csv file is created in output directory
    expected_file = output_directory / "frame_20100101_0000.csv"
    assert expected_file.is_file()


def test_cell_stats_invalid_threshold_list(feature_cube):
    """Test that cell_stats raises a ValueError if passed a list of wrong size."""
    invalid_thresholds = [0.5, 1.0]
    with pytest.raises(ValueError):
        feature.cell_stats(cubes=feature_cube, threshold=invalid_thresholds, min_size=1)


def test_check_uniform_grid(feature_cube) -> None:
    """Test that _check_uniform_grid does not raise an error for valid uniform grid."""
    result = feature._check_uniform_grid(feature_cube)
    assert result is True


def test_check_uniform_grid_invalid() -> None:
    """Test that _check_uniform_grid raises a ValueError for invalid uniform grid."""
    # Create a cube with non-uniform grid
    data_arr = np.zeros((10, 10))
    lat_points = np.linspace(-90, 90, 10)
    lat_points[-1] = 95

    lat_coord = iris.coords.DimCoord(
        points=lat_points,
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

    result = feature._check_uniform_grid(cube)
    assert result is False


def test_get_cell_stats_arrays_from_timeline(cell_stats_timeline):
    """Test that _get_cell_stats_arrays_from_timeline returns expected arrays."""
    expected_frame_times = [
        dt.datetime(2010, 1, 1, 0, 0, 0),
        dt.datetime(2010, 1, 1, 0, 5, 0),
        dt.datetime(2010, 1, 1, 0, 10, 0),
    ]

    size_array, mean_array, max_array = feature._get_cell_stats_arrays_from_timeline(
        cell_stats_timeline, expected_frame_times
    )

    # Expected values based on the feature_cube data and the threshold of 0.5
    expected_size_array = np.array([[16], [16], [16]])  # Each feature is a 4x4 square
    expected_mean_array = np.array([[5], [10], [20]])  # Mean values of each feature
    expected_max_array = np.array([[5], [10], [20]])  # Max values of each feature

    np.testing.assert_array_equal(size_array, expected_size_array)
    np.testing.assert_array_equal(mean_array, expected_mean_array)
    np.testing.assert_array_equal(max_array, expected_max_array)


def test_get_effective_radius_from_feature_size(feature_cube):
    """Test that _get_effective_radius_from_feature_size returns expected values."""
    # Use the same size data from above test
    size_data = np.array([[16], [16], [16]])  # Each feature is a 4x4 square

    effective_radius_data, grid_spacing = (
        feature._get_effective_radius_from_feature_size(size_data, feature_cube)
    )

    # Expected values based on the feature_cube data
    grid_spacing = 10  # Assuming grid spacing is 10 meters from test setup
    expected_radius_data = np.sqrt(size_data * grid_spacing**2 / np.pi)
    # Convert to km
    expected_radius_data = expected_radius_data / 1000

    np.testing.assert_array_almost_equal(effective_radius_data, expected_radius_data)
    assert grid_spacing == 10


def test_get_effective_radius_from_feature_size_km_input_cube(feature_cube):
    """Test that _get_effective_radius_from_feature_size returns expected values for km input cube."""
    # Use the same size data from above test
    size_data = np.array([[16], [16], [16]])  # Each feature is a 4x4 square

    # Convert cube to km units
    feature_cube_km = feature_cube.copy()
    feature_cube_km.coord("projection_x_coordinate").convert_units("km")
    feature_cube_km.coord("projection_y_coordinate").convert_units("km")

    effective_radius_data, grid_spacing = (
        feature._get_effective_radius_from_feature_size(size_data, feature_cube_km)
    )

    # Expected values based on the feature_cube data
    grid_spacing = 0.01  # Assuming grid spacing is 10 meters (0.01 km) from test setup
    expected_radius_data = np.sqrt(size_data * grid_spacing**2 / np.pi)

    np.testing.assert_array_almost_equal(effective_radius_data, expected_radius_data)
    assert grid_spacing == 0.01


def test_get_effective_radius_from_feature_size_latlon_cube():
    """Test that _get_effective_radius_from_feature_size returns expected values for lat/lon cube."""
    # Create a cube with lat/lon coordinates
    data_arr = np.zeros((10, 10))
    lat_points = np.linspace(-1, 1, 10)
    lon_points = np.linspace(-1, 1, 10)

    lat_coord = iris.coords.DimCoord(
        points=lat_points,
        standard_name="latitude",
        var_name="latitude",
        units="degrees",
    )
    lon_coord = iris.coords.DimCoord(
        points=lon_points,
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

    # Use the same size data from above test
    size_data = np.array([[2], [2], [2]])  # Each feature is a 4x4 square

    effective_radius_data, grid_spacing = (
        feature._get_effective_radius_from_feature_size(size_data, cube)
    )

    # Expected values based on the feature_cube data
    # For lat/lon cube, grid spacing is calculated based on the distance between points
    # Expected grid spacing is 2 degrees (222 km) / 9 intervals = 24.666 km
    expected_grid_spacing = 24.666
    expected_radius_data = np.sqrt(size_data * expected_grid_spacing**2 / np.pi)

    np.testing.assert_array_almost_equal(
        effective_radius_data, expected_radius_data, decimal=3
    )
    np.testing.assert_almost_equal(grid_spacing, expected_grid_spacing, decimal=3)


def test_add_cell_stats_data_to_cubes(cell_stats_timeline, feature_cube):
    """Test that _add_cell_stats_data_to_cubes adds expected data to cubelist."""
    expected_frame_times = [
        dt.datetime(2010, 1, 1, 0, 0, 0),
        dt.datetime(2010, 1, 1, 0, 5, 0),
        dt.datetime(2010, 1, 1, 0, 10, 0),
    ]

    # Get feature data from each frame of data
    size_data, mean_data, max_data = feature._get_cell_stats_arrays_from_timeline(
        timeline=cell_stats_timeline, expected_frame_times=expected_frame_times
    )

    # Get effective radius from feature size, using horizontal coordinate of input cube to estimate grid spacing
    effective_radius_data, __ = feature._get_effective_radius_from_feature_size(
        size_data=size_data, cube_with_hzntl_coord=feature_cube
    )

    cube_properties = {
        "feature_size": {
            "data": size_data,
            "long_name": "feature_size",
            "units": 1,
        },
        "feature_mean": {
            "data": mean_data,
            "long_name": "feature_mean",
            "units": 1,
        },
        "feature_max": {"data": max_data, "long_name": "feature_max", "units": 1},
        "feature_effective_radius": {
            "data": effective_radius_data,
            "long_name": "feature_effective_radius",
            "units": "km",
        },
    }

    cubelist = feature._add_cell_stats_data_to_cubes(cube_properties, feature_cube)

    # Test a cube of each name is produced
    expected_cube_names = [
        "feature_size",
        "feature_mean",
        "feature_max",
        "feature_effective_radius",
    ]

    for cube_name in expected_cube_names:
        assert any(cube.long_name == cube_name for cube in cubelist)

    # Check each cube contains a forecast_reference_time coordinate, copied from
    # feature_cube
    for cube in cubelist:
        assert cube.coords("forecast_reference_time")

    # test cube attributes copied to cell stats cubes
    for cube in cubelist:
        assert cube.attributes == feature_cube.attributes
