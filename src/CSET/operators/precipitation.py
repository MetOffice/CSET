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

from typing import Literal

import iris
import iris.cube
import numpy as np
from skimage.measure import label

from CSET._common import iter_maybe


def MAUL_properties(
    cubes: iris.cube.Cube | iris.cube.CubeList,
    output: Literal["number", "base", "depth"],
) -> iris.cube.Cube | iris.cube.CubeList:
    """Identify properties of Moist Absolutely Unstable Layers.

    Parameters
    ----------
    cubes: iris.cube.Cube | iris.cube.CubeList
      A cube or cubelist of a mask(s) as to whether a MAUL exists.
      This input must be a binary field.
    output: Literal["number", "base", "depth"]
      The output is the desired property required. It can be
      number, base, depth for the number of MAULs, base height
      of the deepest MAUL, or the depth of the deepest MAUL,
      respectively.

    Returns
    -------
    cube: iris.cube.Cube | iris.cube.CubeList
       A Cube or CubeList depending upon the output specified.

    Raises
    ------
    ValueError: Data contains values that are not 0 or 1, only masked data should be used.
        This error is raised when a mask field is not provided to the operator.
    ValueError: Unexpected value for output. Expected number, depth or base. Got {output}.
        This error is raised when the wrong output string is specified.

    Notes
    -----
    Having been provided with a mask field for identifying whether Moist
    Absolutely Unstable Layers (MAULs) are present, based on criteria
    set out in a recipe, this operator applies image processing to the mask
    to each point in turn. It uses the image processing to identify continuous
    layers. It identifies the number, top and base of each layer. Depending
    on output desired it will output information for the deepest MAUL.

    When a MAUL is not present the output will be set to NaN for depth and base.
    If number of MAULs is the desired output it will be set to zero.

    The MAUL diagnostic is applicable anywhere in the globe and across all scales.
    """
    num_MAULs = iris.cube.CubeList([])
    maul_d = iris.cube.CubeList([])
    maul_b = iris.cube.CubeList([])

    if output not in ("number", "base", "depth"):
        raise ValueError(
            f"""Unexpected value for output. Expected number, depth or base. Got {output}."""
        )

    for cube in iter_maybe(cubes):
        # Check for binary fields.
        if not np.array_equal(cube.data, cube.data.astype(bool)):
            raise ValueError(
                "Data contains values that are not 0 or 1, only masked data should be used."
            )
        # Create dummy cubes to store the output.
        number_of_MAULs = next(cube.slices_over("model_level_number")).copy()
        number_of_MAULs.data[:] = 0.0
        maul_depth = number_of_MAULs.copy()
        maul_base = number_of_MAULs.copy()
        # Loop over realization.
        for mem_number, member in enumerate(cube.slices_over("realization")):
            # Loop over time.
            for time_point, time in enumerate(member.slices_over("time")):
                # Loop over latitude.
                for lat_point, lat in enumerate(time.slices_over("latitude")):
                    # Loop over longitude.
                    for lon_point, lon in enumerate(lat.slices_over("longitude")):
                        # Label each object in the vertical.
                        labels = label(lon.core_data())
                        # Finds the number of MAULs present, if no MAUL is present
                        # the value is set to zero.
                        if (
                            len(number_of_MAULs.coord("realization").points) != 1
                            and len(number_of_MAULs.coord("time").points) != 1
                        ):
                            number_of_MAULs.data[
                                mem_number, time_point, lat_point, lon_point
                            ] = np.max(labels)
                        elif (
                            len(number_of_MAULs.coord("realization").points) != 1
                            and len(number_of_MAULs.coord("time").points) == 1
                        ):
                            number_of_MAULs.data[mem_number, lat_point, lon_point] = (
                                np.max(labels)
                            )
                        elif (
                            len(number_of_MAULs.coord("time").points) != 1
                            and len(number_of_MAULs.coord("realization").points) == 1
                        ):
                            number_of_MAULs.data[time_point, lat_point, lon_point] = (
                                np.max(labels)
                            )
                        else:
                            number_of_MAULs.data[lat_point, lon_point] = np.max(labels)
                        if output != "number":
                            # Find the base, top, and depth for each object using cube metadata.
                            maul_start = []
                            maul_end = []
                            maul_dep = []
                            # Loop over the number of MAULs (plus one to ensure only one MAUL is covered).
                            for maul in range(1, np.max(labels) + 1):
                                maul_range = np.where(labels == maul)
                                maul_start_point = lon.coord("level_height").points[
                                    maul_range[0][0]
                                ]
                                maul_end_point = lon.coord("level_height").points[
                                    maul_range[0][-1]
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
                                elif (
                                    len(number_of_MAULs.coord("realization").points)
                                    != 1
                                    and len(number_of_MAULs.coord("time").points) == 1
                                ):
                                    maul_depth.data[
                                        mem_number, lat_point, lon_point
                                    ] = np.max(maul_dep)
                                    maul_base.data[mem_number, lat_point, lon_point] = (
                                        maul_start[index]
                                    )
                                elif (
                                    len(number_of_MAULs.coord("time").points) != 1
                                    and len(number_of_MAULs.coord("realization").points)
                                    == 1
                                ):
                                    maul_depth.data[
                                        time_point, lat_point, lon_point
                                    ] = np.max(maul_dep)
                                    maul_base.data[time_point, lat_point, lon_point] = (
                                        maul_start[index]
                                    )
                                else:
                                    maul_depth.data[lat_point, lon_point] = np.max(
                                        maul_dep
                                    )
                                    maul_base.data[lat_point, lon_point] = maul_start[
                                        index
                                    ]
                            # Here a ValueError is raised if a MAUL is not found, however
                            # this is a valid answer, and so output data is set to NaN.
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
                                elif (
                                    len(number_of_MAULs.coord("realization").points)
                                    != 1
                                    and len(number_of_MAULs.coord("time").points) == 1
                                ):
                                    maul_depth.data[
                                        mem_number, lat_point, lon_point
                                    ] = np.nan
                                    maul_base.data[mem_number, lat_point, lon_point] = (
                                        np.nan
                                    )
                                elif (
                                    len(number_of_MAULs.coord("time").points) != 1
                                    and len(number_of_MAULs.coord("realization").points)
                                    == 1
                                ):
                                    maul_depth.data[
                                        time_point, lat_point, lon_point
                                    ] = np.nan
                                    maul_base.data[time_point, lat_point, lon_point] = (
                                        np.nan
                                    )
                                else:
                                    maul_depth.data[lat_point, lon_point] = np.nan
                                    maul_base.data[lat_point, lon_point] = np.nan

        # Units and renaming.
        match output:
            case "number":
                number_of_MAULs.units = "1"
                number_of_MAULs.rename("Number_of_MAULs")
                num_MAULs.append(number_of_MAULs)
            case "depth":
                maul_depth.units = "m"
                maul_depth.rename("MAUL_depth")
                maul_d.append(maul_depth)
            case _:
                maul_base.units = "m"
                maul_base.rename("MAUL_base_height")
                maul_b.append(maul_base)

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
        case _:
            return maul_b
