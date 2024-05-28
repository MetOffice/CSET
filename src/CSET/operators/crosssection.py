# Copyright 2024 Met Office and contributors.
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

"""Operators to extract a cross section given a tuple of xy coords to start/finish."""

from math import asin, cos, radians, sin, sqrt

import iris
import numpy as np

from CSET.operators._utils import get_cube_xycoordname


def _calc_dist(coord_1, coord_2):
    """Haversine distance in metres."""
    # Approximate radius of earth in m
    # Source: https://nssdc.gsfc.nasa.gov/planetary/factsheet/earthfact.html
    radius = 6378000

    # extract coordinates and convert to radians
    lat1 = radians(coord_1[0])
    lon1 = radians(coord_1[1])
    lat2 = radians(coord_2[0])
    lon2 = radians(coord_2[1])

    # Find out delta latitude, longitude
    dlon = lon2 - lon1
    dlat = lat2 - lat1

    # Compute distance
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    distance = radius * c

    return distance


def calc_crosssection(cube, startxy, endxy, coord="distance"):
    """
    Compute cross section.

    Compute a cross section for a given cube containing pressure level, latitude
    and longitude coordinates, with an appropriate sampling interval along the
    transect based on grid spacing.

    Arguments
    ---------

    cube: Cube
        An iris cube containing at least pressure, latitude and longitude coordinate
        dimensions.

    """
    # Find out xy coord name
    x_name, y_name = get_cube_xycoordname(cube)

    # Get local cutout so we can get proper xmin/ymin spacing.
    cube = cube.intersection(
        latitude=(startxy[0] - 0.5, endxy[0] + 0.5),
        longitude=(startxy[1] - 0.5, endxy[1] + 0.5),
    )

    # Compute minimum gap between coords - in case variable res, default to minimum.
    xmin = np.min(
        cube.coord("longitude").points[1:] - cube.coord("longitude").points[:-1]
    )
    ymin = np.min(
        cube.coord("latitude").points[1:] - cube.coord("latitude").points[:-1]
    )

    # Compute vector distance between start and end points in degrees.
    dist_deg = np.sqrt(((startxy[0] - endxy[0]) ** 2) + ((startxy[1] - endxy[1]) ** 2))

    # For scenarios where coord is at 90 degree (no latitude/longitude change).
    # Only xmin or ymin will be zero, not both (otherwise startxy and endxy the same).
    if startxy[1] - endxy[1] == 0:
        latslice_only = True
    else:
        latslice_only = False

    if startxy[0] - endxy[0] == 0:
        lonslice_only = True
    else:
        lonslice_only = False

    if latslice_only:
        xpnts = np.repeat(startxy[1], int(dist_deg / ymin))
        ypnts = np.linspace(startxy[0], endxy[0], int(dist_deg / ymin))
    elif lonslice_only:
        xpnts = np.linspace(startxy[1], endxy[1], int(dist_deg / xmin))
        ypnts = np.repeat(startxy[0], int(dist_deg / xmin))
    else:
        # Else use the smallest grid space in x or y direction.
        xpnts = np.linspace(startxy[1], endxy[1], int(dist_deg / np.min([xmin, ymin])))
        ypnts = np.linspace(startxy[0], endxy[0], int(dist_deg / np.min([xmin, ymin])))

    interpolated_cubes = iris.cube.CubeList()
    for i in range(0, xpnts.shape[0]):
        print(i, "/", xpnts.shape[0])

        # Get point along transect.
        cube_slice = cube.interpolate(
            [("latitude", ypnts[i]), ("longitude", xpnts[i])], iris.analysis.Linear()
        )

        if coord == "distance":
            # one step at end potentially at end and add to cube after merge.
            dist = _calc_dist((startxy[0], startxy[1]), (ypnts[i], xpnts[i]))
            dist_coord = iris.coords.AuxCoord(dist, long_name="distance", units="m")
            cube_slice.add_aux_coord(dist_coord)
            cube_slice = iris.util.new_axis(cube_slice, scalar_coord="distance")
            cube_slice.remove_coord("latitude")
            cube_slice.remove_coord("longitude")
        elif coord == "latitude":
            cube_slice.remove_coord("latitude")
            cube_slice.remove_coord("longitude")
            dist_coord = iris.coords.AuxCoord(
                ypnts[i], long_name="latitude", units="degrees"
            )
            cube_slice.add_aux_coord(dist_coord)
            cube_slice = iris.util.new_axis(cube_slice, scalar_coord="latitude")
        elif coord == "longitude":
            cube_slice.remove_coord("latitude")
            cube_slice.remove_coord("longitude")
            dist_coord = iris.coords.AuxCoord(
                xpnts[i], long_name="longitude", units="degrees"
            )
            cube_slice.add_aux_coord(dist_coord)
            cube_slice = iris.util.new_axis(cube_slice, scalar_coord="longitude")

        interpolated_cubes.append(cube_slice)

    interpolated_cubes = interpolated_cubes.concatenate()

    if len(interpolated_cubes) == 1:
        return interpolated_cubes[0]
    else:
        raise ValueError("Can't merge into a single cube")


cube = calc_crosssection(
    cube=iris.load_cube(
        "/scratch/jawarner/tmp_2304/20210422T0600Z_Regn1_resn_1_RA2T_pz024.pp",
        "air_temperature",
    )[4, 10, :, :],
    startxy=(-2, 38),
    endxy=(7, 39),
    coord="longitude",
)
print(cube)
