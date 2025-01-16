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

"""Test collapse operators."""

import iris
import iris.cube
import pytest

from CSET.operators import collapse


@pytest.fixture()
def long_forecast() -> iris.cube.Cube:
    """Get long_forecast to run tests on."""
    return iris.load_cube(
        "tests/test_data/long_forecast_air_temperature.nc", "air_temperature"
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
