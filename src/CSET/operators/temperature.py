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
from CSET.operators.constants import CPD, EPSILON, LV, RV, T0
from CSET.operators.humidity import mixing_ratio_from_RH
from CSET.operators.pressure import exner_pressure, vapour_pressure


def dewpoint_temperature(
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
        td.units = "K"
        td.rename("dewpoint temperature")
        Td.append(td)
    if len(Td) == 1:
        return Td[0]
    else:
        return Td


def virtual_temperature(
    temperature: iris.cube.Cube | iris.cube.CubeList,
    mixing_ratio: iris.cube.Cube | iris.cube.CubeList,
) -> iris.cube.Cube | iris.cube.CubeList:
    """Calculate the virtual temperature."""
    Tv = iris.cube.CubeList([])
    for T, W in zip(iter_maybe(temperature), iter_maybe(mixing_ratio), strict=True):
        virT = T * ((W + EPSILON) / (EPSILON * (1 + W)))
        virT.rename("virtual_temperature")
        Tv.append(virT)
    if len(Tv) == 1:
        return Tv[0]
    else:
        return Tv


def potential_temperature(
    temperature: iris.cube.Cube | iris.cube.CubeList,
    pressure: iris.cube.Cube | iris.cube.CubeList,
) -> iris.cube.Cube | iris.cube.CubeList:
    """Calculate the potenital temperature."""
    theta = iris.cube.CubeList([])
    for T, P in zip(iter_maybe(temperature), iter_maybe(pressure), strict=True):
        TH = T / exner_pressure(P)
        TH.rename("potential_temperature")
        theta.append(TH)
    if len(theta) == 1:
        return theta[0]
    else:
        return theta


def virtual_potential_temperature(
    temperature: iris.cube.Cube | iris.cube.CubeList,
    mixing_ratio: iris.cube.Cube | iris.cube.CubeList,
    pressure: iris.cube.Cube | iris.cube.CubeList,
) -> iris.cube.Cube | iris.cube.CubeList:
    """Calculate the virtual potential temperature."""
    theta_v = iris.cube.CubeList([])
    for T, W, P in zip(
        iter_maybe(temperature),
        iter_maybe(mixing_ratio),
        iter_maybe(pressure),
        strict=True,
    ):
        TH_V = virtual_temperature(T, W) / exner_pressure(P)
        TH_V.rename("virtual_potential_temperature")
        theta_v.append(TH_V)
    if len(theta_v) == 1:
        return theta_v[0]
    else:
        return theta_v


def equivalent_potential_temperature(
    temperature: iris.cube.Cube | iris.cube.CubeList,
    relative_humidity: iris.cube.Cube | iris.cube.CubeList,
    pressure: iris.cube.Cube | iris.cube.CubeList,
) -> iris.cube.Cube | iris.cube.CubeList:
    """Calculate the equivalent potenital temperature."""
    theta_e = iris.cube.CubeList([])
    for T, RH, P in zip(
        iter_maybe(temperature),
        iter_maybe(relative_humidity),
        iter_maybe(pressure),
        strict=True,
    ):
        if RH.units == "%":
            RH /= 100.0
            RH.units = "1"
        theta = potential_temperature(T, P)
        w = mixing_ratio_from_RH(T, P, RH)
        second_term_power = -(w * RV) / CPD
        second_term = RH.core_data() ** second_term_power.core_data()
        third_term_power = LV * w / (CPD * T)
        third_term = np.exp(third_term_power.core_data())
        TH_E = theta * second_term * third_term
        TH_E.rename("equivalent_potential_temperature")
        TH_E.units = "K"
        theta_e.append(TH_E)
    if len(theta_e) == 1:
        return theta_e[0]
    else:
        return theta_e
