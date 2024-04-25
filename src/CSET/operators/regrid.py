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

# Usual names for spatial coordinates.
# TODO can we determine grid coord names in a more intelligent way?
X_COORD_NAMES = ["longitude", "grid_longitude", "projection_x_coordinate", "x"]
Y_COORD_NAMES = ["latitude", "grid_latitude", "projection_y_coordinate", "y"]


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
    The acceptable coordinate names for X and Y coordinates are currently described
    in X_COORD_NAMES and Y_COORD_NAMES. These cover commonly used coordinate types,
    though a user can append new ones.
    Currently rectlinear grids (uniform) are supported.
    """
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
    The acceptable coordinate names for X and Y coordinates are currently described
    in X_COORD_NAMES and Y_COORD_NAMES. These cover commonly used coordinate types,
    though a user can append new ones.
    Currently rectlinear grids (uniform) are supported.

    """
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


# ***** We created this new Operator as a modified version of the one above.
#      We added the "lon_pt" and "lat_pt" as new inputs specifying the chosen point.
def regrid_to_single_point(
    incube: iris.cube.Cube, lat_pt: float, lon_pt: float, method: str, **kwargs
) -> iris.cube.Cube:
    """Select data at a single point by longitude and latitude.

    Selection is performed by a regrid function, selecting the nearest gridpoint to
    the selected longitude and latitude values.

    Parameters
    ----------
    incube: Cube
        An iris cube of the data to regrid. As a minimum, it needs to be 2D with a latitude,
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
        An iris cube of the data at the specified point (this will have time
        and/or height dimensions).

    Raises
    ------
    ValueError
        If a unique x/y coordinate cannot be found; also if, for selecting a single
        gridpoint, the chosen longitude and latitude point is outside the domain.
    [TO DO: these limits may need updating to exclude selecting points too near the
    boundaries.]
    NotImplementedError
        If the cubes grid, or the method for regridding, is not yet supported.

    Notes
    -----
    The acceptable coordinate names for X and Y coordinates are currently described
    in X_COORD_NAMES and Y_COORD_NAMES. These cover commonly used coordinate types,
    though a user can append new ones.
    Currently rectlinear grids (uniform) are supported.

    """
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

    # List of supported grids - check if it is compatible
    supported_grids = (iris.coord_systems.GeogCS, iris.coord_systems.RotatedGeogCS)
    # **** We added the RotatedGeogCS grid to the list above
    #      so that it works with rotated grids.
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

    # Check to see if selected point is outside the domain
    if (
        (lat_pt < lat_min)
        or (lat_pt > lat_max)
        or (lon_pt < lon_min)
        or (lon_pt > lon_max)
    ):
        raise ValueError("Selected point is outside the domain.")
    # **** We added these criteria to check that the point is within the domain.

    regrid_method = getattr(iris.analysis, method, None)
    if callable(regrid_method):
        cube_rgd = incube.interpolate(
            [(y_coord, lat_pt), (x_coord, lon_pt)], regrid_method
        )
        # **** This is then the updated interpolation method, reflects exactly the same
        #     as the version above ("regrid_onto_xyspacing").
    else:
        raise NotImplementedError(f"Does not currently support {method} regrid method")

    return cube_rgd
