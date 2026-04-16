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

"""Operators to perform various kinds of image processing."""

import iris
import iris.cube
import numpy as np
from skimage.measure import label


def MAUL_properties(
    cube: iris.cube.Cube | iris.cube.CubeList, output: str
) -> iris.cube.Cube | iris.cube.CubeList:
    """Identify objects in the vertical."""
    number_of_MAULs = cube[:, :, 0, :, :].copy()
    number_of_MAULs.data[:] = 0.0
    maul_depth = number_of_MAULs.copy()
    maul_base = number_of_MAULs.copy()
    maul_top = number_of_MAULs.copy()
    ii = 0
    jj = 0
    kk = 0
    ll = 0
    for i in cube.slices_over("realization"):
        for j in i.slices_over("time"):
            for k in j.slices_over("latitude"):
                for column in k.slices_over("longitude"):
                    labels = label(column.core_data())
                    number_of_MAULs.data[ii, jj, kk, ll] = np.max(labels)
                    if output != "number":
                        maul_start = []
                        maul_end = []
                        maul_dep = []
                        for maul in range(0, np.max(labels)):
                            maul_range = np.where(labels == maul)
                            maul_start.append(
                                column.coord("level_height").points[maul_range[0]]
                            )
                            maul_end.append(
                                column.coord("level_height").points[maul_range[0]]
                            )
                            maul_dep.append(maul_end - maul_start)
                        index = np.where(maul_dep == np.max(maul_dep))
                        maul_depth.data[ii, jj, kk, ll] = np.max(maul_dep)
                        maul_base.data[ii, jj, kk, ll] = maul_start[index]
                        maul_top.data[ii, jj, kk, ll] = maul_end[index]
                    ll += 1
                kk += 1
            jj += 1
        ii += 1
    # Units, renaming, and output.
    if output == "number":
        number_of_MAULs.units("1")
        number_of_MAULs.rename("Number_of_MAULs")
        return number_of_MAULs
    elif output == "depth":
        maul_depth.units("m")
        maul_depth.rename("MAUL_depth")
        return maul_depth
    elif output == "base":
        maul_base.units("m")
        maul_base.rename("MAUL_base_height")
        return maul_base
    elif output == "top":
        maul_top.units("m")
        maul_top.rename("MAUL_top_height")
        return maul_top
    else:
        raise ValueError
