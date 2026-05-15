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

"""Operators to calculate various forms or properties of wind."""

import logging

import iris
import iris.cube
import numpy as np

from CSET._common import iter_maybe
from CSET.operators._utils import get_cube_yxcoordname
from CSET.operators.regrid import regrid_onto_cube


def calculate_vector_wind_from_list(
    cubes: iris.cube.CubeList,
    *,
    u_name: str = "x_wind",
    v_name: str = "y_wind",
) -> iris.cube.Cube:
    """
    Extract U and V components from CubeList.

    Takes the U and V cubes and pass them to
    calculate_vector_wind.

    Notes
    -----
    - Input must be a CubeList containing U and V component cubes;
    TypeError raised if not CubeList

    Example
    --------
    >>> vector_winds = wind.calculate_vector_wind_from_list(winds)
    """
    if not isinstance(cubes, iris.cube.CubeList):
        raise TypeError(
            "calculate_vector_wind_from_list expects an iris.cube.CubeList "
            f"but got {type(cubes).__name__}"
        )
    try:
        u_cube = cubes.extract_cube(iris.Constraint(name=u_name))
        v_cube = cubes.extract_cube(iris.Constraint(name=v_name))
    except Exception as err:
        available = [c.name() for c in cubes]
        raise ValueError(
            f"Need exactly one U and one V cube. Available cube names: {available}"
        ) from err

    # Ensure cubes to compare are on common differencing grid.
    # This is triggered if either
    #      i) latitude and longitude shapes are not the same. Note grid points
    #         are not compared directly as these can differ through rounding
    #         errors.
    #     ii) or variables are known to often sit on different grid staggering
    #         in different models (e.g. cell center vs cell edge), as is the case
    #         for UM and LFRic comparisons.
    # In future greater choice of regridding method might be applied depending
    # on variable type. Linear regridding can in general be appropriate for smooth
    # variables. Care should be taken with interpretation of differences
    # given this dependency on regridding.

    # Get spatial coord names.
    u_cube_lat_name, u_cube_lon_name = get_cube_yxcoordname(u_cube)
    v_cube_lat_name, v_cube_lon_name = get_cube_yxcoordname(v_cube)

    if (
        u_cube.coord(u_cube_lat_name).shape != v_cube.coord(v_cube_lat_name).shape
        or u_cube.coord(u_cube_lon_name).shape != v_cube.coord(v_cube_lon_name).shape
    ):
        logging.debug(
            "Linear regridding base cube to other grid to compute differences"
        )
        u_cube = regrid_onto_cube(u_cube, v_cube, method="Linear")

    return calculate_vector_wind(u_cube, v_cube)


def calculate_vector_wind(
    u_cube: iris.cube.Cube,
    v_cube: iris.cube.Cube,
) -> iris.cube.CubeList:
    """
    Calculate wind speed and wind direction from U, V component cubes.

    Arguments
    ----------
    u_cube : iris.cube.Cube
        Zonal wind component (eastward wind). Must have same shape,
        coordinates, and units as `v_cube`.

    v_cube : iris.cube.Cube
        Meridional wind component (northward wind). Must have same shape,
        coordinates, and units as `u_cube`.

    Notes
    -----
    - Speed = np.hypot(u, v)
    - Direction is meteorological "from" direction in degrees, 0..360:
    0 = from North, 90 = from East, 180 = from South, 270 = from West
    computed as: (atan2(-u, -v) in degrees + 360) % 360

    Returns
    -------
    Returns a CubeList containing:
        - wind_speed cube
        - wind_direction cube
    """
    u = u_cube.data()
    v = v_cube.data()

    direction = (np.degrees(np.arctan2(-u, -v)) + 360) % 360
    speed = np.hypot(u, v)

    speed_cube = u_cube.copy(data=speed)
    speed_cube.rename("wind_speed")
    if u_cube.units != v_cube.units:
        raise ValueError("U and V cubes must have the same units")

    speed_cube.units = u_cube.units

    direction_cube = u_cube.copy(data=direction)
    direction_cube.rename("wind_direction")
    direction_cube.units = "degrees"
    direction_cube.standard_name = "wind_from_direction"

    return iris.cube.CubeList([speed_cube, direction_cube])


def convert_to_beaufort_scale(
    cubes: iris.cube.Cube | iris.cube.CubeList,
) -> iris.cube.Cube | iris.cube.CubeList:
    r"""Convert windspeed from m/s to the Beaufort Scale.

    Arguments
    ---------
    cubes: iris.cube.Cube | iris.cube.CubeList
        Cubes of windspeed to be converted.
        Required: `wind_speed_at_10m`.

    Returns
    -------
    iris.cube.Cube | iris.cube.CubeList
        Converted windspeed.

    Notes
    -----
    The relationship used to convert the windspeed from m/s to the Beaufort
    Scale is an empirical relationship (e.g., [Beer96]_):

    .. math:: F = (\frac{v}{0.836})^{2/3}

    for F the Beaufort Force, and v the windspeed at 10 m in m/s.

    The Beaufort Scale was devised in 1805 by Rear Admiral Sir Francis Beaufort.
    It is a widely used windscale that categorises the winds into forces and provides
    human-understable names (e.g. gale). The table below shows the Beaufort Scale based
    on the Handbook of Meteorology ([Berryetal45]_).

    .. list-table:: Beaufort Scale
       :widths: 5 20 10 10 10
       :header-rows: 1

       * - Force [1]
         - Descriptor
         - Windspeed [m/s]
         - Windspeed [kn]
         - Windspeed [mph]
       * - 0
         - Calm
         - < 0.4
         - < 1
         - < 1
       * - 1
         - Light Air
         - 0.4 - 1.5
         - 1 - 3
         - 1 - 3
       * - 2
         - Light Breeze
         - 1.6 - 3.3
         - 4 - 6
         - 4 - 7
       * - 3
         - Gentle Breeze
         - 3.4 - 5.4
         - 7 - 10
         - 8 - 12
       * - 4
         - Moderate Breeze
         - 5.5 - 7.9
         - 11 - 16
         - 13 - 18
       * - 5
         - Fresh Breeze
         - 8.0 - 10.7
         - 17 - 21
         - 19 - 24
       * - 6
         - Strong Breeze
         - 10.8 - 13.8
         - 22 - 27
         - 25 - 31
       * - 7
         - Near Gale
         - 13.9 - 17.1
         - 28 - 33
         - 32 - 38
       * - 8
         - Gale
         - 17.2 - 20.7
         - 34 - 40
         - 39 - 46
       * - 9
         - Strong Gale
         - 20.8 - 24.4
         - 41 - 47
         - 47 - 54
       * - 10
         - Storm
         - 24.5 - 28.4
         - 48 - 55
         - 55 - 63
       * - 11
         - Violent Storm
         - 28.5 - 33.5
         - 56 - 63
         - 64 - 73
       * - 12 (+)
         - Hurricane
         - > 33.6
         - > 64
         - > 74

    The modern names have been used in this table. However, it should be noted
    for historical accuracy that Force 7 was originally "Moderate Gale", Force 8
    was originally "Fresh Gale", Force 10 was originally "Whole Gale", and
    Force 11 was originally "Storm". Force 9 can also be referred to as
    "Severe Gale". Furthermore, it should be noted that there is an extended
    Beaufort Scale, sometimes used for tropical cyclones. Hence, why values
    can reach above 12 in this diagnostic. However, these are not referred to
    in the table as anything above F12 is labelled as Hurricane force.

    References
    ----------
    .. [Beer96] Beer, T. (1996) Environmental Oceanography, CRC Marince Science,
       Vol. 11, 2nd Edition, CRC Press, 402 pp.
    .. [Berryetal45] Berry, F. A., Jr., E. Bollay, and N. R. Beers, (1945) Handbook
       of Meteorology. McGraw Hill, 1068 pp.

    Examples
    --------
    >>> Beaufort_Scale=wind.convert_to_Beaufort_scale(winds)
    """
    # Create and empty cubelist.
    winds = iris.cube.CubeList([])
    # Loop over cubelist.
    for cube in iter_maybe(cubes):
        # Copy cube so we do not overwrite data.
        wind_cube = cube.copy()
        # Divide data by 0.836.
        wind_cube /= 0.836
        # Raise to power of 2/3 to produce decimal Beaufort Scale.
        wind_cube.data **= 2.0 / 3.0
        # Round using even round (i.e. to nearest even number).
        wind_cube.data = np.round(wind_cube.data)
        # Convert units.
        wind_cube.units = "1"
        # Rename cube.
        wind_cube.rename(f"{cube.name()}_on_Beaufort_Scale")
        winds.append(wind_cube)
    # Output as single cube or cubelist depending on if cube of cubelist given
    # as input.
    if len(winds) == 1:
        return winds[0]
    else:
        return winds
