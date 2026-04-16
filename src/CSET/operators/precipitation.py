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


def column_object_identification(cube: iris.cube.Cube | iris.cube.CubeList):
    """Identify objects in the vertical."""
    number_of_MAULs = cube[:, :, 0, :, :].copy()
    number_of_MAULs.data[:] = 0.0
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
                    ll += 1
                kk += 1
            jj += 1
        ii += 1
    return number_of_MAULs
