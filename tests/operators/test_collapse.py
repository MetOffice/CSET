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

import iris
import iris.cube
import numpy as np
import pytest

from CSET.operators import collapse


@pytest.fixture()
def long_forecast() -> iris.cube.Cube:
    """Get long_forecast to run tests on."""
    return iris.load_cube(
        "tests/test_data/long_forecast_air_temp_fcst_1.nc", "air_temperature"
    )


@pytest.fixture()
def long_forecast_multi_day() -> iris.cube.Cube:
    """Get long_forecast_multi_day to run tests on."""
    return iris.load_cube(
        "tests/test_data/long_forecast_air_temp_multi_day.nc", "air_temperature"
    )


@pytest.fixture()
def long_forecast_many_cubes() -> iris.cube.Cube:
    """Get long_forecast_may_cubes to run tests on."""
    return iris.load(
        "tests/test_data/long_forecast_air_temp_fcst_*.nc", "air_temperature"
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


def test_collapse_percentile(cube):
    """Reduce dimension of a cube with a PERCENTILE aggregation."""
    with pytest.raises(ValueError):
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
    # Test collapsing a long forecast.
    collapsed_cube = collapse.collapse_by_hour_of_day(long_forecast, "MEAN")
    expected_cube = "<iris 'Cube' of air_temperature / (K) (-- : 24; grid_latitude: 3; grid_longitude: 3)>"
    assert repr(collapsed_cube) == expected_cube


def test_collapse_by_hour_of_day_percentile(long_forecast):
    """Convert and aggregate time dimension by hour of day with percentiles."""
    with pytest.raises(ValueError):
        collapse.collapse_by_hour_of_day(long_forecast, "PERCENTILE")
    # Test collapsing long forecast.
    collapsed_cube = collapse.collapse_by_hour_of_day(
        long_forecast, "PERCENTILE", additional_percent=[25, 75]
    )
    expected_cube = "<iris 'Cube' of air_temperature / (K) (percentile_over_hour: 2; -- : 24; grid_latitude: 3; grid_longitude: 3)>"
    assert repr(collapsed_cube) == expected_cube


def test_collapse_by_lead_time_single_cube(long_forecast_multi_day):
    """Check cube collapse by lead time."""
    calculated_cube = collapse.collapse(
        long_forecast_multi_day, "forecast_period", "MEAN"
    )
    assert np.allclose(
        calculated_cube.data,
        collapse.collapse_by_lead_time(long_forecast_multi_day, "MEAN").data,
        rtol=1e-06,
        atol=1e-02,
    )


def test_collapse_by_lead_time_cube_list(
    long_forecast_multi_day, long_forecast_many_cubes
):
    """Check CubeList is made into an aggregatable cube and collapses by lead time."""
    calculated_cube = collapse.collapse(
        long_forecast_multi_day, "forecast_period", "MEAN"
    )
    assert np.allclose(
        calculated_cube.data,
        collapse.collapse_by_lead_time(long_forecast_many_cubes, "MEAN").data,
        rtol=1e-06,
        atol=1e-02,
    )


def test_collapse_by_lead_time_single_cube_percentile(long_forecast_multi_day):
    """Check Cube collapse by lead time with percentiles."""
    calculated_cube = collapse.collapse(
        long_forecast_multi_day, "forecast_period", "PERCENTILE", additional_percent=75
    )
    with pytest.raises(ValueError):
        collapse.collapse_by_lead_time(long_forecast_multi_day, "PERCENTILE")
    assert np.allclose(
        calculated_cube.data,
        collapse.collapse_by_lead_time(
            long_forecast_multi_day, "PERCENTILE", additional_percent=75
        ).data,
        rtol=1e-06,
        atol=1e-02,
    )


def test_collapse_by_lead_time_cube_list_percentile(
    long_forecast_multi_day, long_forecast_many_cubes
):
    """Check CubeList is made into an aggregatable cube and collapses by lead time with percentiles."""
    calculated_cube = collapse.collapse(
        long_forecast_multi_day, "forecast_period", "PERCENTILE", additional_percent=75
    )
    with pytest.raises(ValueError):
        collapse.collapse_by_lead_time(long_forecast_many_cubes, "PERCENTILE")
    assert np.allclose(
        calculated_cube.data,
        collapse.collapse_by_lead_time(
            long_forecast_many_cubes, "PERCENTILE", additional_percent=75
        ).data,
        rtol=1e-06,
        atol=1e-02,
    )
