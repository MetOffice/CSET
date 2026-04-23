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

from CSET._common import iter_maybe


def MAUL_properties(
    cubes: iris.cube.Cube | iris.cube.CubeList, output: str
) -> iris.cube.Cube | iris.cube.CubeList:
    """Identify objects in the vertical."""
    num_MAULs = iris.cube.CubeList([])
    maul_d = iris.cube.CubeList([])
    maul_b = iris.cube.CubeList([])

    for cube in iter_maybe(cubes):
        number_of_MAULs = next(cube.slices_over("model_level_number")).copy()
        number_of_MAULs.data[:] = 0.0
        maul_depth = number_of_MAULs.copy()
        maul_base = number_of_MAULs.copy()
        print(maul_base)
        mem_number = 0
        for member in cube.slices_over("realization"):
            time_point = 0
            for time in member.slices_over("time"):
                lat_point = 0
                for lat in time.slices_over("latitude"):
                    lon_point = 0
                    for lon in lat.slices_over("longitude"):
                        labels = label(lon.core_data())
                        if (
                            len(number_of_MAULs.coord("realization").points) != 1
                            and len(number_of_MAULs.coord("time").points) != 1
                        ):
                            number_of_MAULs.data[
                                mem_number, time_point, lat_point, lon_point
                            ] = np.max(labels)
                        elif len(
                            number_of_MAULs.coord("realization").points
                        ) != 1 and len(number_of_MAULs.coord("time").points == 1):
                            number_of_MAULs.data[mem_number, lat_point, lon_point] = (
                                np.max(labels)
                            )
                        else:
                            number_of_MAULs.data[lat_point, lon_point] = np.max(labels)
                        if output != "number":
                            maul_start = []
                            maul_end = []
                            maul_dep = []
                            for maul in range(0, np.max(labels)):
                                maul_range = np.where(labels == maul)
                                maul_start_point = lon.coord("level_height").points[
                                    maul_range[0]
                                ]
                                maul_end_point = lon.coord("level_height").points[
                                    maul_range[0]
                                ]
                                maul_dep.append(maul_end_point - maul_start_point)
                                maul_start.append(maul_start_point)
                                maul_end.append(maul_end_point)
                            try:
                                index = int(
                                    np.where(maul_dep == np.max(maul_dep))[0][0]
                                )
                                if (
                                    len(number_of_MAULs.coord("realization").points)
                                    != 1
                                    and len(number_of_MAULs.coord("time").points) != 1
                                ):
                                    maul_depth.data[
                                        mem_number, time_point, lat_point, lon_point
                                    ] = np.max(maul_dep)
                                    maul_base.data[
                                        mem_number, time_point, lat_point, lon_point
                                    ] = maul_start[index]
                                elif len(
                                    number_of_MAULs.coord("realization").points
                                ) != 1 and len(
                                    number_of_MAULs.coord("time").points == 1
                                ):
                                    maul_depth.data[
                                        mem_number, lat_point, lon_point
                                    ] = np.max(maul_dep)
                                    maul_base.data[mem_number, lat_point, lon_point] = (
                                        maul_start[index]
                                    )
                                else:
                                    maul_depth.data[lat_point, lon_point] = np.max(
                                        maul_dep
                                    )
                                    maul_base.data[lat_point, lon_point] = maul_start[
                                        index
                                    ]
                            except ValueError:
                                if (
                                    len(number_of_MAULs.coord("realization").points)
                                    != 1
                                    and len(number_of_MAULs.coord("time").points) != 1
                                ):
                                    maul_depth.data[
                                        mem_number, time_point, lat_point, lon_point
                                    ] = np.nan
                                    maul_base.data[
                                        mem_number, time_point, lat_point, lon_point
                                    ] = np.nan
                                elif len(
                                    number_of_MAULs.coord("realization").points
                                ) != 1 and len(
                                    number_of_MAULs.coord("time").points == 1
                                ):
                                    maul_depth.data[
                                        mem_number, lat_point, lon_point
                                    ] = np.nan
                                    maul_base.data[mem_number, lat_point, lon_point] = (
                                        np.nan
                                    )
                                else:
                                    maul_depth.data[lat_point, lon_point] = np.nan
                                    maul_base.data[lat_point, lon_point] = np.nan
                        lon_point += 1
                    lat_point += 1
                time_point += 1
            mem_number += 1

        # Units and renaming.
        match output:
            case "number":
                number_of_MAULs.units("1")
                number_of_MAULs.rename("Number_of_MAULs")
                num_MAULs.append(number_of_MAULs)
            case "depth":
                maul_depth.units("m")
                maul_depth.rename("MAUL_depth")
                maul_d.append(maul_depth)
            case "base":
                maul_base.units("m")
                maul_base.rename("MAUL_base_height")
                maul_d.append(maul_base)
            case _:
                raise ValueError("""Unexpected value for output. Expected number,
                                 depth, base or top. Got {output}.""")
    # Output data.
    match output:
        case "number" if len(num_MAULs) == 1:
            return num_MAULs[0]
        case "number":
            return num_MAULs
        case "depth" if len(maul_d) == 1:
            return maul_d[0]
        case "depth":
            return maul_d
        case "base" if len(maul_b) == 1:
            return maul_b[0]
        case "base":
            return maul_b
