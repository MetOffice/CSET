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

import logging
from math import asin, cos, radians, sin, sqrt

import iris
import numpy as np

from CSET.operators._utils import get_cube_yxcoordname


def _calc_dist(coord_1: tuple, coord_2: tuple):
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


def calc_crosssection(
    cube: iris.cube.Cube, startxy: tuple, endxy: tuple, coord="distance"
):
    """
    Compute cross section.

    Computes a cross section for a given cube containing pressure level, latitude
    and longitude coordinates, using an appropriate sampling interval along the
    transect based on grid spacing.

    Arguments
    ---------

    cube: Cube
        An iris cube containing at least pressure, latitude and longitude coordinate
        dimensions, to compute the transect on.
    startxy: tuple
        A tuple containing the start coordinates for the transect using the original
        data coordinates, ordered (latitude,longitude).
    endxy: tuple
        A tuple containing the end coordinates for the transect using the original
        data coordinates, ordered (latitude,longitude).
    coord: str
        A string specifying the coordinate to be used to plot on the x axis for the
        transect, and thus be used for plotting the cross section. 'distance' can
        also be used to show the transect as a function of distance from startxy.

    Returns
    -------
    cube: Cube
        A cube containing at least pressure and the coordinate specified by coord, for
        the transect specified between startxy and endxy.

    Notes
    -----
    This operator uses the iris.linear method to interpolate the specific point along
    the transect.
    """
    # Parse arguments
    startxy = startxy.split(",")
    endxy = endxy.split(",")
    startxy[0] = float(startxy[0])
    startxy[1] = float(startxy[1])
    endxy[0] = float(endxy[0])
    endxy[1] = float(endxy[1])

    # Find out xy coord name
    y_name, x_name = get_cube_yxcoordname(cube)

    if startxy[0] > max(cube.coord(y_name).points) or startxy[0] < min(
        cube.coord(y_name).points
    ):
        raise IndexError(
            "starty {a} not between {b} and {c}".format(
                a=startxy[0],
                b=min(cube.coord(y_name).points),
                c=max(cube.coord(y_name).points),
            )
        )
    if startxy[1] > max(cube.coord(x_name).points) or startxy[1] < min(
        cube.coord(x_name).points
    ):
        raise IndexError(
            "startx {a} not between {b} and {c}".format(
                a=startxy[1],
                b=min(cube.coord(x_name).points),
                c=max(cube.coord(x_name).points),
            )
        )
    if endxy[0] > max(cube.coord(y_name).points) or endxy[0] < min(
        cube.coord(y_name).points
    ):
        raise IndexError(
            "endy {a} not between {b} and {c}".format(
                a=endxy[0],
                b=min(cube.coord(y_name).points),
                c=max(cube.coord(y_name).points),
            )
        )
    if endxy[1] > max(cube.coord(x_name).points) or endxy[1] < min(
        cube.coord(x_name).points
    ):
        raise IndexError(
            "endx {a} not between {b} and {c}".format(
                a=endxy[1],
                b=min(cube.coord(x_name).points),
                c=max(cube.coord(x_name).points),
            )
        )

    # Create dict for parsing into intersection method
    keyword_args = {
        x_name: (startxy[1], endxy[1]),
        y_name: (startxy[0], endxy[0]),
    }

    # Get local cutout so we can get proper xmin/ymin spacing relevant to the
    # cross section itself.
    cube = cube.intersection(**keyword_args)

    # Compute minimum gap between x/y spatial coords.
    xmin = np.min(cube.coord(x_name).points[1:] - cube.coord(x_name).points[:-1])
    ymin = np.min(cube.coord(y_name).points[1:] - cube.coord(y_name).points[:-1])

    # Compute vector distance between start and end points in degrees.
    dist_deg = np.sqrt(((startxy[0] - endxy[0]) ** 2) + ((startxy[1] - endxy[1]) ** 2))

    # For scenarios where coord is at 90 degree to the grid (i.e. no latitude/longitude change).
    # Only xmin or ymin will be zero, not both (otherwise startxy and endxy the same).
    if startxy[1] - endxy[1] == 0:
        latslice_only = True
    else:
        latslice_only = False

    if startxy[0] - endxy[0] == 0:
        lonslice_only = True
    else:
        lonslice_only = False

    # Depending on the transect angle relative to the grid
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

    # Create cubelist to store interpolated points along transect.
    interpolated_cubes = iris.cube.CubeList()

    # Iterate over all points along transect.
    for i in range(0, xpnts.shape[0]):
        logging.info("%s/%s", i, xpnts.shape[0])

        # Get point along transect.
        cube_slice = cube.interpolate(
            [(x_name, xpnts[i]), (y_name, ypnts[i])], iris.analysis.Linear()
        )

        if coord == "distance":
            # Need to remove existing spatial coords otherwise won't merge.
            dist = _calc_dist((startxy[0], startxy[1]), (ypnts[i], xpnts[i]))
            dist_coord = iris.coords.AuxCoord(dist, long_name="distance", units="m")
            cube_slice.add_aux_coord(dist_coord)
            cube_slice = iris.util.new_axis(cube_slice, scalar_coord="distance")
            cube_slice.remove_coord(x_name)
            cube_slice.remove_coord(y_name)
        elif coord == "latitude":
            cube_slice.remove_coord(x_name)
            cube_slice.remove_coord(y_name)
            dist_coord = iris.coords.AuxCoord(
                ypnts[i], long_name="latitude", units="degrees"
            )
            cube_slice.add_aux_coord(dist_coord)
            cube_slice = iris.util.new_axis(cube_slice, scalar_coord="latitude")
        elif coord == "longitude":
            cube_slice.remove_coord(x_name)
            cube_slice.remove_coord(y_name)
            dist_coord = iris.coords.AuxCoord(
                xpnts[i], long_name="longitude", units="degrees"
            )
            cube_slice.add_aux_coord(dist_coord)
            cube_slice = iris.util.new_axis(cube_slice, scalar_coord="longitude")

        interpolated_cubes.append(cube_slice)

    # Concatenate into single cube.
    interpolated_cubes = interpolated_cubes.concatenate()

    # If concatenation successful, should be cubelist with one cube left.
    if len(interpolated_cubes) == 1:
        print(interpolated_cubes)
        return interpolated_cubes[0]
    else:
        raise ValueError("Can't merge into a single cube")
