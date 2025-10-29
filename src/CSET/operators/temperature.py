# © Crown copyright, Met Office (2022-2025) and CSET contributors.
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

"""Operators to produce different temperatures."""

import logging

import iris
import iris.cube
import numpy as np

from CSET._common import iter_maybe


def equivalent_potential_temperature_pressure_levels(relative_humidity, temperature):
    """Calculate the equivalent potential temperature."""
    theta_e_list = iris.cube.CubeList([])
    # Constansts.
    p0 = 1000.0
    Rd = 287.0
    Rv = 461.0
    cpd = 1005.7
    Lv = 2.501e6
    for RH, T in zip(
        iter_maybe(relative_humidity), iter_maybe(temperature), strict=True
    ):
        theta_e = T.copy()
        theta_e.data[:] = 0.0

        logging.debug("Convert relative humidity to mixing ratio.")
        es = T.copy()
        TT = T.copy()
        mr = T.copy()
        e0 = 6.1078  # hPa
        TT = 17.27 * (T - 273.16) / (T - 35.86)
        es.data = e0 * np.exp(TT.data)
        es.rename("saturation_vapour_pressure")
        es.units = "hPa"
        mr = RH * (0.622 * (es / (T.coord("pressure").points[:] - es)))
        mr.rename("mixing_ratio")
        mr.units = "1"
        logging.debug("Calculate equivalent potential temperature on pressure levels.")
        first_term = (p0 / T.coord("pressure").points[:]) ** (Rd / cpd)
        second_term_power = -(mr * Rv) / cpd
        second_term = RH.data**second_term_power.data
        third_term_power = Lv * mr / (cpd * T)
        third_term = np.exp(third_term_power.data)
        theta_e = T * first_term * second_term * third_term
        theta_e.rename("equivalent_potential_temperature")
        theta_e_list.append(theta_e)

    if len(theta_e_list) == 1:
        return theta_e_list[0]
    else:
        return theta_e_list
