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
from CSET.operators._atmospheric_constants import CPD, EPSILON, LV, RV, T0
from CSET.operators.humidity import (
    mixing_ratio_from_relative_humidity,
    saturation_mixing_ratio,
)
from CSET.operators.misc import convert_units
from CSET.operators.pressure import exner_pressure, vapour_pressure


def dewpoint_temperature(
    temperature: iris.cube.Cube | iris.cube.CubeList,
    relative_humidity: iris.cube.Cube | iris.cube.CubeList,
) -> iris.cube.Cube | iris.cube.CubeList:
    """Calculate the dewpoint temperature following Bolton (1980)."""
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


def wet_bulb_temperature(
    temperature: iris.cube.Cube | iris.cube.CubeList,
    relative_humidity: iris.cube.Cube | iris.cube.CubeList,
) -> iris.cube.Cube | iris.cube.CubeList:
    """Calculate the wet-bulb temperature following Stull (2011)."""
    Tw = iris.cube.CubeList([])
    for T, RH in zip(
        iter_maybe(temperature), iter_maybe(relative_humidity), strict=True
    ):
        RH = convert_units(RH, "%")
        T = convert_units(T, "Celsius")
        wetT = (
            T * np.arctan(0.151977 * (RH.core_data() + 8.313659) ** 0.5)
            + np.arctan(T.core_data() + RH.core_data())
            - np.arctan(RH.core_data() - 1.676331)
            + 0.00391838
            * (RH.core_data()) ** (3.0 / 2.0)
            * np.arctan(0.023101 * RH.core_data())
            - 4.686035
        )
        wetT.rename("wet_bulb_temperature")
        wetT = convert_units(wetT, "K")
        Tw.append(wetT)
    if len(Tw) == 1:
        return Tw[0]
    else:
        return Tw


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
        RH = convert_units(RH, "1")
        theta = potential_temperature(T, P)
        w = mixing_ratio_from_relative_humidity(T, P, RH)
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


def wet_bulb_potential_temperature(
    temperature: iris.cube.Cube | iris.cube.CubeList,
    relative_humidity: iris.cube.Cube | iris.cube.CubeList,
    pressure: iris.cube.Cube | iris.cube.CubeList,
) -> iris.cube.Cube | iris.cube.CubeList:
    """Calculate wet-bulb potential temperature after Davies-Jones (2008)."""
    theta_w = iris.cube.CubeList([])
    for T, RH, P in zip(
        iter_maybe(temperature),
        iter_maybe(relative_humidity),
        iter_maybe(pressure),
        strict=True,
    ):
        TH_E = equivalent_potential_temperature(T, P, RH)
        X = TH_E / T0
        X.units = "1"
        A0 = 7.101574
        A1 = -20.68208
        A2 = 16.11182
        A3 = 2.574631
        A4 = -5.205688
        B1 = -3.552497
        B2 = 3.781782
        B3 = -0.6899655
        B4 = -0.5929340
        exponent = (A0 + A1 * X + A2 * X**2 + A3 * X**3 + A4 * X**4) / (
            1.0 + B1 * X + B2 * X**2 + B3 * X**3 + B4 * X**4
        )
        TH_W = TH_E.copy()
        TH_W.data[:] = TH_E.core_data() - np.exp(exponent.core_data())
        TH_W.rename("wet_bulb_potential_temperature")
        TH_W.data[TH_W.data - T0 < -30.0] = np.nan
        TH_W.data[TH_W.data - T0 > 50.0] = np.nan
        theta_w.append(TH_W)
    if len(theta_w) == 1:
        return theta_w[0]
    else:
        return theta_w


def saturation_equivalent_potential_temperature(
    temperature: iris.cube.Cube | iris.cube.CubeList,
    pressure: iris.cube.Cube | iris.cube.CubeList,
) -> iris.cube.Cube | iris.cube.CubeList:
    """Calculate the saturation equivalent potenital temperature."""
    theta_s = iris.cube.CubeList([])
    for T, P in zip(
        iter_maybe(temperature),
        iter_maybe(pressure),
        strict=True,
    ):
        theta = potential_temperature(T, P)
        ws = saturation_mixing_ratio(T, P)
        second_term_power = LV * ws / (CPD * T)
        second_term = np.exp(second_term_power.core_data())
        TH_S = theta * second_term
        TH_S.rename("saturation_equivalent_potential_temperature")
        TH_S.units = "K"
        theta_s.append(TH_S)
    if len(theta_s) == 1:
        return theta_s[0]
    else:
        return theta_s
