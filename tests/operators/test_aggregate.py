# Copyright 2023 Met Office and contributors.
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

from CSET.operators import aggregate, constraints, filters, read


def test_aggregate():
    """Aggregate time to 2 hour intervals."""
    # Set test interval to 2 hours.
    interval = "PT2H"

    # Introduces new coordinate for cube based on existing
    # coordinate which has equal or less increments.
    cubes = read.read_cubes("tests/test_data/air_temp.nc")
    constraint = constraints.combine_constraints(
        constraints.generate_stash_constraint("m01s03i236"),
        a=constraints.generate_cell_methods_constraint([]),
    )
    cube = filters.filter_cubes(cubes, constraint)

    # Test adding further coordinate.
    aggregated_cube = aggregate.time_aggregate(
        cube, method="SUM", interval_iso=interval
    )

    # Check if number of aux coords on aggregated cube is
    # by 1 greater than original cube.
    assert (
        len(aggregated_cube.aux_coords) == len(cube.aux_coords) + 1
    ), "aggregated cube does not have additional aux coordinate"
