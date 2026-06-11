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
    set out in a recipe. The operator applies image processing to the mask
    to each point in the latitude/longitude coordinates. It uses the image
    processing to identify continuous layers (1s), and labels them.
    It identifies the number of layesr by identifying the maximum label number,
    and then finds the top and base of each layer. Depending on the output
    desired it will output information for the deepest MAUL.

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
        # Create dummy cubes to store the output. The shape of the dummy cube
        # depends upon which dimensions are present in the mask cube.
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
                        # Finds the number of MAULs present based upon the
                        # number of objects identified, if no MAUL is present
                        # the value is set to zero.
                        # The code checks for whether there are multiple
                        # realization and/or time points for correct
                        # indexing of the output data and applies accordingly.
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
                            # Find the base, top, and depth for each object
                            # using cube metadata.
                            maul_start = []
                            maul_end = []
                            maul_dep = []
                            # Loop over the number of MAULs (plus one to ensure
                            # the case for only one MAUL being present).
                            for maul in range(1, np.max(labels) + 1):
                                # Find all vertical indices belonging to a MAUL.
                                maul_range = np.where(labels == maul)
                                # Find the height at the base of the MAUL
                                # (lowest level).
                                maul_start_point = lon.coord("level_height").points[
                                    maul_range[0][0]
                                ]
                                # Find the height at the top of the MAUL
                                # (highest level).
                                maul_end_point = lon.coord("level_height").points[
                                    maul_range[0][-1]
                                ]
                                # Calculate the MAUL depth, and store
                                # base and top heights.
                                maul_dep.append(maul_end_point - maul_start_point)
                                maul_start.append(maul_start_point)
                                maul_end.append(maul_end_point)
                            try:
                                # Idendtify where the deepest MAUL is.
                                index = int(
                                    np.where(maul_dep == np.max(maul_dep))[0][0]
                                )
                                # As with number the code checks for whether
                                # there are multiple realization and/or time
                                # points for correct indexing of the output data
                                # and applies accordingly.
                                if (
                                    len(number_of_MAULs.coord("realization").points)
                                    != 1
                                    and len(number_of_MAULs.coord("time").points) != 1
                                ):
                                    # Store the deepest MAUL.
                                    maul_depth.data[
                                        mem_number, time_point, lat_point, lon_point
                                    ] = np.max(maul_dep)
                                    # Store the base height of the deepest MAUL.
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
                            # The dimensionality logic for output data is identical
                            # to that used previously.
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

        # Units and renaming for number, depth and base (the other case).
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


def convert_rainfall_depth_to_rate(cubes, **kwargs):
    """Convert rainfall depth to rate.

    Convert rainfall depth (e.g. mm or kg m-2)
    over a time interval into a rainfall rate (kg m-2 s-1).

    The conversion uses the duration associated with the time coordinate:
    - If time bounds are present, the bounds define the accumulation interval
    - Otherwise, the interval is inferred from differences between time points

    Arguments
    ---------
    cubes: iris.cube.Cube | iris.cube.CubeList
        Cube(s) containing rainfall accumulation (depth), with units convertible
        to kg m-2 (equivalent to mm of water).

        Each cube must include a time coordinate, optionally with bounds.

    kwargs:
        Additional keyword arguments (currently unused, present for API compatibility).

    Returns
    -------
    iris.cube.Cube | iris.cube.CubeList
        Cube(s) with rainfall expressed as a rate in kg m-2 s-1.

        The returned object matches the type of the input:
        - single Cube → single Cube
        - CubeList → CubeList

    Raises
    ------
    ValueError
        - If no time coordinate is present
        - If only a single time point is available without bounds
        - If any inferred duration is non-positive

    Notes
    -----
    - Conversion relies on the equivalence:
      1 mm of rainfall ≡ 1 kg m-2

    - Unit handling:
        * Cubes already in rate units (convertible to kg m-2 s-1) are left unchanged
        * Cubes not representing accumulation (not convertible to kg m-2) are skipped

    - Time handling:
        * If units are time-reference units (e.g. "hours since ..."),
          only the base unit (e.g. hours) is used for duration conversion

    - Broadcasting:
        The duration array is reshaped to match the time dimension of the cube
        before division.

    - The operation is applied in-place to cube data.

    Examples
    --------
    >>> rate = precipitation.convert_rainfall_depth_to_rate(cube)
    >>> rate_list = precipitation.convert_rainfall_depth_to_rate(cube_list)
    """
    from cf_units import (
        Unit as CFUnit,  # if needed elsewhere; not strictly needed below
    )

    cubes_list = iris.cube.CubeList(iter_maybe(cubes))

    for cube in cubes_list:
        # Identify input type
        is_rate = cube.units.is_convertible("kg m-2 s-1") or cube.units.is_convertible(
            "mm s-1"
        )
        is_mass_accum = cube.units.is_convertible("kg m-2")
        is_depth_accum = cube.units.is_convertible("mm")

        # Skip rates and unrelated variables
        if is_rate:
            continue
        if not (is_mass_accum or is_depth_accum):
            continue

        # Time coordinate is required for rainfall accumulations
        try:
            time = cube.coord("time")
        except iris.exceptions.CoordinateNotFoundError as exc:
            raise ValueError("No time coordinate; cannot convert rainfall.") from exc

        # Get accumulation duration
        if time.bounds is not None:
            bounds = time.bounds
            duration = bounds[:, 1] - bounds[:, 0]
        else:
            t = time.points
            dt = np.diff(t)
            if len(dt) == 0:
                raise ValueError("Cannot infer duration from single time point")
            dt = np.concatenate([dt, [dt[-1]]])
            duration = dt

        # Convert duration to seconds
        if time.units.is_time_reference():
            base = str(time.units).split(" since ")[0].strip()
            duration = CFUnit(base).convert(duration, "seconds")
        else:
            duration = time.units.convert(duration, "seconds")

        if np.any(duration <= 0):
            raise ValueError("Non-positive rainfall accumulation interval detected.")

        # Normalise rainfall accumulation units before dividing
        if is_depth_accum:
            # e.g. mm -> mm
            cube.data = cube.units.convert(cube.data, "mm")
        else:
            # e.g. kg m-2 -> kg m-2
            cube.data = cube.units.convert(cube.data, "kg m-2")

        # Reshape duration for broadcasting along time dimension
        reshape = [1] * cube.ndim
        time_dim = cube.coord_dims("time")[0]
        reshape[time_dim] = -1
        duration = duration.reshape(reshape)

        # Convert depth/amount to rate
        # Numerically: mm s-1 == kg m-2 s-1
        cube.data = cube.data / duration
        cube.units = "kg m-2 s-1"

    return cubes_list[0] if isinstance(cubes, iris.cube.Cube) else cubes_list
