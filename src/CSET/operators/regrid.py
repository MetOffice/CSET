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

"""Operators to regrid cubes."""

import iris
import iris.cube
import numpy as np

from CSET.operators._utils import get_cube_yxcoordname


def regrid_onto_cube(
    toregrid: iris.cube.Cube | iris.cube.CubeList,
    target: iris.cube.Cube,
    method: str,
    **kwargs,
) -> iris.cube.Cube | iris.cube.CubeList:
    """Regrid a cube or cubelist, projecting onto a target cube.

    All cubes must have at least 2 spatial (map) dimensions.

    Arguments
    ----------
    toregrid: iris.cube | iris.cube.CubeList
        An iris Cube of data to regrid, or multiple cubes to regrid in a CubeList.
        A minimum requirement is that the cube(s) need to be 2D with a latitude,
        longitude coordinates.
    target: Cube
        An iris cube of the data to regrid onto. It needs to be 2D with a latitude,
        longitude coordinate.
    method: str
        Method used to regrid onto, etc. Linear will use iris.analysis.Linear()

    Returns
    -------
    iris.cube | iris.cube.CubeList
        An iris cube of the data that has been regridded, or a cubelist of the cubes
        that have been regridded in the same order they were passed in toregrid.

    Raises
    ------
    ValueError
        If a unique x/y coordinate cannot be found
    NotImplementedError
        If the cubes grid, or the method for regridding, is not yet supported.

    Notes
    -----
    Currently rectlinear grids (uniform) are supported.
    """
    # If only one cube, put into cubelist as an iterable.
    if type(toregrid) == iris.cube.Cube:
        toregrid = iris.cube.CubeList([toregrid])

    # To store regridded cubes
    regridded_cubes = iris.cube.CubeList()

    # Iterate over all cubes and regrid
    for cube in toregrid:
        # Get y,x coord names
        y_coord, x_coord = get_cube_yxcoordname(cube)

        # List of supported grids - check if it is compatible
        supported_grids = (iris.coord_systems.GeogCS,)
        if not isinstance(cube.coord(x_coord).coord_system, supported_grids):
            raise NotImplementedError(
                f"Does not currently support {cube.coord(x_coord).coord_system} coordinate system"
            )
        if not isinstance(cube.coord(y_coord).coord_system, supported_grids):
            raise NotImplementedError(
                f"Does not currently support {cube.coord(y_coord).coord_system} coordinate system"
            )

        regrid_method = getattr(iris.analysis, method, None)
        if callable(regrid_method):
            regridded_cubes.append(cube.regrid(target, regrid_method()))
        else:
            raise NotImplementedError(
                f"Does not currently support {method} regrid method"
            )

    # Preserve returning a cube if only a cube has been supplied to regrid.
    if len(regridded_cubes) == 1:
        return regridded_cubes[0]
    else:
        return regridded_cubes


def regrid_onto_xyspacing(
    toregrid: iris.cube.Cube | iris.cube.CubeList,
    xspacing: int,
    yspacing: int,
    method: str,
    **kwargs,
) -> iris.cube.Cube:
    """Regrid cube or cubelist onto a set x,y spacing.

    Regrid cube(s) using specified x,y spacing, which is performed linearly.

    Parameters
    ----------
    toregrid: iris.cube | iris.cube.CubeList
        An iris cube of the data to regrid, or multiple cubes to regrid in a cubelist.
        A minimum requirement is that the cube(s) need to be 2D with a latitude,
        longitude coordinates.
    xspacing: integer
        Spacing of points in longitude direction (could be degrees, meters etc.)
    yspacing: integer
        Spacing of points in latitude direction (could be degrees, meters etc.)
    method: str
        Method used to regrid onto, etc. Linear will use iris.analysis.Linear()

    Returns
    -------
    iris.cube | iris.cube.CubeList
        An iris cube of the data that has been regridded, or a cubelist of the cubes
        that have been regridded in the same order they were passed in toregrid.

    Raises
    ------
    ValueError
        If a unique x/y coordinate cannot be found
    NotImplementedError
        If the cubes grid, or the method for regridding, is not yet supported.

    Notes
    -----
    Currently rectlinear grids (uniform) are supported.

    """
    # If only one cube, put into cubelist as an iterable.
    if type(toregrid) == iris.cube.Cube:
        toregrid = iris.cube.CubeList([toregrid])

    # To store regridded cubes
    regridded_cubes = iris.cube.CubeList()

    # Iterate over all cubes and regrid
    for cube in toregrid:
        # Get x,y coord names
        y_coord, x_coord = get_cube_yxcoordname(cube)

        # List of supported grids - check if it is compatible
        supported_grids = (iris.coord_systems.GeogCS,)
        if not isinstance(cube.coord(x_coord).coord_system, supported_grids):
            raise NotImplementedError(
                f"Does not currently support {cube.coord(x_coord).coord_system} regrid method"
            )
        if not isinstance(cube.coord(y_coord).coord_system, supported_grids):
            raise NotImplementedError(
                f"Does not currently support {cube.coord(y_coord).coord_system} regrid method"
            )

        # Get axis
        lat, lon = cube.coord(y_coord), cube.coord(x_coord)

        # Get bounds
        lat_min, lon_min = lat.points.min(), lon.points.min()
        lat_max, lon_max = lat.points.max(), lon.points.max()

        # Generate new mesh
        latout = np.arange(lat_min, lat_max, yspacing)
        lonout = np.arange(lon_min, lon_max, xspacing)

        regrid_method = getattr(iris.analysis, method, None)
        if callable(regrid_method):
            regridded_cubes.append(
                cube.interpolate(
                    [(y_coord, latout), (x_coord, lonout)], regrid_method()
                )
            )
        else:
            raise NotImplementedError(
                f"Does not currently support {method} regrid method"
            )

    # Preserve returning a cube if only a cube has been supplied to regrid.
    if len(regridded_cubes) == 1:
        return regridded_cubes[0]
    else:
        return regridded_cubes
