# Copyright 2022 Met Office and contributors.
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

from CSET.operators import read


def test_read_cubes():
    """Read cube and verify."""
    cubes = read.read_cubes("tests/test_data/air_temp.nc")
    assert len(cubes) == 3
    possible_cubes = [
        "<iris 'Cube' of air_temperature / (K) (time: 2; grid_latitude: 17; grid_longitude: 13)>",
        "<iris 'Cube' of air_temperature / (K) (time: 3; grid_latitude: 17; grid_longitude: 13)>",
    ]
    for cube in cubes:
        assert repr(cube) in possible_cubes
