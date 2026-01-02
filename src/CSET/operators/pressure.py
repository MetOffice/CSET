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

"""Operators for pressure conversions."""

import iris.cube
import numpy as np

from CSET._common import iter_maybe
from CSET.operators.atmospheric_constants import E0


def vapour_pressure(
    temperature: iris.cube.Cube | iris.cube.CubeList,
) -> iris.cube.Cube | iris.cube.CubeList:
    """Calculate the vapour pressure of the atmosphere."""
    vapour_pressure = iris.cube.CubeList([])
    for T in iter_maybe(temperature):
        es = T.copy()
        exponent = 17.27 * (T - 273.16) / (T - 35.86)
        es.data[:] = E0 * np.exp(exponent.core_data())
        vapour_pressure.append(es)
    if len(vapour_pressure) == 1:
        return vapour_pressure[0]
    else:
        return vapour_pressure
