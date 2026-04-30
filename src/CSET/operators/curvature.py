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


def _lat_lon_identifier(original_lat, original_lon, distance, bearing):
    """Find the latitude and longitude of new points based on great circle distance."""
    R = 6371.0  # km.
    lat_rad = np.radians(original_lat)
    lon_rad = np.radians(original_lon)
    bearing_rad = np.radians(bearing)

    new_lat = np.arcsin(
        np.sin(lat_rad) * np.cos(distance / R)
        + np.cos(lat_rad) * np.sin(distance / R) * np.cos(bearing_rad)
    )
    new_lon = lon_rad + np.arctan2(
        np.sin(bearing_rad) * np.sin(distance / R) * np.cos(lat_rad),
        np.cos(distance / R) - np.sin(lat_rad) * np.sin(new_lat),
    )

    new_lat = np.degrees(new_lat)
    new_lon = np.degrees(new_lon)
    new_lon = np.where(new_lon > 360.0, new_lon - 360.0, new_lon)

    return new_lat, new_lon


def curv(central, radius, num_radial_points=16, tol=0):
    """Calculate the CURV diagnostic."""
    if (num_radial_points == 8) or (num_radial_points == 16):
        bearing = np.linspace(0.0, 360.0, num_radial_points + 1)[:-1]
    else:
        raise ValueError(
            f"Number of radial points should be 8 or 16. You have provided {num_radial_points}."
        )

    logging.info(
        f"CURV calculated base on {num_radial_points} radial points, a {radius} km radius and {tol} tolerance."
    )

    surroundings = iris.cube.CubeList([])
    for b in bearing:
        surround = central.copy()
        # Need to try and avoid this loop for whole domain if possible, also need to raise time and realization bits as well.
        for lat_number, lat in enumerate(central.slices_over("latitude")):
            for lon_number, lon in enumerate(lat.slices_over("longitude")):
                new_lat, new_lon = _lat_lon_identifier(
                    lon.coord("latitude").points,
                    lon.coord("longitude").points,
                    radius,
                    b,
                )
                # Need to get interpolation better.
                surround.data[lat_number, lon_number] = central.data[
                    np.abs(central.coord("latitude").points - new_lat[0]).argmin(),
                    np.abs(central.coord("longitude").points - new_lon[0]).argmin(),
                ]
        surround.add_aux_coord(
            iris.coords.DimCoord(b, long_name="bearing", units="degrees")
        )
        surroundings.append(surround)
    surroundings.merge()
    print(surroundings)

    curv = surroundings[0].copy()
    curv -= central

    curv.data[curv.data > tol] = -1.0
    curv.data[curv.data < tol] = 1.0

    curv.collapsed("bearing", iris.analysis.SUM)
    curv.rename(f"CURV_calculated_from_{num_radial_points}_radial_points")
    curv.units = "1"
    return curv
