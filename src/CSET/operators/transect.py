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

"""Operators to extract a transect given a tuple of xy coords to start/finish."""

import logging

import iris
import numpy as np

from CSET.operators._utils import get_cube_yxcoordname


def _check_within_bounds(point: tuple[float, float], lat_coord, lon_coord):
    """Check if the point (lat, lon) is within the bounds of the data."""
    lon_min = min(lon_coord.points)
    lon_max = max(lon_coord.points)
    lat_min = min(lat_coord.points)
    lat_max = max(lat_coord.points)
    if (
        lat_min > point[0]
        or lat_max < point[0]
        or lon_min > point[1]
        or lon_max < point[1]
    ):
        raise IndexError(
            f"Point {point} not between {(lat_min, lon_min)} and {(lat_max, lon_max)}"
        )


def calc_transect(cube: iris.cube.Cube, startxy: tuple, endxy: tuple):
    """
    Compute transect between startxy and endxy.

    Computes a transect for a given cube containing at least latitude
    and longitude coordinates, using an appropriate sampling interval along the
    transect based on grid spacing. Also decides a suitable x coordinate to plot along
    the transect - see notes for details on this.

    Arguments
    ---------

    cube: Cube
        An iris cube containing latitude and longitude coordinate dimensions,
        to compute the transect on.
    startxy: tuple
        A tuple containing the start coordinates for the transect using the original
        data coordinates, ordered (latitude,longitude).
    endxy: tuple
        A tuple containing the end coordinates for the transect using the original
        data coordinates, ordered (latitude,longitude).

    Returns
    -------
    cube: Cube
        A cube containing at least pressure and the coordinate specified by coord, for
        the transect specified between startxy and endxy.

    Notes
    -----
    This operator uses the iris.linear method to interpolate the specific point along
    the transect.
    Identification of an appropriate coordinate to plot along the x axis is done by
    determining the largest distance out of latitude and longitude. For example, if
    the transect is 90 degrees (west to east), then delta latitude is zero, so it will
    always plot as a function of longitude. Vice versa if the transect is 180 degrees
    (south to north). If a transect is 45 degrees, and delta latitude and longitude
    are the same, it will default to plotting as a function of longitude. Note this
    doesn't affect the transect plot, its purely for interpretation with some appropriate
    x axis labelling/points.
    """
    # Find out xy coord name
    lat_name, lon_name = get_cube_yxcoordname(cube)

    if startxy[0] > max(cube.coord(lat_name).points) or startxy[0] < min(
        cube.coord(lat_name).points
    ):
        raise IndexError(
            "starty {a} not between {b} and {c}".format(
                a=startxy[0],
                b=min(cube.coord(lat_name).points),
                c=max(cube.coord(lat_name).points),
            )
        )
    if startxy[1] > max(cube.coord(lon_name).points) or startxy[1] < min(
        cube.coord(lon_name).points
    ):
        raise IndexError(
            "startx {a} not between {b} and {c}".format(
                a=startxy[1],
                b=min(cube.coord(lon_name).points),
                c=max(cube.coord(lon_name).points),
            )
        )
    if endxy[0] > max(cube.coord(lat_name).points) or endxy[0] < min(
        cube.coord(lat_name).points
    ):
        raise IndexError(
            "endy {a} not between {b} and {c}".format(
                a=endxy[0],
                b=min(cube.coord(lat_name).points),
                c=max(cube.coord(lat_name).points),
            )
        )
    if endxy[1] > max(cube.coord(lon_name).points) or endxy[1] < min(
        cube.coord(lon_name).points
    ):
        raise IndexError(
            "endx {a} not between {b} and {c}".format(
                a=endxy[1],
                b=min(cube.coord(lon_name).points),
                c=max(cube.coord(lon_name).points),
            )
        )

    lon_coord = cube.coord(lon_name)
    lat_coord = cube.coord(lat_name)

    # Compute vector distance between start and end points in degrees.
    dist_deg = np.sqrt((startxy[0] - endxy[0])**2 + (startxy[1] - endxy[1])**2)

    # For scenarios where coord is at 90 degree to the grid (i.e. no latitude/longitude change).
    # Only xmin or ymin will be zero, not both (otherwise startxy and endxy the same).
    if startxy[1] == endxy[1]:
        latslice_only = True
    else:
        latslice_only = False

    if startxy[0] == endxy[0]:
        lonslice_only = True
    else:
        lonslice_only = False

    # Compute minimum gap between x/y spatial coords.
    xmin = np.min(lon_coord.points[1:] - lon_coord.points[:-1])
    ymin = np.min(lat_coord.points[1:] - lat_coord.points[:-1])

    # Depending on the transect angle relative to the grid
    if latslice_only:
        xpnts = np.repeat(startxy[1], int(dist_deg / ymin))
        ypnts = np.linspace(startxy[0], endxy[0], int(dist_deg / ymin))
        xaxis_coord = "latitude"
    elif lonslice_only:
        xpnts = np.linspace(startxy[1], endxy[1], int(dist_deg / xmin))
        ypnts = np.repeat(startxy[0], int(dist_deg / xmin))
        xaxis_coord = "longitude"
    else:
        # Else use the smallest grid space in x or y direction.
        xpnts = np.linspace(startxy[1], endxy[1], int(dist_deg / np.min([xmin, ymin])))
        ypnts = np.linspace(startxy[0], endxy[0], int(dist_deg / np.min([xmin, ymin])))

        # If change in latitude larger than change in longitude:
        if abs(startxy[0] - endxy[0]) > abs(startxy[1] - endxy[1]):
            xaxis_coord = "latitude"
        elif abs(startxy[0] - endxy[0]) <= abs(startxy[1] - endxy[1]):
            xaxis_coord = "longitude"

    # Create cubelist to store interpolated points along transect.
    interpolated_cubes = iris.cube.CubeList()

    # Iterate over all points along transect.
    for i in range(0, xpnts.shape[0]):
        logging.info("%s/%s", i + 1, xpnts.shape[0])

        # Get point along transect.
        cube_slice = cube.interpolate(
            [(lon_name, xpnts[i]), (lat_name, ypnts[i])], iris.analysis.Linear()
        )

        if xaxis_coord == "latitude":
            cube_slice.remove_coord(lon_name)
            cube_slice.remove_coord(lat_name)
            dist_coord = iris.coords.AuxCoord(
                ypnts[i], long_name="latitude", units="degrees"
            )
            cube_slice.add_aux_coord(dist_coord)
            cube_slice = iris.util.new_axis(cube_slice, scalar_coord="latitude")
        elif xaxis_coord == "longitude":
            cube_slice.remove_coord(lon_name)
            cube_slice.remove_coord(lat_name)
            dist_coord = iris.coords.AuxCoord(
                xpnts[i], long_name="longitude", units="degrees"
            )
            cube_slice.add_aux_coord(dist_coord)
            cube_slice = iris.util.new_axis(cube_slice, scalar_coord="longitude")

        interpolated_cubes.append(cube_slice)

    # Concatenate into single cube.
    interpolated_cubes = interpolated_cubes.concatenate()

    # If concatenation successful, should be cubelist with one cube left.
    return interpolated_cubes[0]
