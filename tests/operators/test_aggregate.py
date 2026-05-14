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
    cubes = aggregate.ensure_aggregatable_across_cases(
        long_forecast_multi_day, time_coord_name="time"
    )
    assert len(cubes) == 1
    cube = cubes[0]
    assert np.allclose(
        cube.data,
        long_forecast_multi_day.data,
        rtol=1e-06,
        atol=1e-02,
    )


def test_ensure_aggregatable_across_cases_false_aggregatable_cube(cardington_cube):
    """Check that a non-aggregatable cube raises an error."""
    with pytest.raises(ValueError):
        aggregate.ensure_aggregatable_across_cases(
            cardington_cube, time_coord_name="time"
        )


def test_ensure_aggregatable_across_cases_cubelist(
    long_forecast_many_cubes, long_forecast_multi_day
):
    """Check that a CubeList turns into an aggregatable Cube."""
    output_data = aggregate.ensure_aggregatable_across_cases(
        long_forecast_multi_day, time_coord_name="time"
    )
    assert isinstance(output_data, iris.cube.CubeList)
    assert len(output_data) == 1

    # Check output is a Cube.
    output_data = aggregate.ensure_aggregatable_across_cases(
        long_forecast_many_cubes, time_coord_name="time"
    )
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
    output = aggregate.ensure_aggregatable_across_cases(cubes, time_coord_name="time")
    assert isinstance(output, iris.cube.CubeList)
    assert len(output) == 2


def test_ensure_aggregatable_across_cube_coord_attribute(long_forecast_multi_day):
    """Check that aggregatable cubes preserve information on Ncases."""
    print(long_forecast_multi_day)
    output_data = aggregate.ensure_aggregatable_across_cases(
        long_forecast_multi_day, time_coord_name="time"
    )
    print(output_data)
    assert output_data[0].coord("time").attributes["number_reference_times"] == 3


def test_ensure_aggregatable_across_cases_coord_attribute(long_forecast_many_cubes):
    """Check that aggregatable cubes preserve information on Ncases."""
    output_data = aggregate.ensure_aggregatable_across_cases(
        long_forecast_many_cubes, time_coord_name="time"
    )
    assert output_data[0].coord("time").attributes["number_reference_times"] == 3


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


def test_rolling_window_time_aggregation(long_forecast):
    """Check that a rolling maximum is found in a cube."""
    expected_cube = long_forecast.rolling_window("time", iris.analysis.MAX, 24)
    actual_cube = aggregate.rolling_window_time_aggregation(long_forecast, "MAX", 24)
    # Ensure expected and actual cubes are the same shape.
    assert expected_cube.shape == actual_cube.shape
    # Ensure rolling window has applied so shapes differ by window size -1 from original cube.
    assert actual_cube.shape[0] == long_forecast.shape[0] - 23
    # Ensure data is the same.
    assert np.allclose(expected_cube.data, actual_cube.data, rtol=1e-6, atol=1e-2)


def test_rolling_window_time_aggregation_cubelist(long_forecast):
    """Check that a rolling maximum is found in a cubelist."""
    cubelist = iris.cube.CubeList([long_forecast, long_forecast])
    actual_cubelist = aggregate.rolling_window_time_aggregation(cubelist, "MAX", 24)
    expected_cubes = iris.cube.CubeList([])
    for cube in cubelist:
        new_cube = cube.rolling_window("time", iris.analysis.MAX, 24)
        expected_cubes.append(new_cube)

    for cube_a, cube_b, cube_c in zip(
        actual_cubelist, expected_cubes, cubelist, strict=True
    ):
        assert cube_a.shape == cube_b.shape
        assert cube_a.shape[0] == cube_c.shape[0] - 23
        assert np.allclose(cube_a.data, cube_b.data, rtol=1e-6, atol=1e-2)


def test_aggregate_without_time_dimcoords_single_cube(cardington_cube):
    """Check that a single cube can be aggregated at a specific time."""
    cube_slice = cardington_cube[0]
    time_coord = cube_slice.coord("time")

    # Create a single time coordinate for aggregation
    single_time = iris.coords.DimCoord(
        [time_coord.points[0]], standard_name="time", units=time_coord.units
    )
    result = aggregate._aggregate_without_time_dimcoords(
        cube_slice, single_time, iris.analysis.MEAN, None
    )

    assert isinstance(result, iris.cube.CubeList)
    assert len(result) == 1

    # Check that num_cases coordinate was added
    assert result[0].coord("num_cases").points[0] == 1
    # Check data is unchanged
    assert np.allclose(result[0].data, cube_slice.data, rtol=1e-6, atol=1e-2)


def test_aggregate_without_time_dimcoords_cubelist(cardington_cube):
    """Check that a CubeList can be aggregated at a specific time."""
    cube1 = cardington_cube[0]
    cube2 = cardington_cube[0].copy()

    # Modify cube2 data slightly to test aggregation
    cube2.data = cube2.data * 1.5

    cubelist = iris.cube.CubeList([cube1, cube2])

    time_coord = cube1.coord("time")
    single_time = iris.coords.DimCoord(
        [time_coord.points[0]], standard_name="time", units=time_coord.units
    )

    result = aggregate._aggregate_without_time_dimcoords(
        cubelist, single_time, iris.analysis.MEAN, None
    )

    assert isinstance(result, iris.cube.CubeList)
    assert len(result) == 1

    # Check that num_cases coordinate was added with correct value
    assert result[0].coord("num_cases").points[0] == 2

    # Check data is the mean of the two cubes
    expected_data = (cube1.data + cube2.data) / 2
    assert np.allclose(result[0].data, expected_data, rtol=1e-6, atol=1e-2)


def test_aggregate_without_time_dimcoords_percentile(cardington_cube):
    """Check that PERCENTILE aggregator works correctly."""
    # Create three cubes with the same time but different data
    cube1 = cardington_cube[0].copy()
    cube2 = cardington_cube[0].copy()
    cube3 = cardington_cube[0].copy()
    cube1.data = np.full_like(cube1.data, 10.0)
    cube2.data = np.full_like(cube2.data, 20.0)
    cube3.data = np.full_like(cube3.data, 30.0)

    cubelist = iris.cube.CubeList([cube1, cube2, cube3])

    time_coord = cube1.coord("time")
    single_time = iris.coords.DimCoord(
        [time_coord.points[0]], standard_name="time", units=time_coord.units
    )

    # Aggregate at this time using 50th percentile
    result = aggregate._aggregate_without_time_dimcoords(
        cubelist, single_time, iris.analysis.PERCENTILE, 50
    )
    assert isinstance(result, iris.cube.CubeList)
    assert len(result) == 1
    # Check that num_cases coordinate was added
    assert result[0].coord("num_cases").points[0] == 3
    # Check data is the median (50th percentile) which should be 20.0
    expected_data = np.full_like(cube1.data, 20.0)
    assert np.allclose(result[0].data, expected_data, rtol=1e-6, atol=1e-2)


def test_aggregate_without_time_dimcoords_multiple_time_error(cardington_cube):
    """Check that ValueError is raised when time coordinate has multiple points."""
    cube = cardington_cube[0]

    # Create a time coordinate with multiple points (this should cause an error)
    time_coord = cube.coord("time")
    multiple_times = iris.coords.DimCoord(
        [time_coord.points[0], time_coord.points[0] + 1, time_coord.points[0] + 2],
        standard_name="time",
        units=time_coord.units,
    )

    with pytest.raises(
        ValueError, match="Time coordinate should specify a single time only"
    ):
        aggregate._aggregate_without_time_dimcoords(
            cube, multiple_times, iris.analysis.MEAN, None
        )


def test_aggregate_without_time_dimcoords_removes_duplicates(cardington_cube):
    """Check that duplicate cubes are removed before aggregation."""
    cube1 = cardington_cube[0]
    cube2 = cube1.copy()  # Exact duplicate

    cubelist = iris.cube.CubeList([cube1, cube2])

    time_coord = cube1.coord("time")
    single_time = iris.coords.DimCoord(
        [time_coord.points[0]], standard_name="time", units=time_coord.units
    )
    result = aggregate._aggregate_without_time_dimcoords(
        cubelist, single_time, iris.analysis.MEAN, None
    )

    # Check that num_cases is 1 (duplicates removed)
    assert result[0].coord("num_cases").points[0] == 1
    # Check data is unchanged
    assert np.allclose(result[0].data, cube1.data, rtol=1e-6, atol=1e-2)


def test_aggregate_without_time_dimcoords_removes_number_coord(cardington_cube):
    """Check that the temporary 'number' coordinate is removed from result."""
    cube = cardington_cube[0]
    time_coord = cube.coord("time")
    single_time = iris.coords.DimCoord(
        [time_coord.points[0]], standard_name="time", units=time_coord.units
    )

    result = aggregate._aggregate_without_time_dimcoords(
        cube, single_time, iris.analysis.MEAN, None
    )

    # Check that 'number' coordinate is not in the result
    coord_names = [coord.name() for coord in result[0].coords()]
    assert "number" not in coord_names
