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
from CSET.operators._atmospheric_constants import E0, KAPPA, P0
from CSET.operators.misc import convert_units


def vapour_pressure(
    temperature: iris.cube.Cube | iris.cube.CubeList,
) -> iris.cube.Cube | iris.cube.CubeList:
    """Calculate the vapour pressure of the atmosphere."""
    v_pressure = iris.cube.CubeList([])
    for T in iter_maybe(temperature):
        es = T.copy()
        exponent = 17.27 * (T - 273.16) / (T - 35.86)
        es.data[:] = E0 * np.exp(exponent.core_data())
        es.units = "hPa"
        es.rename("vapour_pressure")
        v_pressure.append(es)
    if len(v_pressure) == 1:
        return v_pressure[0]
    else:
        return v_pressure


def vapour_pressure_from_RH(
    temperature: iris.cube.Cube | iris.cube.CubeList,
    relative_humidity: iris.cube.Cube | iris.cube.CubeList,
) -> iris.cube.Cube | iris.cube.CubeList:
    """Calculate the vapour pressure using RH."""
    v_pressure = iris.cube.CubeList([])
    for T, RH in zip(
        iter_maybe(temperature), iter_maybe(relative_humidity), strict=True
    ):
        RH = convert_units(RH, "1")
        vp = vapour_pressure(T) * RH
        v_pressure.append(vp)
    if len(v_pressure) == 1:
        return v_pressure[0]
    else:
        return v_pressure


def exner_pressure(
    pressure: iris.cube.Cube | iris.cube.CubeList,
) -> iris.cube.Cube | iris.cube.CubeList:
    """Calculate the exner pressure."""
    pi = iris.cube.CubeList([])
    for P in iter_maybe(pressure):
        PI = P.copy()
        PI.data[:] = (P.core_data() / P0) ** KAPPA
        PI.rename("exner_pressure")
        PI.units = "1"
        pi.append(PI)
    if len(pi) == 1:
        return pi[0]
    else:
        return pi
