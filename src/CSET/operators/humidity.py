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
from CSET.operators._atmospheric_constants import EPSILON
from CSET.operators.misc import convert_units
from CSET.operators.pressure import vapour_pressure


def mixing_ratio_from_specific_humidity(
    specific_humidity: iris.cube.Cube | iris.cube.CubeList,
) -> iris.cube.Cube | iris.cube.CubeList:
    """Convert specific humidity to mixing ratio."""
    w = iris.cube.CubeList([])
    for q in iter_maybe(specific_humidity):
        mr = q.copy()
        mr = q / (1 - q)
        mr.rename("mixing_ratio")
        w.append(mr)
    if len(w) == 1:
        return w[0]
    else:
        return w


def specific_humidity_from_mixing_ratio(
    mixing_ratio: iris.cube.Cube | iris.cube.CubeList,
) -> iris.cube.Cube | iris.cube.CubeList:
    """Convert mixing ratio to specific humidity."""
    q = iris.cube.CubeList([])
    for w in iter_maybe(mixing_ratio):
        sh = w.copy()
        sh = w / (1 + w)
        sh.rename("specific_humidity")
        q.append(sh)
    if len(q) == 1:
        return q[0]
    else:
        return q


def saturation_mixing_ratio(
    temperature: iris.cube.Cube | iris.cube.CubeList,
    pressure: iris.cube.Cube | iris.cube.CubeList,
) -> iris.cube.Cube | iris.cube.CubeList:
    """Calculate saturation mixing ratio."""
    w = iris.cube.CubeList([])
    for T, P in zip(iter_maybe(temperature), iter_maybe(pressure), strict=True):
        P = convert_units(P, "hPa")
        mr = (EPSILON * vapour_pressure(T)) / (P - vapour_pressure(T))
        mr.units = "kg/kg"
        mr.rename("saturation_mixing_ratio")
        w.append(mr)
    if len(w) == 1:
        return w[0]
    else:
        return w


def saturation_specific_humidity(
    temperature: iris.cube.Cube | iris.cube.CubeList,
    pressure: iris.cube.Cube | iris.cube.CubeList,
) -> iris.cube.Cube | iris.cube.CubeList:
    """Calculate saturation specific humidity."""
    q = iris.cube.CubeList([])
    for T, P in zip(iter_maybe(temperature), iter_maybe(pressure), strict=True):
        P = convert_units(P, "hPa")
        sh = (EPSILON * vapour_pressure(T)) / P
        sh.units = "kg/kg"
        sh.rename("saturation_specific_humidity")
        q.append(sh)
    if len(q) == 1:
        return q[0]
    else:
        return q


def mixing_ratio_from_relative_humidity(
    temperature: iris.cube.Cube | iris.cube.CubeList,
    pressure: iris.cube.Cube | iris.cube.CubeList,
    relative_humidity: iris.cube.Cube | iris.cube.CubeList,
) -> iris.cube.Cube | iris.cube.CubeList:
    """Calculate the mixing ratio from RH."""
    w = iris.cube.CubeList([])
    for T, P, RH in zip(
        iter_maybe(temperature),
        iter_maybe(pressure),
        iter_maybe(relative_humidity),
        strict=True,
    ):
        RH = convert_units(RH, "1")
        mr = saturation_mixing_ratio(T, P) * RH
        mr.rename("mixing_ratio")
        mr.units = "kg/kg"
        w.append(mr)
    if len(w) == 1:
        return w[0]
    else:
        return w


def specific_humidity_from_relative_humidity(
    temperature: iris.cube.Cube | iris.cube.CubeList,
    pressure: iris.cube.Cube | iris.cube.CubeList,
    relative_humidity: iris.cube.Cube | iris.cube.CubeList,
) -> iris.cube.Cube | iris.cube.CubeList:
    """Calculate the mixing ratio from RH."""
    q = iris.cube.CubeList([])
    for T, P, RH in zip(
        iter_maybe(temperature),
        iter_maybe(pressure),
        iter_maybe(relative_humidity),
        strict=True,
    ):
        RH = convert_units(RH, "1")
        sh = saturation_specific_humidity(T, P) * RH
        sh.rename("specific_humidity")
        sh.units = "kg/kg"
        q.append(sh)
    if len(q) == 1:
        return q[0]
    else:
        return q


def relative_humidity_from_mixing_ratio(
    mixing_ratio: iris.cube.Cube | iris.cube.CubeList,
    temperature: iris.cube.Cube | iris.cube.CubeList,
    pressure: iris.cube.Cube | iris.cube.CubeList,
) -> iris.cube.Cube | iris.cube.CubeList:
    """Convert mixing ratio to relative humidity."""
    RH = iris.cube.CubeList([])
    for W, T, P in zip(
        iter_maybe(mixing_ratio),
        iter_maybe(temperature),
        iter_maybe(pressure),
        strict=True,
    ):
        rel_h = W / saturation_mixing_ratio(T, P)
        rel_h.rename("relative_humidity")
        rel_h = convert_units(rel_h, "%")
        RH.append(rel_h)
    if len(RH) == 1:
        return RH[0]
    else:
        return RH


def relative_humidity_from_specific_humidity(
    specific_humidity: iris.cube.Cube | iris.cube.CubeList,
    temperature: iris.cube.Cube | iris.cube.CubeList,
    pressure: iris.cube.Cube | iris.cube.CubeList,
) -> iris.cube.Cube | iris.cube.CubeList:
    """Convert specific humidity to relative humidity."""
    RH = iris.cube.CubeList([])
    for Q, T, P in zip(
        iter_maybe(specific_humidity),
        iter_maybe(temperature),
        iter_maybe(pressure),
        strict=True,
    ):
        rel_h = Q / saturation_specific_humidity(T, P)
        rel_h.rename("relative_humidity")
        rel_h = convert_units(rel_h, "%")
        RH.append(rel_h)
    if len(RH) == 1:
        return RH[0]
    else:
        return RH
