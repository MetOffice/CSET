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

"""Operators for humidity conversions."""

import iris.cube

from CSET._common import iter_maybe


def specific_humidity_to_mixing_ratio(
    cubes: iris.cube.Cube | iris.cube.CubeList,
) -> iris.cube.Cube | iris.cube.CubeList:
    """Convert specific humidity to mixing ratio."""
    w = iris.cube.CubeList([])
    for cube in iter_maybe(cubes):
        mr = cube.copy()
        mr = cube / (1 - cube)
        mr.rename("mixing_ratio")
        w.append(mr)
    if len(w) == 1:
        return w[0]
    else:
        return w
