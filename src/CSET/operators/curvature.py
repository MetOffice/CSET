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

import numpy as np


def lat_lon_identifier(original_lat, original_lon, distance, bearing):
    """Find the latitude and longitude of new points based on great circle distance."""
    R = 6371.0
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

    new_lon = np.where(new_lon > 180.0, new_lon - 360.0, new_lon)

    return new_lat, new_lon


# def curvature_function(central, surrounding, tolerance, radial_points):
#    """Calculate the intermediate data for CURV diagnostic."""
#    shape_of_surrounding = surrounding.shape
#    binary_difference = np.zeros(shape_of_surrounding)
#    for rp in range(radial_points):
#        binary_difference[:, rp] = np.where(
#            surrounding[:, rp] < central[:] + tolerance, 1, 0
#        )
#        binary_difference[:, rp] = np.where(
#            surroudnig[:, rp] > central[:] - tolerance, -1, binary_difference[:, rp]
#        )
#    curvature = bindary_difference.sum(axis=1)
#    return curvature


# def curv(
#    radius, num_radial_points, north, south, east, west, tolerance, cube, outputfile
# ):
#    """Calculate the CURV diagnostic."""
#    if (num_radial_points != 8) or (num_radial_points != 16):
#        raise ValueError(
#            f"Number of radial points should be 8 or 16. You have provided {num_radial_points}."
#        )
#    else:
#        bearing = np.linspace(0.0, 360.0, num_radial_points + 1)
#
#    data_area = [north, west, south, east]
#
#    logging.info(
#        f"CURV calculated base on {num_radial_points} radial points, a {radius} km radius, with {tolerance} tolerance."
#    )
#    logging.info(f"CURV calculated over area {data_area}.")
#
#    extracted_data = cube.extract(lon)
#    extract_lats = extract_data.extract(lat)
#
#    points = np.size(extract_data.core_data())
#
#    curv = np.zeros(points)
#
#    new_lats = np.zeros((points, num_radial_points))
#    new_lons = np.zeros((points, num_radial_points))
#
#    new_vals = np.zeros((points, num_radial_points))
#
#    for i in range(num_radial_points):
#        new_lats[:, i], new_lons[:, i] = lat_lon_identifier(
#            lats, lons, radius, bearing[i]
#        )
#
#        new_vals[:, i] = cube.interpolate(new_lats[:, i], new_lons[:, i])
#
#    curv = curvature_function(cube, new_vals, tolerance, num_radial_points)
#
#    return curv
