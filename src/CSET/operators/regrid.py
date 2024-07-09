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

import warnings

import iris
import iris.cube
import numpy as np

from CSET.operators._utils import get_cube_yxcoordname


class BoundaryWarning(UserWarning):
    """Selected gridpoint is close to the domain edge.

    In many cases gridpoints near the domain boundary contain non-physical
    values, so caution is advised when interpreting them.
    """


def regrid_onto_cube(
    incube: iris.cube.Cube, target: iris.cube.Cube, method: str, **kwargs
) -> iris.cube.Cube:
    """Regrid a cube, projecting onto a target cube.

    Cube must have at least 2 dimensions.

    Arguments
    ----------
    incube: Cube
        An iris cube of the data to regrid. As a minimum, it needs to be 2D with a latitude,
        longitude coordinates.
    target: Cube
        An iris cube of the data to regrid onto. It needs to be 2D with a latitude,
        longitude coordinate.
    method: str
        Method used to regrid onto, etc. Linear will use iris.analysis.Linear()

    Returns
    -------
    iris.cube.Cube
        An iris cube of the data that has been regridded.

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
    # Get y,x coord names
    y_coord, x_coord = get_cube_yxcoordname(incube)

    # List of supported grids - check if it is compatible
    supported_grids = (iris.coord_systems.GeogCS,)
    if not isinstance(incube.coord(x_coord).coord_system, supported_grids):
        raise NotImplementedError(
            f"Does not currently support {incube.coord(x_coord).coord_system} coordinate system"
        )
    if not isinstance(incube.coord(y_coord).coord_system, supported_grids):
        raise NotImplementedError(
            f"Does not currently support {incube.coord(y_coord).coord_system} coordinate system"
        )

    regrid_method = getattr(iris.analysis, method, None)
    if callable(regrid_method):
        return incube.regrid(target, regrid_method())
    else:
        raise NotImplementedError(f"Does not currently support {method} regrid method")


def regrid_onto_xyspacing(
    incube: iris.cube.Cube, xspacing: int, yspacing: int, method: str, **kwargs
) -> iris.cube.Cube:
    """Regrid cube onto a set x,y spacing.

    Regrid cube using specified x,y spacing, which is performed linearly.

    Parameters
    ----------
    incube: Cube
        An iris cube of the data to regrid. As a minimum, it needs to be 2D with a latitude,
        longitude coordinates.
    xspacing: integer
        Spacing of points in longitude direction (could be degrees, meters etc.)
    yspacing: integer
        Spacing of points in latitude direction (could be degrees, meters etc.)
    method: str
        Method used to regrid onto, etc. Linear will use iris.analysis.Linear()

    Returns
    -------
    cube_rgd: Cube
        An iris cube of the data that has been regridded.

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
    # Get x,y coord names
    y_coord, x_coord = get_cube_yxcoordname(incube)

    # List of supported grids - check if it is compatible
    supported_grids = (iris.coord_systems.GeogCS,)
    if not isinstance(incube.coord(x_coord).coord_system, supported_grids):
        raise NotImplementedError(
            f"Does not currently support {incube.coord(x_coord).coord_system} regrid method"
        )
    if not isinstance(incube.coord(y_coord).coord_system, supported_grids):
        raise NotImplementedError(
            f"Does not currently support {incube.coord(y_coord).coord_system} regrid method"
        )

    # Get axis
    lat, lon = incube.coord(y_coord), incube.coord(x_coord)

    # Get bounds
    lat_min, lon_min = lat.points.min(), lon.points.min()
    lat_max, lon_max = lat.points.max(), lon.points.max()

    # Generate new mesh
    latout = np.arange(lat_min, lat_max, yspacing)
    lonout = np.arange(lon_min, lon_max, xspacing)

    regrid_method = getattr(iris.analysis, method, None)
    if callable(regrid_method):
        cube_rgd = incube.interpolate(
            [(y_coord, latout), (x_coord, lonout)], regrid_method()
        )
    else:
        raise NotImplementedError(f"Does not currently support {method} regrid method")

    return cube_rgd


def regrid_to_single_point(
    incube: iris.cube.Cube, lat_pt: float, lon_pt: float, method: str, **kwargs
) -> iris.cube.Cube:
    """Select data at a single point by longitude and latitude.

    Selection of model grid point is performed by a regrid function, either selecting the
    nearest gridpoint to the selected longitude and latitude values or using linear
    interpolation across the surrounding points.

    Parameters
    ----------
    incube: Cube
        An iris cube of the data to regrid. As a minimum, it needs to be 2D with latitude,
        longitude coordinates.
    lon_pt: float
        Selected value of longitude.
    lat_pt: float
        Selected value of latitude.
    method: str
        Method used to determine the values at the selected longitude and latitude.
        The recommended approach is to use iris.analysis.Nearest(), which selects the
        nearest gridpoint. An alternative is iris.analysis.Linear(), which obtains
        the values at the selected longitude and latitude by linear interpolation.

    Returns
    -------
    cube_rgd: Cube
        An iris cube of the data at the specified point (this may have time
        and/or height dimensions).

    Raises
    ------
    ValueError
        If a unique x/y coordinate cannot be found; also if, for selecting a single
        gridpoint, the chosen longitude and latitude point is outside the domain.
    NotImplementedError
        If the cubes grid, or the method for regridding, is not yet supported.

    Notes
    -----
    The acceptable coordinate names for X and Y coordinates are currently described
    in X_COORD_NAMES and Y_COORD_NAMES. These cover commonly used coordinate types,
    though a user can append new ones.
    Currently rectilinear grids (uniform) are supported.
    Warnings are raised if the selected gridpoint is within eight gridlengths of the
    domain boundary as data here is potentially unreliable.

    """
    # Get x and y coordinate names.
    y_coord, x_coord = get_cube_yxcoordname(incube)

    # List of supported grids - check if it is compatible
    # NOTE: The "RotatedGeogCS" option below seems to be required for rotated grids --
    #  this may need to be added in other places in these Operators.
    supported_grids = (iris.coord_systems.GeogCS, iris.coord_systems.RotatedGeogCS)
    if not isinstance(incube.coord(x_coord).coord_system, supported_grids):
        raise NotImplementedError(
            f"Does not currently support {incube.coord(x_coord).coord_system} regrid method"
        )
    if not isinstance(incube.coord(y_coord).coord_system, supported_grids):
        raise NotImplementedError(
            f"Does not currently support {incube.coord(y_coord).coord_system} regrid method"
        )

    # Get axis
    lat, lon = incube.coord(y_coord), incube.coord(x_coord)

    # Get bounds
    lat_min, lon_min = lat.points.min(), lon.points.min()
    lat_max, lon_max = lat.points.max(), lon.points.max()

    # Get bounds
    # Boundaries of frame to avoid selecting gridpoint close to domain edge
    # Currently hardwired to 8 but could be a user input
    lat_min_bound, lon_min_bound = lat.points[7], lon.points[7]
    lat_max_bound, lon_max_bound = lat.points[-8], lon.points[-8]

    # Check to see if selected point is outside the domain
    if (
        (lat_pt < lat_min)
        or (lat_pt > lat_max)
        or (lon_pt < lon_min)
        or (lon_pt > lon_max)
    ):
        raise ValueError("Selected point is outside the domain.")
    else:
        if (
            (lat_pt < lat_min_bound)
            or (lat_pt > lat_max_bound)
            or (lon_pt < lon_min_bound)
            or (lon_pt > lon_max_bound)
        ):
            warnings.warn(
                "Selected point is within 8 gridlengths of the domain edge.",
                category=BoundaryWarning,
                stacklevel=2,
            )

    regrid_method = getattr(iris.analysis, method, None)
    if not callable(regrid_method):
        raise NotImplementedError(f"Does not currently support {method} regrid method")
    cube_rgd = incube.interpolate(((lat, lat_pt), (lon, lon_pt)), regrid_method())
    return cube_rgd
