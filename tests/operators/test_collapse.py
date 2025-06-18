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

"""Test collapse operators."""

import datetime

import iris
import iris.cube
import numpy as np
import pytest

from CSET.operators import collapse


@pytest.fixture()
def medium_forecast() -> iris.cube.Cube:
    """Get medium forecast with monotonic time coordinate."""
    return iris.load_cube(
        "tests/test_data/medium_forecast_air_temp_monotonic.nc", "air_temperature"
    )


def test_collapse(cube):
    """Reduces dimension of cube."""
    # Test collapsing a single coordinate.
    collapsed_cube = collapse.collapse(cube, "time", "MEAN")
    expected_cube = (
        "<iris 'Cube' of air_temperature / (K) (grid_latitude: 17; grid_longitude: 13)>"
    )
    assert repr(collapsed_cube) == expected_cube

    # Test collapsing two coordinates.
    collapsed_cube = collapse.collapse(
        cube, ["grid_latitude", "grid_longitude"], "MEAN"
    )
    expected_cube = "<iris 'Cube' of air_temperature / (K) (time: 3)>"
    assert repr(collapsed_cube) == expected_cube


def test_collapse_cubelist(cube):
    """Reduce dimensions of multiple cubes in a CubeList."""
    cubes = iris.cube.CubeList([cube, cube])
    collapsed_cubes = collapse.collapse(cubes, "time", "MEAN")
    assert len(collapsed_cubes) == 2
    expected_cube = (
        "<iris 'Cube' of air_temperature / (K) (grid_latitude: 17; grid_longitude: 13)>"
    )
    for collapsed_cube in collapsed_cubes:
        assert repr(collapsed_cube) == expected_cube


def test_collapse_percentile(cube):
    """Reduce dimension of a cube with a PERCENTILE aggregation."""
    with pytest.raises(ValueError, match="Must specify additional_percent"):
        collapse.collapse(cube, "time", "PERCENTILE")

    # Test collapsing a single coordinate.
    collapsed_cube = collapse.collapse(
        cube, "time", "PERCENTILE", additional_percent=75
    )
    expected_cube = (
        "<iris 'Cube' of air_temperature / (K) (grid_latitude: 17; grid_longitude: 13)>"
    )
    assert repr(collapsed_cube) == expected_cube


def test_collapse_by_hour_of_day(long_forecast):
    """Convert and aggregates time dimension by hour of day."""
    collapsed_cube = collapse.collapse_by_hour_of_day(long_forecast, "MEAN")
    expected_cube = "<iris 'Cube' of air_temperature / (K) (hour: 24; grid_latitude: 3; grid_longitude: 3)>"
    assert repr(collapsed_cube) == expected_cube


def test_collapse_by_hour_of_day_single_day(long_forecast):
    """Convert and aggregates time dimension by hour of day."""
    # Read in only first 24h of input data.
    day_long_forecast = long_forecast[0:24]
    collapsed_cube = collapse.collapse_by_hour_of_day(day_long_forecast, "MEAN")
    expected_cube = "<iris 'Cube' of air_temperature / (K) (hour: 24; grid_latitude: 3; grid_longitude: 3)>"
    assert repr(collapsed_cube) == expected_cube

    # Ensure data has changed position in cube (averaging 1-day only).
    # Input data spans T=3 through to T=2.
    assert collapsed_cube.data[0, 0, 0] == day_long_forecast.data[21, 0, 0]
    assert collapsed_cube.data[0, -1, -1] == day_long_forecast.data[21, -1, -1]

    # Select different segment from long_forecast input data.
    day_long_forecast_2 = long_forecast[56:80]
    collapsed_cube = collapse.collapse_by_hour_of_day(day_long_forecast_2, "MEAN")
    expected_cube = "<iris 'Cube' of air_temperature / (K) (hour: 24; grid_latitude: 3; grid_longitude: 3)>"
    assert repr(collapsed_cube) == expected_cube

    # Ensure cube data has changed position in cube (averaging 1-day only).
    # Input data spans T=11 through to T=10
    assert collapsed_cube.data[0, 0, 0] == day_long_forecast_2.data[13, 0, 0]
    assert collapsed_cube.data[0, -1, -1] == day_long_forecast_2.data[13, -1, -1]


def test_collapse_by_hour_of_day_cubelist(long_forecast):
    """Collapsing a CubeList by hour of day collapses each cube separately."""
    cubes = iris.cube.CubeList([long_forecast, long_forecast.copy()])
    collapsed_cubes = collapse.collapse_by_hour_of_day(cubes, "MEAN")
    assert isinstance(collapsed_cubes, iris.cube.CubeList)
    assert len(collapsed_cubes) == 2
    expected_cube = "<iris 'Cube' of air_temperature / (K) (hour: 24; grid_latitude: 3; grid_longitude: 3)>"
    for collapsed_cube in collapsed_cubes:
        assert repr(collapsed_cube) == expected_cube


def test_collapse_by_hour_of_day_single_cubelist(long_forecast):
    """Check single CubeList input collapsed by hour of day."""
    # Test single cubelist entry.
    cubes = iris.cube.CubeList([long_forecast])
    collapsed_cube = collapse.collapse_by_hour_of_day(cubes, "MEAN")
    expected_cube = "<iris 'Cube' of air_temperature / (K) (hour: 24; grid_latitude: 3; grid_longitude: 3)>"
    assert repr(collapsed_cube) == expected_cube


def test_collapse_by_hour_of_day_percentile(long_forecast):
    """Convert and aggregate time dimension by hour of day with percentiles."""
    # Test collapsing long forecast.
    collapsed_cube = collapse.collapse_by_hour_of_day(
        long_forecast, "PERCENTILE", additional_percent=[25, 75]
    )
    expected_cube = "<iris 'Cube' of air_temperature / (K) (percentile_over_hour: 2; hour: 24; grid_latitude: 3; grid_longitude: 3)>"
    assert repr(collapsed_cube) == expected_cube


def test_collapse_by_hour_of_day_percentile_fail(long_forecast):
    """Test failing due to non-specified additional_percent."""
    with pytest.raises(ValueError, match="Must specify additional_percent"):
        collapse.collapse_by_hour_of_day(long_forecast, "PERCENTILE")


def test_collapse_by_hour_of_day_multi_forecast_cube(long_forecast_multi_day):
    """Convert and aggregates time dimension by hour of day for a multi day cube."""
    collapsed_cube = collapse.collapse_by_hour_of_day(long_forecast_multi_day, "MEAN")
    expected_cube = "<iris 'Cube' of air_temperature / (K) (hour: 24; grid_latitude: 3; grid_longitude: 3)>"
    assert repr(collapsed_cube) == expected_cube


def test_collapse_by_hour_of_day_multi_forecast_single_day(long_forecast_multi_day):
    """Test time averaging and data rolling correct for collapse_hour_of_day."""
    # Ensure data components are as expected, working with first 24h inputs.
    long_forecast_pick_day = long_forecast_multi_day[0:24]
    collapsed_cube = collapse.collapse_by_hour_of_day(long_forecast_pick_day, "MEAN")
    expected_cube = "<iris 'Cube' of air_temperature / (K) (hour: 24; grid_latitude: 3; grid_longitude: 3)>"
    assert repr(collapsed_cube) == expected_cube

    # Ensure cube data has changed position in cube (averaging 1-day only).
    # First initialisation segment in input spans T=3 through to T=2.
    # Second initialisation segment in input spans T=15 through to T=14.
    # Third initialisation segment in input spans T=3 through to T=2.
    calc_mean = (
        long_forecast_pick_day.data[21, 0, 0, 0]
        + long_forecast_pick_day.data[9, 1, 0, 0]
        + long_forecast_pick_day.data[21, 2, 0, 0]
    ) / 3.0
    assert collapsed_cube.data[0, 0, 0] == calc_mean
    calc_mean2 = (
        long_forecast_pick_day.data[21, 0, -1, -1]
        + long_forecast_pick_day.data[9, 1, -1, -1]
        + long_forecast_pick_day.data[21, 2, -1, -1]
    ) / 3.0
    assert collapsed_cube.data[0, -1, -1] == calc_mean2

    # Select different segment from long_forecast input data.
    # First segment T=1 to T=0. Second T=13 to T=12. Third T=1 to T=0.
    long_forecast_pick_day2 = long_forecast_multi_day[22:46]
    collapsed_cube = collapse.collapse_by_hour_of_day(long_forecast_pick_day2, "MEAN")
    calc_mean = (
        long_forecast_pick_day2.data[23, 0, 0, 0]
        + long_forecast_pick_day2.data[11, 1, 0, 0]
        + long_forecast_pick_day2.data[23, 2, 0, 0]
    ) / 3.0
    assert collapsed_cube.data[0, 0, 0] == calc_mean
    calc_mean2 = (
        long_forecast_pick_day2.data[23, 0, -1, -1]
        + long_forecast_pick_day2.data[11, 1, -1, -1]
        + long_forecast_pick_day2.data[23, 2, -1, -1]
    ) / 3.0
    assert collapsed_cube.data[0, -1, -1] == calc_mean2


def test_collapse_by_lead_time_single_cube(long_forecast_multi_day):
    """Check cube collapse by lead time."""
    calculated_cube = collapse.collapse(
        long_forecast_multi_day, "forecast_reference_time", "MEAN"
    )
    assert np.allclose(
        calculated_cube.data,
        collapse.collapse(
            long_forecast_multi_day, "forecast_reference_time", "MEAN"
        ).data,
        rtol=1e-06,
        atol=1e-02,
    )


def test_collapse_by_hour_of_day_multi_non_overlapping(long_forecast_multi_day):
    """Identify when inputs have non-overlapping cubes."""
    print(long_forecast_multi_day)
    cube_day1 = long_forecast_multi_day[0:24, 0, :, :]
    cube_day2 = long_forecast_multi_day[24:48, 2, :, :]
    print(cube_day1.coord("time"))
    print(cube_day2.coord("time"))
    non_overlap_cubelist = iris.cube.CubeList([cube_day1, cube_day2])
    with pytest.raises(
        ValueError, match="No overlapping times detected in input cubes."
    ):
        collapse.collapse_by_hour_of_day(non_overlap_cubelist, "MEAN")


def test_collapse_by_lead_time_single_cube_percentile_fail(long_forecast_multi_day):
    """Test fail by not setting additional percent."""
    with pytest.raises(ValueError, match="Must specify additional_percent"):
        collapse.collapse(
            long_forecast_multi_day, "forecast_reference_time", "PERCENTILE"
        )


def test_collapse_by_validity_time(long_forecast_multi_day):
    """Reduce a dimension of a cube by validity time."""
    collapsed_cube = collapse.collapse_by_validity_time(long_forecast_multi_day, "MEAN")
    expected_cube = "<iris 'Cube' of air_temperature / (K) (time: 145; grid_latitude: 3; grid_longitude: 3)>"
    assert repr(collapsed_cube) == expected_cube


def test_collapse_by_validity_time_cubelist(long_forecast_multi_day):
    """Collapsing a CubeList by validity time collapses each cube separately."""
    cubes = iris.cube.CubeList(
        [long_forecast_multi_day, long_forecast_multi_day.copy()]
    )
    collapsed_cubes = collapse.collapse_by_validity_time(cubes, "MEAN")
    assert isinstance(collapsed_cubes, iris.cube.CubeList)
    assert len(collapsed_cubes) == 2
    expected_cube = "<iris 'Cube' of air_temperature / (K) (time: 145; grid_latitude: 3; grid_longitude: 3)>"
    for collapsed_cube in collapsed_cubes:
        assert repr(collapsed_cube) == expected_cube


def test_collapse_by_validity_time_no_time_coordinate(long_forecast_multi_day):
    """Collapse a cube without a time coordinate by validity time."""
    long_forecast_multi_day.remove_coord("time")
    collapsed_cube = collapse.collapse_by_validity_time(long_forecast_multi_day, "MEAN")
    expected_cube = "<iris 'Cube' of air_temperature / (K) (time: 145; grid_latitude: 3; grid_longitude: 3)>"
    assert repr(collapsed_cube) == expected_cube


def test_collapse_by_validity_time_no_common_points(cube):
    """Test exception when there are no common time points between cubes."""
    c1 = cube.extract(iris.Constraint(time=datetime.datetime(2022, 9, 21, 2, 30)))
    c2 = cube.extract(iris.Constraint(time=datetime.datetime(2022, 9, 21, 4, 30)))
    cubes = iris.cube.CubeList([c1, c2])
    with pytest.raises(
        ValueError,
        match="Cubes do not overlap therefore cannot collapse across validity time.",
    ):
        collapse.collapse_by_validity_time(cubes, "MEAN")


def test_collapse_by_validity_time_percentile(long_forecast_multi_day):
    """Reduce by validity time with percentiles."""
    # Test successful collapsing by validity time.
    collapsed_cube = collapse.collapse_by_validity_time(
        long_forecast_multi_day, "PERCENTILE", additional_percent=[25, 75]
    )
    expected_cube = "<iris 'Cube' of air_temperature / (K) (percentile_over_equalised_validity_time: 2; time: 145; grid_latitude: 3; grid_longitude: 3)>"
    assert repr(collapsed_cube) == expected_cube


def test_collapse_by_validity_time_percentile_fail(long_forecast_multi_day):
    """Test not specifying additional percent fails."""
    with pytest.raises(ValueError, match="Must specify additional_percent"):
        collapse.collapse_by_validity_time(long_forecast_multi_day, "PERCENTILE")
