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
        es.data = E0 * np.exp(exponent.core_data())
        es.units = "hPa"
        es.rename("vapour_pressure")
        v_pressure.append(es)
    if len(v_pressure) == 1:
        return v_pressure[0]
    else:
        return v_pressure


def vapour_pressure_from_relative_humidity(
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
        vp.units = "hPa"
        vp.rename("vapour_pressure")
        v_pressure.append(vp)
    if len(v_pressure) == 1:
        return v_pressure[0]
    else:
        return v_pressure


def exner_pressure(
    pressure: iris.cube.Cube | iris.cube.CubeList,
) -> iris.cube.Cube | iris.cube.CubeList:
    r"""Calculate the exner pressure.

    Arguments
    ---------
    pressure: iris.cube.Cube | iris.cube.CubeList
        Cubes of pressure to be converted.

    Returns
    -------
    iris.cube.Cube | iris.cube.CubeList
        Converted pressure.

    Notes
    -----
    The Exner pressure is also referred to as the Exner function. It is a
    dimensionless parameter that can be used either as a vertical coordinate or
    more frequently as a means to simplifying conversions between different
    parameters (e.g. Temperature and Potential Temperature; [Holton13]_).
    It is calculated as

    .. math:: \Pi = \left(\frac{P}{P_0}\right)^{\frac{R_d}{c_p}}

    for :math:`\Pi` the Exner Pressure, P the pressure in hPa, :math:`P_0` a reference pressure
    of 1000 hPa, :math:`R_d` the specific gas constant of dry air taken as 297 :math:`J kg^{-1} K^{-1}`,
    :math:`c_p` the specific heat capacity at constant pressure taken as 1005.7 :math:`J kg^{-1} K^{-1}`.

    A value below one implies the pressure is higher than the reference pressure;
    values above one implies the pressure is lower than the reference pressure; a
    value of one implies the pressure is equal to the reference pressure.

    References
    ----------
    .. [Holton13] Holton, J.R. and Hakim G.J. (2013) An Introduction to Dynamic
       Meteorology. 5th Edition, Burlington, MA, Elsevier Academic Press, 532 pp.

    Examples
    --------
    >>> Exner_pressure = pressure.exner_pressure(pressure)
    """
    pi = iris.cube.CubeList([])
    for P in iter_maybe(pressure):
        PI = P.copy()
        P = convert_units(P, "hPa")
        PI.data = (P.core_data() / P0) ** KAPPA
        PI.rename("exner_pressure")
        PI.units = "1"
        pi.append(PI)
    if len(pi) == 1:
        return pi[0]
    else:
        return pi
