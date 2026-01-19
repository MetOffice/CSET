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
from CSET.operators.pressure import (
    exner_pressure,
    vapour_pressure_from_relative_humidity,
)


def dewpoint_temperature(
    temperature: iris.cube.Cube | iris.cube.CubeList,
    relative_humidity: iris.cube.Cube | iris.cube.CubeList,
) -> iris.cube.Cube | iris.cube.CubeList:
    r"""Calculate the dewpoint temperature.

    Arguments
    ---------
    temperature: iris.cube.Cube | iris.cube.CubeList
        Cubes of temperature in Kelvin.
    relative_humidity: iris.cube.Cube | iris.cube.CubeList
        Cubes of relative humidity.

    Returns
    -------
    iris.cube.Cube | iris.cueb.CubeList
        Calculated dewpoint temperature in Kelvin.

    Notes
    -----
    The dewpoint temperature provides the temperature at which the air must be
    cooled for dew to form (i.e. the water vapour condenses to liquid water).
    It is calculated based upon [Bolton80]_

    .. math:: T_d = \frac{243.5 * ln(e) - 440.8}{19.48 - ln(e)}

    for :math:`T_d` the dewpoint temperature and e the vapour pressure. Here the
    vapour pressure is calculated from relative humidity using
    `pressure.vapour_pressure_from_relative_humidity`.

    The dewpoint temperature is presented when -35.0 C < T < 35.0 C as this is
    when the calculation is the most accurate [Bolton80]_ this roughly equates to
    exclusion of dewpoints on pressures of 400 hPa and above (e.g. [Flack24]_).

    When :math:`T_d` is equivalent to T the relative humidity will be 100 %.

    All cubes must be on the same grid.

    References
    ----------
    .. [Bolton80] Bolton. D. (1980) "The computation of equivalent potential
       temperature". Monthly Weather Review, vol. 108, 1046-1053,
       doi: 10.1175/1520-0493(1980)108<1046:TCOEPT>2.0.CO;2
    .. [Flack24] Flack, D.L.A. (2024) "Stratification of the vertical spread-skill
       relation by radiosonde drift in a convective-scale ensemble."
       Atmospheric Science Letters, vol. 25, e1194, doi: 10.1002/asl.1194

    Examples
    --------
    >>> Td = temperature.dewpoint_temperature(T, RH)
    """
    Td = iris.cube.CubeList([])
    for T, RH in zip(
        iter_maybe(temperature), iter_maybe(relative_humidity), strict=True
    ):
        vp = vapour_pressure_from_relative_humidity(T, RH)
        td = vp.copy()
        td.data = ((243.5 * np.log(vp.core_data())) - 440.8) / (
            19.48 - np.log(vp.core_data())
        )
        td.data[T.data - T0 < -35.0] = np.nan
        td.data[T.data - T0 > 35.0] = np.nan
        td.units = "Celsius"
        td.rename("dewpoint_temperature")
        td = convert_units(td, "K")
        Td.append(td)
    if len(Td) == 1:
        return Td[0]
    else:
        return Td


def virtual_temperature(
    temperature: iris.cube.Cube | iris.cube.CubeList,
    mixing_ratio: iris.cube.Cube | iris.cube.CubeList,
) -> iris.cube.Cube | iris.cube.CubeList:
    r"""Calculate the virtual temperature.

    Arguments
    ---------
    temperature: iris.cube.Cube | iris.cube.CubeList
        Cubes of temperature in Kelvin.
    mixing_ratio: iris.cube.Cube | iris.cube.CubeList
        Cubes of mixing ratio.

    Returns
    -------
    iris.cube.Cube | iris.cube.CubeList
        Calculated virtual temperature in Kelvin.

    Notes
    -----
    The virtual temperature is that required for a dry parcel to have the
    same density as a moist parcel at the same pressure. It is calculated
    as

    .. math:: T_v = T * \frac{w + \epsilon}{\epsilon (1 + w)}

    for :math:`T_v` the virtual temperature, T the temperature, w the mixing
    ratio, and :math:`\epsilon` the ratio between dry and moist air equating
    to 0.622.

    All cubes must be on the same grid.

    Examples
    --------
    >>> Tv = temperature.virtual_temperature(T, w)
    """
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
    r"""Calculate the wet-bulb temperature.

    Arguments
    ---------
    temperature: iris.cube.Cube | iris.cube.CubeList
        Cubes of temperature.
    relative_humidity: iris.cube.Cube | iris.cube.CubeList
        Cubes of relative humidity.

    Returns
    -------
    iris.cube.Cube | iris.cube.CubeList
        Calculated wet-bulb temperature in Kelvin.

    Notes
    -----
    The wet-bulb temperature is the temperature the air reaches when all the
    water has been evaporated out of it. It can be calculated from temperature in Celsius
    and relative humidity in percent following [Stull11]_

    .. math:: T_w = T * arctan\left(0.151977*(RH + 8.313659)^{0.5}\right) + arctan(T + RH) - arctan(RH - 1.676331) + 0.00391838*RH^{\frac{3}{2}}*arctan(0.023101*RH) - 4.686035

    for :math:`T_w` the wet-bulb temperature, T the temperature, and RH the relative
    humidity.

    The equation is valid for 5% < RH < 99% and -20 C < T < 50 C, and results are
    only presented for these values.

    The temperature and relative humidity unit conversions are applied in the
    operator.

    All cubes should be on the same grid.

    References
    ----------
    .. [Stull11] Stull, R. (2011) "Wet-Bulb Temperature from Relative Humidity
       and air temperature." Journal of Applied Meteorology and Climatology, vol. 50,
       2267-2269, doi: 10.1175/JAMC-D-11-0143.1

    Examples
    --------
    >>> Tw = temperature.wet_bulb_temperature(T, RH)
    """
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
        wetT.data[T.core_data() < -20.0] = np.nan
        wetT.data[T.core_data() > 50.0] = np.nan
        wetT.data[RH.core_data() < 5.0] = np.nan
        wetT.data[RH.core_data() > 99.0] = np.nan
        Tw.append(wetT)
    if len(Tw) == 1:
        return Tw[0]
    else:
        return Tw


def potential_temperature(
    temperature: iris.cube.Cube | iris.cube.CubeList,
    pressure: iris.cube.Cube | iris.cube.CubeList,
) -> iris.cube.Cube | iris.cube.CubeList:
    r"""Calculate the potenital temperature.

    Arguments
    ---------
    temperature: iris.cube.Cube | iris.cube.CubeList
        Cubes of temperature.
    pressure: iris.cube.Cube | iris.cube.CuebList
        Cubes of pressure.

    Returns
    -------
    iris.cube.Cube | iris.cube.CubeList
        Calculated potential temperature in Kelvin.

    Notes
    -----
    The potential temperature is the temperature at which an air parcel would reach
    if it was moved adiabatically to a reference pressure. Here we use 1000 hPa
    as the reference pressure. It is calculated from

    .. math:: \theta = \frac{T}{\Pi}

    for :math:`\theta` the potential temperature, T the temperature, and :math:`\Pi`
    the exner pressure. The exner pressure is calculated using `pressure.exner_pressure`.

    All cubes must be on the same grid.

    Examples
    --------
    >>> Theta = temperature.potential_temperature(T, P)
    """
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
    r"""Calculate the virtual potential temperature.

    Arguments
    ---------
    s

    Returns
    -------
    s

    Notes
    -----
    s

    References
    ----------
    s

    Examples
    --------
    >>> s
    """
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
    r"""Calculate the equivalent potenital temperature.

    Arguments
    ---------
    s

    Returns
    -------
    s

    Notes
    -----
    s

    References
    ----------
    s

    Examples
    --------
    >>> s
    """
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
    r"""Calculate wet-bulb potential temperature after Davies-Jones (2008).

    Arguments
    ---------
    s

    Returns
    -------
    s

    Notes
    -----
    s

    References
    ----------
    s

    Examples
    --------
    >>> s
    """
    theta_w = iris.cube.CubeList([])
    for T, RH, P in zip(
        iter_maybe(temperature),
        iter_maybe(relative_humidity),
        iter_maybe(pressure),
        strict=True,
    ):
        TH_E = equivalent_potential_temperature(T, RH, P)
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
    r"""Calculate the saturation equivalent potenital temperature.

    Arguments
    ---------
    s

    Returns
    -------
    s

    Notes
    -----
    s

    References
    ----------
    s

    Examples
    --------
    >>> s
    """
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
