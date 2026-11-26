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

"""A module containing different implementations of CURV.

The diagnostics here are separate implementations of CURV for both
global models and limited-area models.
"""

import logging

import iris
import numpy as np

from CSET._common import iter_maybe
from CSET.operators._atmospheric_constants import Ra

logger = logging.getLogger(__name__)


def _lat_lon_identifier(original_lat, original_lon, distance, bearing):
    """Find the latitude and longitude of new points based on great circle distance."""
    lat_rad = np.radians(original_lat)
    lon_rad = np.radians(original_lon)
    bearing_rad = np.radians(bearing)

    new_lat = np.arcsin(
        np.sin(lat_rad) * np.cos(distance / Ra)
        + np.cos(lat_rad) * np.sin(distance / Ra) * np.cos(bearing_rad)
    )
    new_lon = lon_rad + np.arctan2(
        np.sin(bearing_rad) * np.sin(distance / Ra) * np.cos(lat_rad),
        np.cos(distance / Ra) - np.sin(lat_rad) * np.sin(new_lat),
    )

    new_lat = np.degrees(new_lat)
    new_lon = np.degrees(new_lon)
    new_lon = np.where(new_lon > 180.0, new_lon - 360.0, new_lon)

    return new_lat, new_lon


def global_curv(
    central: iris.cube.Cube | iris.cube.CubeList,
    radius: float,
    num_radial_points: int = 16,
    tol: float = 400.0,
) -> iris.cube.Cube | iris.cube.CubeList:
    """Calculate the CURV for a global model.

    Parameters
    ----------
    central: iris.cube.Cube | iris.cube.CubeList
        The raw pressure or geopotential height field that acts as the central
        point for determining the curvature around.
    radius: float
        The radius of interest for CURV to be calculated over.
    num_radial_points: integer, default 16.
        The number of points around your central point to consider. It defaults
        to 16, but you can also consider 8 points.
    tol: float, default 400.0
        The tolerance for the CURV calculation. This is used to help reduce noise
        in the field. The current default is 400.0. It takes the units of the field
        you are considering Pascals for pressure, metres for geopotenital height.

    Returns
    -------
    curv: iris.cube.Cube | iris.cube.CubeList
        The results of the CURV calculation as either a Cube or a CubeList.

    Raises
    ------
    ValueError
        If the number of radial points specified is not 8 or 16.

    Notes
    -----
    TBD
    """
    if (num_radial_points == 8) or (num_radial_points == 16):
        bearing = np.linspace(0.0, 360.0, num_radial_points + 1)[:-1]
    else:
        raise ValueError(
            f"Number of radial points should be 8 or 16. You have provided {num_radial_points}. Support may be added in the future for different numbers of points."
        )

    logger.info(
        f"CURV calculated base on {num_radial_points} radial points, a {radius} km radius and {tol} tolerance."
    )
    curv_cubes = iris.cube.CubeList([])
    for cube in iter_maybe(central):
        curv = cube.copy()
        surroundings = []
        lats, lons = np.meshgrid(
            cube.coord("latitude").points, cube.coord("longitude").points
        )
        for b in bearing:
            target_data = cube.copy()
            new_lat, new_lon = _lat_lon_identifier(
                lats,
                lons,
                radius,
                b,
            )
            new_lat_points = new_lat[0, :]
            new_lon_points = new_lon[:, 0]
            surround = target_data.interpolate(
                [("latitude", new_lat_points), ("longitude", new_lon_points)],
                iris.analysis.Linear(),
            )
            surroundings.append(surround.data)
        surroundings = np.array(surroundings)
        curv_data = surroundings - cube.data
        curv_data_binary = np.zeros(curv_data.shape)
        curv_data_binary[curv_data > tol] = -1.0
        curv_data_binary[curv_data < -tol] = 1.0
        curv_data_collapsed = np.sum(curv_data_binary, 0)
        curv.data = curv_data_collapsed
        curv.rename(f"CURV_calculated_from_{num_radial_points}_radial_points")
        curv.units = "1"
        curv_cubes.append(curv)
    if len(curv_cubes) == 1:
        return curv_cubes[0]
    else:
        return curv_cubes
