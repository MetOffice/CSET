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
