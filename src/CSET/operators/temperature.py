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

"""Operators for temperature conversions."""

import iris.cube
import numpy as np

from CSET._common import iter_maybe
from CSET.operators.constants import T0
from CSET.operators.pressure import vapour_pressure


def dewpoint(
    temperature: iris.cube.Cube | iris.cube.CubeList,
    relative_humidity: iris.cube.Cube | iris.cube.CubeList,
) -> iris.cube.Cube | iris.cube.CubeList:
    """Calculate the dewpoint temperature."""
    Td = iris.cube.CubeList([])
    for T, RH in zip(
        iter_maybe(temperature), iter_maybe(relative_humidity), strict=True
    ):
        vp = vapour_pressure(T, RH)
        td = vp.copy()
        td.data = (243.5 * np.log(vp.core_data()) - 440.8) / (
            19.48 - np.log(vp.core_data())
        )
        td.data[td.data - T0 < -35.0] = np.nan
        td.data[td.data - T0 > 35.0] = np.nan
        td.units("K")
        td.rename("dewpoint temperature")
        Td.append(td)
    if len(Td) == 1:
        return Td[0]
    else:
        return Td
