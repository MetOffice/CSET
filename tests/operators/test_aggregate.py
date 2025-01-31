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
    assert np.allclose(
        aggregate.ensure_aggregatable_across_cases(long_forecast_multi_day).data,
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
    # Check output is a Cube.
    output_data = aggregate.ensure_aggregatable_across_cases(long_forecast_many_cubes)
    assert isinstance(output_data, iris.cube.Cube)
    # Check output can be aggregated in time.
    assert isinstance(
        aggregate.ensure_aggregatable_across_cases(output_data), iris.cube.Cube
    )
    # Check output is identical to a pre-calculated cube.
    pre_calculated_data = long_forecast_multi_day
    assert np.allclose(
        pre_calculated_data.data,
        output_data.data,
        rtol=1e-06,
        atol=1e-02,
    )
