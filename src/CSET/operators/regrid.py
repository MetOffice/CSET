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

"""Operators to regrid cubes."""

import logging
import re
import warnings

import iris
import iris.coord_systems
import iris.coords as icoords
import iris.cube
import numpy as np
from scipy.interpolate import LinearNDInterpolator

from CSET._common import iter_maybe
from CSET.operators._utils import get_cube_yxcoordname


class BoundaryWarning(UserWarning):
    """Selected gridpoint is close to the domain edge.

    In many cases gridpoints near the domain boundary contain non-physical
    values, so caution is advised when interpreting them.
    """


def regrid_onto_cube(
    toregrid: iris.cube.Cube | iris.cube.CubeList,
    target: iris.cube.Cube,
    method: str,
    **kwargs,
) -> iris.cube.Cube | iris.cube.CubeList:
    """Regrid a cube or CubeList, projecting onto a target cube.

    All cubes must have at least 2 spatial (map) dimensions.

    Arguments
    ----------
    toregrid: iris.cube | iris.cube.CubeList
        An iris Cube of data to regrid, or multiple cubes to regrid in a
        CubeList. A minimum requirement is that the cube(s) need to be 2D with a
        latitude, longitude coordinates.
    target: Cube
        An iris cube of the data to regrid onto. It needs to be 2D with a
        latitude, longitude coordinate.
    method: str
        Method used to regrid onto, etc. Linear will use iris.analysis.Linear()

    Returns
    -------
    iris.cube | iris.cube.CubeList
        An iris cube of the data that has been regridded, or a CubeList of the
        cubes that have been regridded in the same order they were passed in
        toregrid.

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
    # To store regridded cubes.
    regridded_cubes = iris.cube.CubeList()

    # Iterate over all cubes and regrid.
    for cube in iter_maybe(toregrid):
        # Get y,x coord names
        y_coord, x_coord = get_cube_yxcoordname(cube)

        # List of supported grids - check if it is compatible
        supported_grids = (iris.coord_systems.GeogCS, iris.coord_systems.RotatedGeogCS)
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
    xspacing: float,
    yspacing: float,
    method: str,
    **kwargs,
) -> iris.cube.Cube | iris.cube.CubeList:
    """Regrid cube or cubelist onto a set x,y spacing.

    Regrid cube(s) using specified x,y spacing, which is performed linearly.

    Parameters
    ----------
    toregrid: iris.cube | iris.cube.CubeList
        An iris cube of the data to regrid, or multiple cubes to regrid in a
        cubelist. A minimum requirement is that the cube(s) need to be 2D with a
        latitude, longitude coordinates.
    xspacing: float
        Spacing of points in longitude direction (could be degrees, meters etc.)
    yspacing: float
        Spacing of points in latitude direction (could be degrees, meters etc.)
    method: str
        Method used to regrid onto, etc. Linear will use iris.analysis.Linear()

    Returns
    -------
    iris.cube | iris.cube.CubeList
        An iris cube of the data that has been regridded, or a cubelist of the
        cubes that have been regridded in the same order they were passed in
        toregrid.

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
    # To store regridded cubes.
    regridded_cubes = iris.cube.CubeList()

    # Iterate over all cubes and regrid.
    for cube in iter_maybe(toregrid):
        # Get x,y coord names
        y_coord, x_coord = get_cube_yxcoordname(cube)

        # List of supported grids - check if it is compatible
        supported_grids = (iris.coord_systems.GeogCS, iris.coord_systems.RotatedGeogCS)
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


def regrid_to_single_point(
    cubes: iris.cube.Cube | iris.cube.CubeList,
    lat_pt: float,
    lon_pt: float,
    latlon_in_type: str = "rotated",
    method: str = "Nearest",
    boundary_margin: int = 8,
    **kwargs,
) -> iris.cube.Cube:
    """Select data at a single point by longitude and latitude.

    Selection of model grid point is performed by a regrid function, either
    selecting the nearest gridpoint to the selected longitude and latitude
    values or using linear interpolation across the surrounding points.

    Parameters
    ----------
    cubes: Cube | CubeList
        An iris cube or CubeList of the data to regrid. As a minimum, it needs
        to be 2D with latitude, longitude coordinates.
    lon_pt: float
        Selected value of longitude: this should be in the range -180 degrees to
        180 degrees.
    lat_pt: float
        Selected value of latitude: this should be in the range -90 degrees to
        90 degrees.
    latlon_in_type: str, optional
        Specify whether the input longitude and latitude point is in standard
        geographic realworld coordinates ("realworld") or on the rotated grid
        of the cube ("rotated"). Default is "rotated".
    method: str
        Method used to determine the values at the selected longitude and
        latitude. The recommended approach is to use iris.analysis.Nearest(),
        which selects the nearest gridpoint. An alternative is
        iris.analysis.Linear(), which obtains the values at the selected
        longitude and latitude by linear interpolation.
    boundary_margin: int, optional
        Number of grid points from the domain boundary considered "unreliable".
        Defaults to 8.

    Returns
    -------
    regridded_cubes: Cube | CubeList
        An iris cube or CubeList of the data at the specified point (this may
        have time and/or height dimensions).

    Raises
    ------
    ValueError
        If a unique x/y coordinate cannot be found; also if, for selecting a
        single gridpoint, the chosen longitude and latitude point is outside the
        domain; also (currently) if the difference between the actual and target
        points exceed 0.1 degrees.
    NotImplementedError
        If the cubes grid, or the method for regridding, is not yet supported.

    Notes
    -----
    The acceptable coordinate names for X and Y coordinates are currently
    described in X_COORD_NAMES and Y_COORD_NAMES. These cover commonly used
    coordinate types, though a user can append new ones. Currently rectilinear
    grids (uniform) are supported. Warnings are raised if the selected gridpoint
    is within boundary_margin grid lengths of the domain boundary as data here
    is potentially unreliable.
    """
    # To store regridded cubes.
    regridded_cubes = iris.cube.CubeList()

    # Iterate over all cubes and regrid.
    for cube in iter_maybe(cubes):
        # Get x and y coordinate names.
        y_coord, x_coord = get_cube_yxcoordname(cube)

        # List of supported grids - check if it is compatible
        # NOTE: The "RotatedGeogCS" option below seems to be required for rotated grids --
        #  this may need to be added in other places in these Operators.
        supported_grids = (iris.coord_systems.GeogCS, iris.coord_systems.RotatedGeogCS)
        if not isinstance(cube.coord(x_coord).coord_system, supported_grids):
            raise NotImplementedError(
                f"Does not currently support {cube.coord(x_coord).coord_system} regrid method"
            )
        if not isinstance(cube.coord(y_coord).coord_system, supported_grids):
            raise NotImplementedError(
                f"Does not currently support {cube.coord(y_coord).coord_system} regrid method"
            )

        # Transform input coordinates onto rotated grid if requested
        if latlon_in_type == "realworld":
            lon_tr, lat_tr = transform_lat_long_points(lon_pt, lat_pt, cube)
        elif latlon_in_type == "rotated":
            lon_tr, lat_tr = lon_pt, lat_pt

        # Get axis
        lat, lon = cube.coord(y_coord), cube.coord(x_coord)

        # Get bounds
        lat_min, lon_min = lat.points.min(), lon.points.min()
        lat_max, lon_max = lat.points.max(), lon.points.max()

        # Use different logic for single point obs data.
        if len(cube.coord(x_coord).points) > 1:
            # Get boundaries of frame to avoid selecting gridpoint close to domain edge
            lat_min_bound, lon_min_bound = (
                lat.points[boundary_margin - 1],
                lon.points[boundary_margin - 1],
            )
            lat_max_bound, lon_max_bound = (
                lat.points[-boundary_margin],
                lon.points[-boundary_margin],
            )

            # Check to see if selected point is outside the domain
            if (lat_tr < lat_min) or (lat_tr > lat_max):
                raise ValueError("Selected point is outside the domain.")
            else:
                if (lon_tr < lon_min) or (lon_tr > lon_max):
                    if (lon_tr + 360.0 >= lon_min) and (lon_tr + 360.0 <= lon_max):
                        lon_tr += 360.0
                    elif (lon_tr - 360.0 >= lon_min) and (lon_tr - 360.0 <= lon_max):
                        lon_tr -= 360.0
                    else:
                        raise ValueError("Selected point is outside the domain.")

            # Check to see if selected point is near the domain boundaries
            if (
                (lat_tr < lat_min_bound)
                or (lat_tr > lat_max_bound)
                or (lon_tr < lon_min_bound)
                or (lon_tr > lon_max_bound)
            ):
                warnings.warn(
                    f"Selected point is within {boundary_margin} gridlengths of the domain edge, data may be unreliable.",
                    category=BoundaryWarning,
                    stacklevel=2,
                )

            regrid_method = getattr(iris.analysis, method, None)
            if not callable(regrid_method):
                raise NotImplementedError(
                    f"Does not currently support {method} regrid method"
                )

            cube_rgd = cube.interpolate(((lat, lat_tr), (lon, lon_tr)), regrid_method())
            regridded_cubes.append(cube_rgd)
        else:
            if (
                np.abs((lat_tr - lat.points[0])) > 0.1
                or np.abs((lon_tr - lon.points[0])) > 0.1
            ):
                raise ValueError(
                    "Selected point is too far from the specified coordinates. It should be within 0.1 degrees."
                )
            else:
                print(
                    "*** lat/long diffs",
                    np.abs(lat_tr - lat_pt),
                    np.abs(lon_tr - lon_pt),
                )
                regridded_cubes.append(cube)

    # Preserve returning a cube if only a cube has been supplied to regrid.
    if len(regridded_cubes) == 1:
        return regridded_cubes[0]
    else:
        return regridded_cubes


def transform_lat_long_points(lon, lat, cube):
    """Transform a selected point in longitude and latitude.

    Transform the coordinates of a point from the real world
    grid to the corresponding point on the rotated grid of a cube.

    Parameters
    ----------
    cube: Cube
        An iris cube of data defining the rotated grid to be used in
        the longitude-latitude transformation.
    lon: float
        Selected value of longitude: this should be in the range -180 degrees to
        180 degrees.
    lat: float
        Selected value of latitude: this should be in the range -90 degrees to
        90 degrees.

    Returns
    -------
    lon_rot, lat_rot: float
        Coordinates of the selected point on the rotated grid specified within
        the selected cube.

    """
    import cartopy.crs as ccrs

    rot_pole = cube.coord_system().as_cartopy_crs()
    true_grid = ccrs.Geodetic()
    rot_coords = rot_pole.transform_point(lon, lat, true_grid)
    lon_rot = rot_coords[0]
    lat_rot = rot_coords[1]

    return lon_rot, lat_rot


def interpolate_to_point_cube(
    fld: iris.cube.Cube | iris.cube.CubeList, point_cube: iris.cube.Cube, **kwargs
) -> iris.cube.Cube | iris.cube.CubeList:
    """Interpolate from a 2D field to a set of points.

    Interpolate the 2D field in fld to the set of points
    specified in point_cube.

    Parameters
    ----------
    fld: Cube
        An iris cube containing a two-dimensional field.
    point_cube: Cube
        An iris cube specifying the point to which the data
        will be interpolated.

    Returns
    -------
    fld_point_cube: Cube
        An iris cube containing interpolated values at the points
        specified by the point cube.

    """
    #
    # As a basis, create a copy of the point cube.
    fld_point_cube = point_cube.copy()
    # Get indices of positional coordinates. We assume that the
    # point cube is unrotated.
    klon = None
    klat = None
    for kc in range(len(fld_point_cube.aux_coords)):
        if fld_point_cube.aux_coords[kc].standard_name == "latitude":
            klat = kc
        elif fld_point_cube.aux_coords[kc].standard_name == "longitude":
            klon = kc
    #
    # The input may have a rotated coordinate system.
    if len(fld.coords("grid_latitude")) > 0:
        # Interpolate in rotated coordinates.
        rot_csyst = fld.coords("grid_latitude")[0].coord_system
        rotpt = iris.analysis.cartography.rotate_pole(
            fld_point_cube.aux_coords[klon].points,
            fld_point_cube.aux_coords[klat].points,
            rot_csyst.grid_north_pole_longitude,
            rot_csyst.grid_north_pole_latitude,
        )
        # Add other interpolation options later.
        fld_interpolator = iris.analysis.Linear(extrapolation_mode="mask").interpolator(
            fld, ["time", "grid_latitude", "grid_longitude"]
        )
        for jt in range(len(fld_point_cube.coords("time")[0].points)):
            fld_point_cube.data[jt, :] = np.ma.masked_invalid(
                [
                    fld_interpolator(
                        [
                            fld_point_cube.coord("time").points[jt],
                            rotpt[1][k],
                            rotpt[0][k],
                        ]
                    ).data
                    if ~point_cube.data.mask[jt][k]
                    else np.nan
                    for k in range(len(rotpt[0]))
                ]
            )
    else:
        # Add other interpolation options later.
        fld_interpolator = iris.analysis.Linear(extrapolation_mode="mask").interpolator(
            fld, ["time", "latitude", "longitude"]
        )
        for jt in range(len(fld_point_cube.coords("time")[0].points)):
            fld_point_cube.data[jt, :] = np.ma.masked_invalid(
                [
                    fld_interpolator(
                        [
                            fld_point_cube.coords("time")[0].points[jt],
                            fld_point_cube.coord("latitude").points[k],
                            fld_point_cube.coord("longitude").points[k],
                        ]
                    ).data
                    if ~point_cube.data.mask[jt][k]
                    else np.nan
                    for k in range(fld_point_cube.coord("latitude").points)
                ]
            )
    return fld_point_cube


# Lookup dictionary
UGRID_VAR_LOOKUP = {
    "t": {"long_name": "temperature_at_pressure_levels", "units": "K"},
    "u": {"long_name": "zonal_wind_at_pressure_levels", "units": "m s-1"},
    "v": {"long_name": "meridional_wind_at_pressure_levels", "units": "m s-1"},
    "w": {"long_name": "vertical_wind_at_pressure_levels", "units": "m s-1"},
    "q": {
        "long_name": "vapour_specific_humidity_at_pressure_levels_for_climate_averaging",
        "units": "kg kg-1",
    },
    "z": {"long_name": "geopotential_height_at_pressure_levels", "units": "m"},
    "sp": {"long_name": "surface_air_pressure", "units": "Pa"},
    "10u": {"long_name": "eastward_wind_at_10m", "units": "m s-1"},
    "10v": {"long_name": "northward_wind_at_10m", "units": "m s-1"},
    "lsm": {"long_name": "land_binary_mask"},
    "2t": {"long_name": "temperature_at_screen_level", "units": "K"},
    "2d": {"long_name": "dew_point_temperature_at_screen_level", "units": "K"},
    "skt": {"long_name": "grid_surface_temperature", "units": "K"},
    "tp": {"long_name": "surface_microphysical_rainfall_rate", "units": "mm 6hr-1"},
    "latitude": {"long_name": "latitude", "units": "degrees"},
    "longitude": {"long_name": "longitude", "units": "degrees"},
}


def _rebuild_ugrid_meta_firstfix(cube):
    """
    Rebuild iris cube metadata.

    The cube will have metadata within its name and an additional pressure auxiliary
    coordinate inferred from the cube name if present.

    Parameters
    ----------
    cube : iris.cube.Cube
        Original unstructured source cube, used for fixing metadata.

    Returns
    -------
    iris.cube.Cube
        A structured iris cube with appropriate metadata.
    """
    # Get original cube time coordinate dimension.
    try:
        time_coord = cube.coord("time")
    except iris.exceptions.CoordinateNotFoundError:
        return None

    # Create new ugrid coordinate placeholder.
    #  ugrid_coord = icoords.DimCoord(np.arange(cube.shape[1]))

    # Parse cube name, to determine if it contains a likely pressure variable/level.
    # If it can't parse this pattern, returns None
    m = re.match(r"^([a-zA-Z][a-zA-Z0-9]*|\d+[a-zA-Z]+)(?:_(\d+))?$", cube.name())

    # Extract variable and pressure from cube name components.
    # If it can't find, returns None.
    var_key, pressure_hpa = m.group(1), m.group(2)

    # Rename cube using lookup dictionary, if a lookup exists.
    meta = UGRID_VAR_LOOKUP.get(var_key)

    if meta is None:
        return
    else:
        # If there is a number in cube name that can be split.
        if pressure_hpa is not None:
            # Create new pressure coordinate dimension.
            pressure_coord = icoords.DimCoord(
                [int(pressure_hpa)],
                long_name="pressure",
                units="hPa",
            )

            # If ndim = 1, a single 2D timeslice with pressure and time.
            if cube.ndim == 1:
                arr = cube.core_data()[np.newaxis, np.newaxis, :]
            else:
                arr = cube.core_data()[:, np.newaxis, :]

            out_cube = iris.cube.Cube(
                arr,
                dim_coords_and_dims=[
                    (time_coord, 0),
                    (pressure_coord, 1),
                    (icoords.DimCoord(np.arange(arr.shape[-1])), 2),
                ],
            )

        else:
            # Not a pressure level variable, so only 3 dimensions.
            # If ndim = 1, a single 2D timeslice withd time.
            if cube.ndim == 1:
                arr = cube.core_data()[np.newaxis, :]
            else:
                arr = cube.core_data()

            out_cube = iris.cube.Cube(
                arr,
                dim_coords_and_dims=[
                    (time_coord, 0),
                    (icoords.DimCoord(np.arange(arr.shape[-1])), 1),
                ],
            )

        # Fix cube metadata
        out_cube.long_name = meta["long_name"]
        out_cube.units = meta["units"]
        out_cube.rename(meta["long_name"])

        # Add forecast reference time as 'time_origin' to mimic lfric where it will
        # reconstruct forecast_period in a later callback.
        # Extract the origin string from the units
        time_origin = time_coord.units.origin

        # Strip the "seconds since " part.
        time_origin = time_origin.split("since ")[1]

        # Add to cube attributes as str.
        out_cube.coord("time").attributes["time_origin"] = time_origin

    return out_cube


def _rebuild_ugrid_meta(cube, arr, lat, lon):
    """
    Rebuild iris cube metadata.

    The cube will have metadata within its name and an additional pressure auxiliary
    coordinate inferred from the cube name if present.

    Parameters
    ----------
    cube : iris.cube.Cube
        Original unstructured source cube, used for fixing metadata.
    arr : np.ndarray
        Numpy array of UGRID data.
    lat : np.ndarray
        1D latitude coordinate values of regridded data
    lon : np.ndarray
        1D longitude coordinate values of regridded data

    Returns
    -------
    iris.cube.Cube
        A structured iris cube with appropriate metadata.
    """
    # Create new latitude coordinate.
    lat_coord = icoords.DimCoord(
        lat,
        standard_name="grid_latitude",
        units="degrees",
    )

    # Create new longitude coordinate.
    lon_coord = icoords.DimCoord(
        lon,
        standard_name="grid_longitude",
        units="degrees",
    )

    # Get original cube time coordinate dimension.
    time_coord = cube.coord("time")

    try:
        pressure_coord = cube.coord("pressure")
    except iris.exceptions.CoordinateNotFoundError:
        pressure_coord = None

    if pressure_coord is not None:
        # Create length 1 axis to match shape for pressure
        arr = arr[:, np.newaxis, :, :]

        # Create new cube with these dimensions.
        out_cube = iris.cube.Cube(
            arr,
            dim_coords_and_dims=[
                (time_coord, 0),
                (pressure_coord, 1),
                (lat_coord, 2),
                (lon_coord, 3),
            ],
        )

    else:
        out_cube = iris.cube.Cube(
            arr,
            dim_coords_and_dims=[
                (time_coord, 0),
                (lat_coord, 1),
                (lon_coord, 2),
            ],
        )

    # Set units/cube name from previous constructed cube.
    out_cube.standard_name = cube.standard_name
    out_cube.long_name = cube.long_name
    out_cube.units = cube.units

    # Copy attributes.
    out_cube.attributes = cube.attributes.copy()

    # Change units, geopot in m2 s-2.
    if out_cube.long_name == "geopotential_height_at_pressure_levels":
        out_cube.data = out_cube.data / 9.81

    # Raw data in units of 6h accum in meters.
    if out_cube.long_name == "surface_microphysical_rainfall_rate":
        out_cube.data = (out_cube.data * 1000.0) / 6

    return out_cube


def _restructure_ugrid_regrid(cube, tri, lat_grid, lon_grid, xy):
    """
    Restructure a flattened/unstructured cube.

    Parameters
    ----------
    cube : iris.cube
        An iris cube to restructure.
    tri : scipy.spatial._qhull.Delaunay
        A scipy object containing the triangulation mapping of cell points.
    lat_grid : np.ndarray
        1D latitude coordinate values of target grid.
    lon_grid : np.ndarray
        1D longitude coordinate values of target grid.
    xy : np.ndarray
        Meshed and flattened target grid points.

    Returns
    -------
    iris.cube.Cube
        A structured iris cube with appropriate metadata.

    Notes
    -----
    This function uses a pre-calculated triangulation, to save rebuilding for
    every cube. This therefore assumes all cubes being restructured have the
    same flattened structure.
    """
    # Create empty numpy array to store regridded data.
    out = np.empty((cube.shape[0], lat_grid.size, lon_grid.size))

    logging.debug(f"Interpolating {cube.name()}")

    # Extract and transpose source data values.
    src_vals = cube.data.T

    # Build linear interpolator object mapping target triangulation to source values.
    interp = LinearNDInterpolator(tri, src_vals)

    # Interpolate values onto target grid using linear interpolation.
    out_flat = interp(xy)

    # Transpose, and reshape to target 2D regular lat/lon grid.
    out = out_flat.T.reshape(cube.shape[0], lat_grid.size, lon_grid.size)

    # Rebuild metadata using lookup table (mostly for anemoi ML models).
    out_cube = _rebuild_ugrid_meta(cube, out, lat_grid, lon_grid)

    # Return restructured cube with appropriate metadata
    return out_cube


def prefilter_fix_metadata(cubes, constraint):
    """
    Pre-filter cubes prior to regridding to reduce excess compute.

    Parse cubes and filter for required variable, alongside latitude and
    longitude, for further processing. This reduces compute overhead on
    variables that we don't require. This also cleans metadata prior to filtering.

    Parameters
    ----------
    cubes : iris.cube.CubeList
        A cubelist containing unstructured cubes, along with cubes containing
        latitude and longitude information.

    constraint : iris.constraint
        Constraint in order to extract required variable.

    Returns
    -------
    filterd_cubes : iris.cube.CubeList
        A cubelist containing the required cube that matches the constraint, along
        with latitude and longitude cubes.
    """
    # Add metadata to variables, if appropriate
    sanitised_cubes = iris.cube.CubeList()
    for cube in cubes:
        out = _rebuild_ugrid_meta_firstfix(cube)
        if out is not None:
            sanitised_cubes.append(out)

    # Create empty cubelist.
    filtered_cubes = iris.cube.CubeList()

    # Extract latitude and longitude cubes, and append these to filtered_cubes.
    filtered_cubes.append(cubes.extract("latitude")[0])
    filtered_cubes.append(cubes.extract("longitude")[0])

    # Extract required cube based on constraint.
    for c in sanitised_cubes.extract(constraint):
        filtered_cubes.append(c)

    # Ensure we have found more than just latitude/longitude cubes
    if len(filtered_cubes) < 3:
        raise ValueError(f"Only found 2 or less cubes {filtered_cubes}")

    return filtered_cubes


def restructure_ugrid(cubes, constraint):
    """
    Restructure ugrid cubes using parallel processing.

    Parameters
    ----------
    cubes : iris.cube.CubeList
        A cubelist containing unstructured cubes, along with cubes containing
        latitude and longitude information.

    constraint: iris.Constraint
        An iris constraint (or combined constraint) to filter cubes on.

    Returns
    -------
    fixed_cubes: iris.cube.CubeList
        A list of iris cubes, that have been restructured onto a regular grid,
        with appropriate corrections to metadata.
    """
    # First, parse all cubes and fix their metadata (apart from latitude/longitude,
    # which we do later after regridding), and extract required variable from constraint.
    cubes = prefilter_fix_metadata(cubes, constraint)

    # First, extract latitude and longitude coordinates
    lat = cubes.extract("latitude")[0].data
    lon = cubes.extract("longitude")[0].data
    points = np.column_stack((lon, lat))

    # Create output mesh, using standard grid ~2km resolution
    # TODO: discussions with ML developers to include metadata so
    # we don't have to guess target lat/lon resolution.
    # For now, we assume data no higher resolution than 2p2km.
    # This will have impacts on PDFs.
    lon_grid = np.arange(lon.data.min(), lon.data.max(), 0.02)
    lat_grid = np.arange(lat.data.min(), lat.data.max(), 0.02)
    Lon2d, Lat2d = np.meshgrid(lon_grid, lat_grid)

    # Flatten target points
    xy = np.column_stack((Lon2d.ravel(), Lat2d.ravel()))

    # Build triangulation via a dummy interpolator
    tri_interp = LinearNDInterpolator(points, np.zeros(points.shape[0]))
    tri = tri_interp.tri

    fixed_cubes = iris.cube.CubeList()

    # For each cube, where ndim > 1 (excluding latitude/longitude array), do regridding
    # on array.
    for cube in cubes:
        if cube.ndim > 1:
            result_arr = _restructure_ugrid_regrid(cube, tri, lat_grid, lon_grid, xy)
            fixed_cubes.append(result_arr)

    return fixed_cubes.concatenate()


def vertical_interpolation(
    cubes: iris.cube.Cube | iris.cube.CubeList,
    coordinate: str,
    target: iris.cube.Cube | iris.cube.CubeList,
) -> iris.cube.Cube | iris.cube.CubeList:
    """Vertical interpolation of a cube to match that off a different cube.

    Acts as a wrapper around the `cube.interpolate` functionality and uses
    linear interpolation as the method.

    Parameters
    ----------
    cubes: iris.cube.Cube | iris.cube.CubeList
        An iris cube or cubelist of data defining field that should be
        vertically interpolated.
    coordinate: str
        The coordinate the interpolation occurs over.
    target: iris.cube.Cube | iris.cube.CubeList
        The target cube or cubelist that provides the vertical coordinate
        information. It will use `cube.coord(coordinate).points` to provide
        the vertical target. The number of target cubes should match the number
        of cubes used as input.

    Returns
    -------
    interpolated_cubes: iris.cube.Cube | iris.cube.CubeList
        Coordinates of the selected point on the rotated grid specified within
        the selected cube.
    """
    interpolated_cubes = iris.cube.CubeList([])
    for cube, cube_t in zip(iter_maybe(cubes), iter_maybe(target), strict=True):
        target_levels = cube_t.coord(coordinate).points
        new_cube = cube.interpolate(
            [(coordinate, target_levels)], iris.analysis.Linear()
        )
        interpolated_cubes.append(new_cube)
    if len(interpolated_cubes) == 1:
        return interpolated_cubes[0]
    else:
        return interpolated_cubes
