# Copyright 2022 Met Office and contributors.
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

"""Operators to regrid cubes."""

from datetime import datetime
from typing import Union

import iris
import iris.cube


def regrid_onto_cube(incube: iris.cube.Cube, targetcube: iris.cube.Cube, methodplaceholder,
                     **kwargs) -> iris.cube.Cube:
    """Regrid cube using another cube as a target.

    Parameters
    ----------
    incube: Cube
        An iris cube of the data to regrid. As a minimum, it needs to be 2D with a latitude,
        longitude coordinates.
    targetcube: Cube
        An iris cube of the data to regrid onto. It needs to be 2D with a latitude,
        longitude coordinate, though I think more dims are acceptable and are ignored.
    methodplaceholder: iris.analysis
        Method used to regrid onto, such as iris.analysis.Linear()

    Returns
    -------
    iris.cube.Cube
        An iris cube of the data that has been regridded.
    """

    return incube.regrid(targetcube, methodplaceholder)


def regrid_onto_xyspacing(incube: iris.cube.Cube, xspacing: int, yspacing: int, methodplaceholder,
                          **kwargs) -> iris.cube.Cube:
    """Regrid cube onto a set x,y spacing. This could be a useful case where there
       is no cube to regrid onto? This only supports linear spacing for now...

    Parameters
    ----------
    incube: Cube
        An iris cube of the data to regrid. As a minimum, it needs to be 2D with a latitude,
        longitude coordinates.
    xspacing: integer
        Spacing of points in longitude direction (could be degrees, meters etc.)
    yspacing: integer
        Spacing of points in latitude direction (could be degrees, meters etc.)
    methodplaceholder: iris.analysis
        Method used to regrid onto, such as iris.analysis.Linear()

    Returns
    -------
    cube_rgd: Cube
        An iris cube of the data that has been regridded.
    """

    # Usual names for spatial coordinates
    X_COORD_NAMES = ["longitude", "grid_longitude",
                     "projection_x_coordinate", "x"]
    Y_COORD_NAMES = ["latitude", "grid_latitude",
                     "projection_y_coordinate", "y"]

    # Get a list of coordinate names for the cube
    coord_names = [coord.name() for coord in incube.coords()]

    # Check which x-coordinate we have, if any
    x_coords = [coord for coord in coord_names if coord in X_COORD_NAMES]
    if len(x_coords) != 1:
        raise ValueError("Could not identify a unique x-coordinate in cube")
    x_coord = incube.coord(x_coords[0])

    # Check which y-coordinate we have, if any
    y_coords = [coord for coord in coord_names if coord in Y_COORD_NAMES]
    if len(y_coords) != 1:
        raise ValueError("Could not identify a unique y-coordinate in cube")
    y_coord = incube.coord(y_coords[0])

    # Get axis
    lat,lon = x_wind.coord(y_coord),x_wind.coord(x_coord)

    # Get bounds
    lat_min,lon_min = lat.points.min(),lon.points.min()
    lat_max,lon_max = lat.points.max(),lon.points.max()

    # Generate new mesh
    latout = np.arange(lat_min, lat_max, yspacing)
    lonout = np.arange(lon_min, lon_max, xspacing)
    cube_rgd = incube.interpolate([(y_coord, latout), (x_coord, lonout)],
                                     methodplaceholder)

    return cube_rgd


