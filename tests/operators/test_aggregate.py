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

"""Test aggregate operators."""

import iris
import iris.cube
import numpy as np
import pytest

from CSET.operators import aggregate


def test_aggregate(cube):
    """Aggregate time to 2 hour intervals."""
    # Set test interval to 2 hours.
    interval = "PT2H"

    # Introduces new coordinate for cube based on existing
    # coordinate which has equal or less increments.

    # Test adding further coordinate.
    aggregated_cube = aggregate.time_aggregate(
        cube.copy(), method="SUM", interval_iso=interval
    )

    # Check if number of coords on aggregated cube is same as original cube.
    assert len(aggregated_cube.coords()) == len(cube.coords()), (
        "aggregated cube does not have additional aux coordinate"
    )


def test_ensure_aggregatable_across_cases_true_aggregatable_cube(
    long_forecast_multi_day,
):
    """Check that an aggregatable cube is returned with no changes."""
    cubes = aggregate.ensure_aggregatable_across_cases(long_forecast_multi_day)
    assert len(cubes) == 1
    cube = cubes[0]
    assert np.allclose(
        cube.data,
        long_forecast_multi_day.data,
        rtol=1e-06,
        atol=1e-02,
    )


def test_ensure_aggregatable_across_cases_false_aggregatable_cube(long_forecast):
    """Check that a non-aggregatable cube raises an error."""
    with pytest.raises(ValueError):
        aggregate.ensure_aggregatable_across_cases(long_forecast)


def test_ensure_aggregatable_across_cases_cubelist(
    long_forecast_many_cubes, long_forecast_multi_day
):
    """Check that a CubeList turns into an aggregatable Cube."""
    output_data = aggregate.ensure_aggregatable_across_cases(long_forecast_multi_day)
    assert isinstance(output_data, iris.cube.CubeList)
    assert len(output_data) == 1

    # Check output is a Cube.
    output_data = aggregate.ensure_aggregatable_across_cases(long_forecast_many_cubes)
    assert isinstance(output_data, iris.cube.CubeList)
    assert len(output_data) == 1
    cube = output_data[0]
    assert isinstance(cube, iris.cube.Cube)
    # Check output is identical to a pre-calculated cube.
    pre_calculated_data = long_forecast_multi_day
    assert np.allclose(
        pre_calculated_data.data,
        cube.data,
        rtol=1e-06,
        atol=1e-02,
    )


def test_ensure_aggregatable_across_cases_different_buckets(
    long_forecast_multi_day: iris.cube.Cube,
):
    """Check that incompatible cubes are made separately aggregatable."""
    other = long_forecast_multi_day.copy()
    other.rename("other_variable")
    cubes = iris.cube.CubeList([long_forecast_multi_day, other])
    output = aggregate.ensure_aggregatable_across_cases(cubes)
    assert isinstance(output, iris.cube.CubeList)
    assert len(output) == 2


def test_add_hour_coordinate(long_forecast):
    """Check that a Cube has an hour coordinate added to it."""
    cube_with_hour_coordinate = aggregate.add_hour_coordinate(long_forecast)
    hour_coord = cube_with_hour_coordinate.coord("hour")
    assert hour_coord
    assert hour_coord.units == "hours"
    assert len(set(hour_coord.points)) == 24


def test_add_hour_coordinate_cubelist(long_forecast_many_cubes):
    """Check that a CubeList has hour coordinates added to it."""
    cubes_with_hour_coordinate = aggregate.add_hour_coordinate(long_forecast_many_cubes)
    assert isinstance(cubes_with_hour_coordinate, iris.cube.CubeList)
    for cube in cubes_with_hour_coordinate:
        hour_coord = cube.coord("hour")
        assert hour_coord
        assert hour_coord.units == "hours"
        assert len(set(hour_coord.points)) == 24
