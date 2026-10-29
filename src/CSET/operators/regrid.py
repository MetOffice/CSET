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
import warnings

import iris
import iris.coord_systems
import iris.cube
import numpy as np
from iris.analysis.cartography import rotate_pole

from CSET._common import iter_maybe
from CSET.operators._utils import get_cube_yxcoordname

logger = logging.getLogger(__name__)


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
                np.abs(lat_tr - lat.points[0]) > 0.1
                or np.abs(lon_tr - lon.points[0]) > 0.1
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


from functools import reduce

def interpolate_to_point_cube(
    fld: iris.cube.Cube | iris.cube.CubeList, point_cube: iris.cube.Cube | iris.cube.CubeList, **kwargs
) -> iris.cube.Cube | iris.cube.CubeList:
    """Interpolate a 2D field in cube or CubeList to a set of points.

    Regrid cube(s) to set of sample points specified by point_cube.
    Ensures only matching times between input and point_cube are included.

    Parameters
    ----------
    fld: Cube | CubeList
        An iris cube or CubeList containing a two-dimensional field(s).
    point_cube: Cube
        An iris cube specifying the coord point(s) to which the data
        will be interpolated.

    Returns
    -------
    fld_point_cube: Cube | CubeList
        An iris cube or CubeList containing interpolated values at the
        points specified by the point cube for matching times common to
        both fld and point_cube.
    """

    # Empty CubeList To store regridded cubes.
    regridded_cubes = iris.cube.CubeList()

    # Generate array of point cube lat and lon points.
    point_lat_name, point_lon_name = get_cube_yxcoordname(point_cube)
    point_lats = point_cube.coord(point_lat_name).points
    point_lons = point_cube.coord(point_lon_name).points

    # Iterate over all cubes and regrid.
    for cube in iter_maybe(fld):
        y_coord, x_coord = get_cube_yxcoordname(cube)

        # Rotate point_cube coords if required to match model coord rotation.
        if (
            isinstance(
                cube.coord(x_coord).coord_system, iris.coord_systems.RotatedGeogCS
            )
            and point_lat_name == "latitude"
            and point_lon_name == "longitude"
        ):
            point_lons_rp, point_lats_rp = rotate_pole(
                point_lons,
                point_lats,
                pole_lon=cube.coord(x_coord).coord_system.grid_north_pole_longitude,
                pole_lat=cube.coord(x_coord).coord_system.grid_north_pole_latitude,
            )
            sample_points = [
                ("grid_latitude", point_lats_rp),
                ("grid_longitude", point_lons_rp),
            ]
        # Default, sample points based on point cube dimensions
        else:
            sample_points = [
                (point_lat_name, np.array(point_lats)),
                (point_lon_name, np.array(point_lons)),
            ]

        # Interpolate fld cube to required sample points
        fld_point_cube = cube.interpolate(
            sample_points, iris.analysis.Linear(extrapolation_mode="mask")
        )

        diag_data = np.diagonal(
            fld_point_cube.data,
            axis1=-2,
            axis2=-1,
        )

        fv_cube = iris.cube.Cube(
            diag_data,
            standard_name=cube.standard_name,
            long_name=cube.long_name,
            units=cube.units,
        )

        #
        # Add all non-horizontal dimension coordinates
        # from the forecast cube.
        #
        out_dim = 0

        for coord in cube.coords(dim_coords=True):

            if coord.name() in (
                "latitude",
                "longitude",
                "grid_latitude",
                "grid_longitude",
            ):
                continue

            fv_cube.add_dim_coord(
                coord.copy(),
                out_dim,
            )

            out_dim += 1

        #
        # Station dimension is always last.
        #
        station_dim = out_dim

        fv_cube.add_dim_coord(
            point_cube.coord("station").copy(),
            station_dim,
        )

        #
        # Copy forecast auxiliary coordinates.
        #
        for coord in cube.coords():

            if coord.name() in (
                "latitude",
                "longitude",
                "grid_latitude",
                "grid_longitude",
            ):
                continue

            if coord.name() in [c.name() for c in fv_cube.coords()]:
                continue

            dims = cube.coord_dims(coord)

            if dims:
                fv_cube.add_aux_coord(
                    coord.copy(),
                    dims,
                )
            else:
                fv_cube.add_aux_coord(
                    coord.copy(),
                )

        #
        # Copy observation auxiliary coordinates.
        #
        for coord in point_cube.coords():

            if coord.name() in (
                "station",
                "forecast_period",
                "forecast_reference_time",
            ):
                continue

            if coord.name() in [c.name() for c in fv_cube.coords()]:
                continue

            dims = point_cube.coord_dims(coord)

            if dims:
                fv_cube.add_aux_coord(
                    coord.copy(),
                    dims,
                )
            else:
                fv_cube.add_aux_coord(
                    coord.copy(),
                )

        fv_cube.attributes = cube.attributes.copy()
        fv_cube.cell_methods = cube.cell_methods
        fv_cube.units = cube.units

        regridded_cubes.append(fv_cube)

    # Preserve returning a cube if only a cube supplied.
    if len(regridded_cubes) == 1:
        return regridded_cubes[0]

    return regridded_cubes


from iris.coords import AuxCoord, DimCoord
from iris.cube import Cube

import numpy as np


def extract_neighbourhood_to_point_cube(
    fld: Cube,
    point_cube: Cube,
    npoints: int = 5,
) -> Cube:
    """
    Extract an npoints x npoints neighbourhood around each station.

    Parameters
    ----------
    fld : Cube
        Model cube with dimensions

            (forecast_reference_time,
             forecast_period,
             latitude,
             longitude)

    point_cube : Cube
        Observation/station cube containing station metadata.

    npoints : int
        Width of neighbourhood to extract (must be odd).

    Returns
    -------
    Cube

        (forecast_reference_time,
         forecast_period,
         station,
         neighbourhood_y,
         neighbourhood_x)
    """

    if npoints % 2 == 0:
        raise ValueError(
            f"npoints must be odd, got {npoints}"
        )

    half_width = npoints // 2

    lat_points = fld.coord("latitude").points
    lon_points = fld.coord("longitude").points

    station_lats = point_cube.coord("latitude").points
    station_lons = point_cube.coord("longitude").points

    nfrt = fld.shape[0]
    nlead = fld.shape[1]
    nstation = len(station_lats)

    data = np.empty(
        (
            nfrt,
            nlead,
            nstation,
            npoints,
            npoints,
        ),
        dtype=fld.dtype,
    )

    for istation, (station_lat, station_lon) in enumerate(
        zip(station_lats, station_lons)
    ):

        iy = np.argmin(np.abs(lat_points - station_lat))
        ix = np.argmin(np.abs(lon_points - station_lon))

        y0 = iy - half_width
        y1 = iy + half_width + 1

        x0 = ix - half_width
        x1 = ix + half_width + 1

        if (
            y0 < 0
            or x0 < 0
            or y1 > len(lat_points)
            or x1 > len(lon_points)
        ):
            station_name = point_cube.coord(
                "Station_Name"
            ).points[istation]

            raise ValueError(
                f"Station '{station_name}' is too close "
                f"to the domain boundary for a "
                f"{npoints}x{npoints} neighbourhood."
            )

        data[:, :, istation, :, :] = fld.data[
            :,
            :,
            y0:y1,
            x0:x1,
        ]

    cube_out = Cube(
        data,
        standard_name=fld.standard_name,
        long_name=fld.long_name,
        var_name=fld.var_name,
        units=fld.units,
        attributes=fld.attributes.copy(),
        dim_coords_and_dims=[
            (
                fld.coord("forecast_reference_time").copy(),
                0,
            ),
            (
                fld.coord("forecast_period").copy(),
                1,
            ),
            (
                DimCoord(
                    np.arange(nstation),
                    long_name="station",
                ),
                2,
            ),
            (
                DimCoord(
                    np.arange(npoints),
                    long_name="neighbourhood_y",
                ),
                3,
            ),
            (
                DimCoord(
                    np.arange(npoints),
                    long_name="neighbourhood_x",
                ),
                4,
            ),
        ],
    )

    #
    # Preserve station metadata
    #
    for coord_name in [
        "Station_Name",
        "latitude",
        "longitude",
    ]:

        coord = point_cube.coord(coord_name)

        cube_out.add_aux_coord(
            coord.copy(),
            (2,),
        )

    return cube_out


def interpolate_neighbourhood_to_point_cube(
    fld: Cube | iris.cube.CubeList,
    point_cube: Cube,
    npoints: int = 5,
) -> Cube | iris.cube.CubeList:
    """
    Extract an npoints x npoints neighbourhood around each station.

    Parameters
    ----------
    fld : Cube | CubeList
        Model field(s) with dimensions

            (forecast_reference_time,
             forecast_period,
             latitude,
             longitude)

    point_cube : Cube
        Station cube with dimensions

            (forecast_reference_time,
             forecast_period,
             station)

    npoints : int
        Width of neighbourhood. Must be odd.

    Returns
    -------
    Cube | CubeList

        (forecast_reference_time,
         forecast_period,
         station,
         neighbourhood_y,
         neighbourhood_x)
    """
    output = iris.cube.CubeList()

    for cube in iter_maybe(fld):
        output.append(
            _interpolate_neighbourhood_to_point_cube(
                cube,
                point_cube,
                npoints=npoints,
            )
        )

    if len(output) == 1:
        return output[0]

    return output


def _interpolate_neighbourhood_to_point_cube(
    fld: Cube,
    point_cube: Cube,
    npoints: int,
) -> Cube:
    """
    Extract a neighbourhood around each station.
    """

    if npoints % 2 == 0:
        raise ValueError(
            f"npoints must be odd, got {npoints}"
        )

    half_width = npoints // 2

    lat = fld.coord("grid_latitude").points
    lon = fld.coord("grid_longitude").points

    lat_dim = fld.coord_dims("grid_latitude")[0]
    lon_dim = fld.coord_dims("grid_longitude")[0]

    station_lat = point_cube.coord("latitude").points
    station_lon = point_cube.coord("longitude").points

    nstation = len(station_lat)

    #
    # Output shape:
    #
    # original non-spatial dimensions
    # +
    # station
    # +
    # neighbourhood_y
    # +
    # neighbourhood_x
    #
    input_shape = list(fld.shape)

    output_shape = (
        input_shape[:lat_dim]
        + [nstation, npoints, npoints]
    )

    data = np.empty(
        output_shape,
        dtype=fld.dtype,
    )

    for istation, (slat, slon) in enumerate(
        zip(station_lat, station_lon)
    ):

        iy = np.argmin(np.abs(lat - slat))
        ix = np.argmin(np.abs(lon - slon))

        y0 = iy - half_width
        y1 = iy + half_width + 1

        x0 = ix - half_width
        x1 = ix + half_width + 1

        # Shift box back into domain if needed
        if y0 < 0:
            y1 -= y0
            y0 = 0

        if x0 < 0:
            x1 -= x0
            x0 = 0

        if y1 > len(lat):
            y0 -= y1 - len(lat)
            y1 = len(lat)

        if x1 > len(lon):
            x0 -= x1 - len(lon)
            x1 = len(lon)

        # Flexible extraction
        src_index = [slice(None)] * fld.ndim
        src_index[lat_dim] = slice(y0, y1)
        src_index[lon_dim] = slice(x0, x1)

        # Insert station dimension into destination
        dst_index = [slice(None)] * len(output_shape)
        dst_index[-3] = istation

        data[tuple(dst_index)] = fld.data[tuple(src_index)]

    #
    # Build output coordinates.
    #
    dim_coords_and_dims = []

    next_dim = 0

    for coord in fld.dim_coords:

        dims = fld.coord_dims(coord)

        # Skip spatial dimensions
        if lat_dim in dims or lon_dim in dims:
            continue

        dim_coords_and_dims.append(
            (
                coord.copy(),
                next_dim,
            )
        )

        next_dim += 1

    station_dim = next_dim
    neigh_y_dim = next_dim + 1
    neigh_x_dim = next_dim + 2

    dim_coords_and_dims.extend(
        [
            (
                DimCoord(
                    np.arange(nstation),
                    long_name="station",
                ),
                station_dim,
            ),
            (
                DimCoord(
                    np.arange(npoints),
                    long_name="neighbourhood_y",
                ),
                neigh_y_dim,
            ),
            (
                DimCoord(
                    np.arange(npoints),
                    long_name="neighbourhood_x",
                ),
                neigh_x_dim,
            ),
        ]
    )

    cube_out = Cube(
        data,
        standard_name=fld.standard_name,
        long_name=fld.long_name,
        var_name=fld.var_name,
        units=fld.units,
        attributes=fld.attributes.copy(),
        dim_coords_and_dims=dim_coords_and_dims,
    )

    #
    # Preserve station metadata.
    #
    for coord_name in [
        "Station_Name",
        "latitude",
        "longitude",
    ]:

        cube_out.add_aux_coord(
            point_cube.coord(coord_name).copy(),
            (station_dim,),
        )

    return cube_out



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
