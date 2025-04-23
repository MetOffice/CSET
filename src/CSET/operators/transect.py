# © Crown copyright, Met Office (2022-2024) and CSET contributors.
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


def calc_transect(cube: iris.cube.Cube, startcoords: tuple, endcoords: tuple):
    """Compute transect between startcoords and endcoords.

    Computes a transect for a given cube containing at least latitude
    and longitude coordinates, using an appropriate sampling interval along the
    transect based on grid spacing. Also decides a suitable x coordinate to plot along
    the transect - see notes for details on this.

    Arguments
    ---------

    cube: Cube
        An iris cube containing latitude and longitude coordinate dimensions,
        to compute the transect on.
    startcoords: tuple
        A tuple containing the start coordinates for the transect using model coordinates,
        ordered (latitude,longitude).
    endcoords: tuple
        A tuple containing the end coordinates for the transect using model coordinates,
        ordered (latitude,longitude).

    Returns
    -------
    cube: Cube
        A cube containing at least pressure and the coordinate specified by coord, for
        the transect specified between startcoords and endcoords.

    Notes
    -----
    This operator uses the iris.Nearest method to interpolate the specific point along
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

    lon_coord = cube.coord(lon_name)
    lat_coord = cube.coord(lat_name)

    _check_within_bounds(startcoords, lat_coord, lon_coord)
    _check_within_bounds(endcoords, lat_coord, lon_coord)

    # Compute vector distance between start and end points in degrees.
    dist_deg = np.sqrt(
        (startcoords[0] - endcoords[0]) ** 2 + (startcoords[1] - endcoords[1]) ** 2
    )

    # Compute minimum gap between x/y spatial coords.
    lon_min = np.abs(np.min(lon_coord.points[1:] - lon_coord.points[:-1]))
    lat_min = np.abs(np.min(lat_coord.points[1:] - lat_coord.points[:-1]))

    # For scenarios where coord is at 90 degree to the grid (i.e. no
    # latitude/longitude change). Only xmin or ymin will be zero, not both
    # (otherwise startcoords and endcoords the same).
    if startcoords[1] == endcoords[1]:
        # Along latitude.
        lon_pnts = np.repeat(startcoords[1], int(dist_deg / lat_min))
        lat_pnts = np.linspace(startcoords[0], endcoords[0], int(dist_deg / lat_min))
        transect_coord = "latitude"
    elif startcoords[0] == endcoords[0]:
        # Along longitude.
        lon_pnts = np.linspace(startcoords[1], endcoords[1], int(dist_deg / lon_min))
        lat_pnts = np.repeat(startcoords[0], int(dist_deg / lon_min))
        transect_coord = "longitude"
    else:
        # Else use the smallest grid space in x or y direction.
        number_of_points = int(dist_deg / np.min([lon_min, lat_min]))
        lon_pnts = np.linspace(startcoords[1], endcoords[1], number_of_points)
        lat_pnts = np.linspace(startcoords[0], endcoords[0], number_of_points)

        # If change in latitude larger than change in longitude:
        if abs(startcoords[0] - endcoords[0]) > abs(startcoords[1] - endcoords[1]):
            transect_coord = "latitude"
        elif abs(startcoords[0] - endcoords[0]) <= abs(startcoords[1] - endcoords[1]):
            transect_coord = "longitude"

    # Create cubelist to store interpolated points along transect.
    interpolated_cubes = iris.cube.CubeList()

    # Iterate over all points along transect, lon_pnts will be the same shape as
    # lat_pnts so we can use either to iterate over.
    for i in range(0, lon_pnts.shape[0]):
        logging.info("%s/%s", i + 1, lon_pnts.shape[0])

        # Get point along transect.
        cube_slice = cube.interpolate(
            [(lon_name, lon_pnts[i]), (lat_name, lat_pnts[i])], iris.analysis.Nearest()
        )

        # Remove existing coordinates ready to add one single map coordinate
        # Note latitude/longitude cubes may have additional AuxCoord to remove
        for coord_name in ["latitude", "longitude", "grid_latitude", "grid_longitude"]:
            try:
                cube_slice.remove_coord(coord_name)
            except iris.exceptions.CoordinateNotFoundError:
                pass

        if transect_coord == "latitude":
            dist_coord = iris.coords.DimCoord(
                lat_pnts[i], long_name="latitude", units="degrees"
            )
            cube_slice.add_aux_coord(dist_coord)
            cube_slice = iris.util.new_axis(cube_slice, scalar_coord="latitude")
        elif transect_coord == "longitude":
            dist_coord = iris.coords.DimCoord(
                lon_pnts[i], long_name="longitude", units="degrees"
            )
            cube_slice.add_aux_coord(dist_coord)
            cube_slice = iris.util.new_axis(cube_slice, scalar_coord="longitude")

        interpolated_cubes.append(cube_slice)

    # Concatenate into single cube.
    interpolated_cubes = interpolated_cubes.concatenate()

    # Add metadata to interpolated cubes showing coordinates.
    interpolated_cubes[0].attributes["transect_coords"] = (
        f"{startcoords[0]}_{startcoords[1]}_{endcoords[1]}_{endcoords[1]}"
    )
    # If concatenation successful, should be CubeList with one cube left.
    assert len(interpolated_cubes) == 1
    return interpolated_cubes[0]
