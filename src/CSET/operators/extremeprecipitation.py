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

"""Operators for extreme precipitation identification."""

import iris
import iris.analysis as ia
import iris.cube


def maul_identification(equivalent_potential_temperature, relative_humidity):
    """Identify the presence of MAULs."""
    MAUL_exist = iris.cube.CubeList([])
    for th, rh in zip(equivalent_potential_temperature, relative_humidity, strict=True):
        MAUL_presence = rh[:, 1:, :].copy()
        if rh.units == "1":
            rh *= 100.0
            rh.units = "%"
        MAUL_presence.data[:] = 0.0
        delta_thetae = ia.calculus.cube_delta(th, "pressure")
        # If unstable put as one.
        MAUL_presence.data[delta_thetae < 0] = 1.0
        # If too dry revert to zero.
        MAUL_presence.data[rh[:, 1:, :] < 90] = 0.0
        MAUL_presence.collapse("pressure", ia.SUM)
        MAUL_presence.rename("MAUL_presence")
        MAUL_presence.units = "1"
        MAUL_exist.append(MAUL_presence)
    if len(MAUL_exist) == 1:
        return MAUL_exist[0]
    else:
        return MAUL_exist
