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
    r"""Convert specific humidity to mixing ratio.

    Arguments
    ---------
    specific_humidity: iris.cube.Cube | iris.cube.CubeList
        Cubes of specific humidity to be converted to mixing ratio.

    Returns
    -------
    iris.cube.Cube | iris.cube.CubeList
        Converted mixing ratio.

    Notes
    -----
    Atmospheric water vapour can be described by multiple quantities. Here,
    we convert the specific humidity to the mixing ratio using the following
    relation

    .. math:: w = \frac{q}{1 - q}

    with w the mixing ratio and q the specific humidity.

    Larger mixing ratios imply more moisture in the atmosphere. The mixing
    ratio will have the same units as the specific humidity (kg/kg).


    Examples
    --------
    >>> w = humidity.mixing_ratio_from_specific_humidity(specific_humidity)
    """
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
    r"""Convert mixing ratio to specific humidity.

    Arguments
    ---------
    mixing_ratio: iris.cube.Cube | iris.Cube.CubeList
        Cubes of mixing ratio to be converted to specific humidity.

    Returns
    -------
    iris.cube.Cube | iris.cube.CubeList
        Converted specific humidity.

    Notes
    -----
    Here, we invert the relationship from `humidity.mixing_ratio_from_specific_humidity`
    for the following relation

    .. math:: q = \frac{w}{1 + w}

    with q the specific humidity and w the mixing ratio.

    A larger specific humidity implies a more moist atmosphere. The specific
    humidity will have the same units as the mixing ratio (kg/kg).

    Examples
    --------
    >>> q = humidity.specific_humidity_from_mixing_ratio(mixing_ratio)
    """
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
    r"""Calculate saturation mixing ratio.

    Arguments
    ---------
    temperature: iris.cube.Cube | iris.cube.CubeList
        Cubes of temperature in Kelvin.
    pressure: iris.cube.Cube | iris.cube.CubeList
        Cubes of pressure.

    Returns
    -------
    iris.cube.Cube | iris.cube.CubeList
        Saturation mixing ratio in kg/kg.

    Notes
    -----
    The saturation mixing ratio is required to help calculate the relative
    humidity and other diagnostics with respect to the mixing ratio. It can
    be calculated from

    .. math:: w = \epsilon \frac{e}{P - e}

    for w the mixing ratio, :math:`\epsilon` the ratio between the mixing ratio
    of dry and moist air equating to 0.622, P the pressure and e the vapour
    pressure. To ensure that the saturation mixing ratio (:math:`w_s`) is
    calculated the vapour pressure calculated should be with the (dry-bulb)
    temperature to ensure it is the saturated vapour pressure.

    All cubes need to be on the same grid.

    Examples
    --------
    >>> w_s = humidity.saturation_mixing_ratio(temperature, pressure)
    """
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
    r"""Calculate saturation specific humidity.

    Arguments
    ---------
    temperature: iris.cube.Cube | iris.cube.CubeList
        Cubes of temperature in Kelvin.
    pressure: iris.cube.Cube | iris.cube.CubeList
        Cubes of pressure.

    Returns
    -------
    iris.cube.Cube | iris.cube.CubeList
        Saturation specific humidity in kg/kg.

    Notes
    -----
    The saturation specific humidity is required to help calculate the relative
    humidity and other diagnostics with respect to the mixing ratio. It can
    be calculated from

    .. math:: q = \epsilon \frac{e}{P}

    for q the specific humidity, :math:`\epsilon` the ratio between the mixing ratio
    of dry and moist air equating to 0.622, P the pressure and e the vapour
    pressure. To ensure that the saturation specific humidity (:math:`q_{sat}`) is
    calculated the vapour pressure calculated should be with the (dry-bulb)
    temperature to ensure it is the saturated vapour pressure.

    All cubes need to be on the same grid.

    Examples
    --------
    >>> q_sat = humidity.saturation_specific_humidity(temperature, pressure)
    """
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
    r"""Calculate the mixing ratio from RH.

    Arguments
    ---------
    temperature: iris.cube.Cube | iris.cube.CubeList
        Cubes of temperature in Kelvin.
    pressure: iris.cube.Cube | iris.cube.CubeList
        Cubes of pressure.
    relative_humidity: iris.cube.Cube | iris.cube.CubeList
        Cubes of relative humidity.

    Returns
    -------
    iris.cube.Cube | iris.cube.CubeList
        Calculated mixing ratio from relative humidity in kg/kg.

    Notes
    -----
    The mixing ratio can be calculated from temperature, pressure, and
    relative humidity using the following relation

    .. math:: w = RH * w_s

    for w the mixing ratio, :math:`w_s` the saturation mixing ratio, and
    RH the relative humidity. RH is converted to dimensionless fraction rather
    than percentage.

    The operator uses `humidity.saturation_mixing_ratio` to calculate the
    saturation mixing ratio from the temperature and pressure. The relative
    humidity is converted into a decimal before the multiplication occurs.

    All cubes need to be on the same grid.

    Examples
    --------
    >>> w = humidity.mixing_ratio_from_relative_humidity(T, P, RH)
    """
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
    r"""Calculate the specific humidity from relative humidity.

    Arguments
    ---------
    temperature: iris.cube.Cube | iris.cube.CubeList
        Cubes of temperature in Kelvin.
    pressure: iris.cube.Cube | iris.cube.CubeList
        Cubes of pressure.
    relative_humidity: iris.cube.Cube | iris.cube.CubeList
        Cubes of relative humidity.

    Returns
    -------
    iris.cube.Cube | iris.cube.CubeList
        Calculated specific humidity from relative humidity in kg/kg.

    Notes
    -----
    The specific humidity can be calculated from temperature, pressure, and
    relative humidity using the following relation

    .. math:: q = RH * q_{sat}

    for q the specific humidity, :math:`q_{sat}` the saturation specific
    humidity, and RH the relative humidity.

    The operator uses `humidity.saturation_specific_humidity` to calculate the
    saturation specific humidity from the temperature and pressure. The relative
    humidity is converted into a decimal before the multiplication occurs.

    All cubes need to be on the same grid.

    Examples
    --------
    >>> q = humidity.specific_humidity_from_relative_humidity(T, P, RH)
    """
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
    r"""Convert mixing ratio to relative humidity.

    Arguments
    ---------
    mixing_ratio: iris.cube.Cube | iris.cube.CubeList
        Cubes of mixing ratio.
    temperature: iris.cube.Cube | iris.cube.CuebList
        Cubes of temperature in Kelvin.
    pressure: iris.cube.Cube | iris.cube.CubeList
        Cubes of pressure.

    Returns
    -------
    iris.cube.Cube | iris.cube.CubeList
        Relative humidity calculated from mixing ratio.

    Notes
    -----
    The relative humidity can be calculated from the mixing ratio following

    .. math:: RH = \frac{w}{w_s}

    for RH the relative humidity, w the mixing ratio, and :math:`w_s` the
    saturation mixing ratio. The saturation mixing ratio is calculated using
    `humidity.saturation_mixing_ratio`.

    The RH varies predominatly between zero (completely dry) and one (saturated).
    Values larger than one are possible and imply supersaturation.

    All cubes must be on the same grid.

    Examples
    --------
    >>> RH = humidity.relative_humidity_from_mixing_ratio(w, T, P)
    """
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
    r"""Convert specific humidity to relative humidity.

    Arguments
    ---------
    specific_humidity: iris.cube.Cube | iris.cube.CubeList
        Cubes of specific humidity.
    temperature: iris.cube.Cube | iris.cube.CuebList
        Cubes of temperature in Kelvin.
    pressure: iris.cube.Cube | iris.cube.CubeList
        Cubes of pressure.

    Returns
    -------
    iris.cube.Cube | iris.cube.CubeList
        Relative humidity calculated from specific humidity.

    Notes
    -----
    The relative humidity can be calculated from the specific humidity following

    .. math:: RH = \frac{q}{q_{sat}}

    for RH the relative humidity, q the specific humidity, and :math:`q_{sat}` the
    saturation specific humidity. The saturation specific humidity is calculated using
    `humidity.saturation_specific_humidity`.

    The RH varies predominatly between zero (completely dry) and one (saturated).
    Values larger than one are possible and imply supersaturation.

    All cubes must be on the same grid.

    Examples
    --------
    >>> RH = humidity.relative_humidity_from_specific_humidity(q, T, P)
    """
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
