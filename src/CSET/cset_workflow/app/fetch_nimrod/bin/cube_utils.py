"""
General utility functions for use with Iris :class:`iris.cube.Cube` or \
:class:`iris.cube.CubeList` objects.
"""

import collections
import time
import warnings

import agg_regrid
import constants
import dask
import iris
import iris.analysis
import matplotlib
import numpy as np
import shapely.geometry as sgeom
from ants.regrid.rectilinear import TwoStage
from iris.experimental.regrid_conservative import regrid_conservative_via_esmpy

warnings.filterwarnings("ignore")


def get_temporal_range(cube):
    """
    Returns the time range spanned by the time coordinate of an input \
    :class:`iris.cube.Cube`, in the form [first time, last time].
    Time coordinate bounds are taken into account if present.
    """
    # Get a list of coordinate names for the cube
    coord_names = [coord.name() for coord in cube.coords()]
    # Check there is a time coordinate present
    if "time" not in coord_names:
        raise ValueError("Time coordinate not found in cube")
    time_coord = cube.coord("time")
    time_unit = time_coord.units
    if time_coord.has_bounds():
        # Use time bounds if present...
        times = time_coord.bounds
    else:
        # ...else just use the time points
        times = time_coord.points
    # Convert from numeric times to datetimes
    times = time_unit.num2date(times)
    return [np.min(times), np.max(times)]


def get_spatial_coords(cube):
    """Returns the x, y coordinates of an input :class:`iris.cube.Cube`."""
    # Usual names for spatial coordinates
    X_COORD_NAMES = ["longitude", "grid_longitude", "projection_x_coordinate", "x"]
    Y_COORD_NAMES = ["latitude", "grid_latitude", "projection_y_coordinate", "y"]

    # Get a list of coordinate names for the cube
    coord_names = [coord.name() for coord in cube.coords()]

    # Check which x-coordinate we have, if any
    x_coords = [coord for coord in coord_names if coord in X_COORD_NAMES]
    if len(x_coords) != 1:
        raise ValueError("Could not identify a unique x-coordinate in cube")
    x_coord = cube.coord(x_coords[0])

    # Check which y-coordinate we have, if any
    y_coords = [coord for coord in coord_names if coord in Y_COORD_NAMES]
    if len(y_coords) != 1:
        raise ValueError("Could not identify a unique y-coordinate in cube")
    y_coord = cube.coord(y_coords[0])

    return [x_coord, y_coord]


def get_spatial_coord_dims(cube):
    """
    Returns a tuple of the dimensions corresponding to the x, y coordinates \
    of an input :class:`iris.cube.Cube`.
    """
    # Get the spatial coordinates of the cube...
    x_coord, y_coord = get_spatial_coords(cube)
    # ...then the cube dimensions corresponding to these coordinates
    x_dim = cube.coord_dims(x_coord)[0]
    y_dim = cube.coord_dims(y_coord)[0]
    return (x_dim, y_dim)


def get_spatial_extent(cube):
    """
    Takes an :class:`iris.cube.Cube` and returns its spatial extent in the \
    form of a list [min x, max x, min y, max y].
    """
    # Get the spatial coordinates of the cube
    x_coord, y_coord = get_spatial_coords(cube)
    return [
        min(x_coord.points),
        max(x_coord.points),
        min(y_coord.points),
        max(y_coord.points),
    ]


def get_non_spatial_coords(cube):
    """
    Returns a list of the non-spatial coordinates of an input \
    :class:`iris.cube.Cube`.
    """
    # Get a list of the cube coordinates
    coords = cube.coords()
    # Get the spatial coordinates of the cube
    x_coord, y_coord = get_spatial_coords(cube)
    # Remove the spatial coordinates from the list of coordinates
    coords.remove(x_coord)
    coords.remove(y_coord)
    return coords


def guess_bounds(cube):
    """
    Takes an input :class:`iris.cube.Cube`, guesses bounds on the x, y \
    coordinates, then returns the cube. Such bounds are often required by \
    regridding algorithms.
    """
    # Loop over spatial coordinates
    for axis in ["x", "y"]:
        coord = cube.coord(axis=axis)
        # Check that this is not a variable resolution grid
        # TODO: Does bounds really not work with variable resolution? AVD
        # seem to think it won't...
        try:
            _ = iris.util.regular_step(coord)
        except:
            raise ValueError("Cannot guess bounds for a variable resolution grid")
        # Guess bounds if there aren't any
        if coord.bounds is None:
            coord.guess_bounds()
    return cube


def remove_bounds(cube):
    """
    Takes an input :class:`iris.cube.Cube`, removes any bounds on the x, y \
    coordinates, then returns the cube.
    """
    # Loop over spatial coordinates
    for axis in ["x", "y"]:
        cube.coord(axis=axis).bounds = None
    return cube


def remove_cell_method(cube, cell_method):
    """
    Removes the supplied :class:`iris.coords.CellMethod` from an input
    :class:`iris.cube.Cube`, then returns the cube.
    """
    cell_methods = [cm for cm in cube.cell_methods if cm != cell_method]
    cube.cell_methods = ()
    for cm in cell_methods:
        cube.add_cell_method(cm)
    return cube


def get_grid(cube):
    """
    Takes an :class:`iris.cube.Cube` and returns its spatial grid as a 2D \
    :class:`iris.cube.Cube`.
    """
    # Take a copy of the input cube
    grid_cube = cube.copy()
    # Get the spatial coordinates of the cube
    x_coord, y_coord = get_spatial_coords(grid_cube)

    # Take an arbitrary spatial slice of the cube
    grid_cube = next(grid_cube.slices([y_coord, x_coord]))
    # We don't care about the data of this slice so just zero it
    grid_cube.data = np.zeros(grid_cube.data.shape)
    # Add a mask to show which points in the spatial grid are to be
    # considered valid. By default, all of them (False means not masked in
    # masked arrays)
    mask = np.zeros(grid_cube.data.shape, dtype=bool)
    grid_cube.data = np.ma.array(grid_cube.data, mask=mask)
    # Remove all non-spatial coordinates from the cube
    coords = grid_cube.coords()

    coords.remove(x_coord)
    coords.remove(y_coord)

    for coord in coords:
        grid_cube.remove_coord(coord)

    # Set some metadata to signify this is just a grid cube
    grid_cube.standard_name = None
    grid_cube.long_name = "Grid"
    grid_cube.units = "no_unit"
    grid_cube.cell_methods = None
    grid_cube.attributes = {}

    return grid_cube


def get_grid_spacing(cube):
    """
    Takes a :class:`iris.cube.Cube` and returns a tuple (dx, dy) of the grid \
    spacings in the x, y directions.
    """
    # Get the spatial coordinates of the cube
    x_coord, y_coord = get_spatial_coords(cube)
    # Note that regular_step will fail for variable resolution grids
    dx = iris.util.regular_step(x_coord)
    dy = iris.util.regular_step(y_coord)
    return (dx, dy)


def get_min_max_grid_spacing(cube):
    """
    Takes a :class:`iris.cube.Cube` and returns a tuple of the minimum and \
    maximum grid spacings in either of the x, y directions.
    """
    # Get the grid spacings in the x, y directions
    dx, dy = get_grid_spacing(cube)
    return (np.min([dx, dy]), np.max([dx, dy]))


def trim_cube(cube, xmin=None, xmax=None, ymin=None, ymax=None, ignore_bounds=True):
    """
    Trims the spatial extent of an :class:`iris.cube.Cube` to lie in a \
    specified range.

    Arguments:

    * **cube** - an :class:`iris.cube.Cube` object.

    Keyword arguments:

    * **xmin** - minimum value of the cube x-coordinate to select.
    * **xmax** - maximum value of the cube x-coordinate to select.
    * **ymin** - minimum value of the cube y-coordinate to select.
    * **ymax** - maximum value of the cube y-coordinate to select.
    * **ignore_bounds** - set to True to ignore any bounds on the coordinates \
                          and just consider their points.

    Returns
    -------
    * **trimmed_cube** - a copy of the input :class:`iris.cube.Cube` with \
                         x, y coordinate values restricted to the specified \
                         ranges.
    """
    # Take a copy of the input cube
    trimmed_cube = cube.copy()

    # Get the spatial coordinates of the cube
    x_coord, y_coord = get_spatial_coords(trimmed_cube)

    # First trim the cube in the x direction...
    if xmin is None:
        xmin = np.min(x_coord.points)
    xmin -= constants.REAL_MATCH_TOL
    if xmax is None:
        xmax = np.max(x_coord.points)
    xmax += constants.REAL_MATCH_TOL
    x_extent = iris.coords.CoordExtent(x_coord, xmin, xmax)

    trimmed_cube = trimmed_cube.intersection(x_extent, ignore_bounds=ignore_bounds)

    # ...now trim the cube in the y direction
    if ymin is None:
        ymin = np.min(y_coord.points)
    ymin -= constants.REAL_MATCH_TOL
    if ymax is None:
        ymax = np.max(y_coord.points)
    ymax += constants.REAL_MATCH_TOL
    y_extent = iris.coords.CoordExtent(y_coord, ymin, ymax)
    trimmed_cube = trimmed_cube.intersection(y_extent, ignore_bounds=ignore_bounds)

    return trimmed_cube


def trim_variable_grid(cube):
    """
    Removes any variable resolution part of the spatial grid of an input \
    :class:`iris.cube.Cube`.
    """
    # Take a copy of the input cube
    trimmed_cube = cube.copy()
    # Loop over spatial coordinates
    for axis in ["x", "y"]:
        delta = None
        # Keep looping until the variable resolution part of the grid has been
        # fully removed
        while delta is None:
            coord = trimmed_cube.coord(axis=axis)
            try:
                # This will fail for variable resolution grids
                delta = iris.util.regular_step(coord)
            except:
                # Remove one grid cell from either end of the axis
                trimmed_coord = coord.points[1:-1]
                trimmed_cube = trimmed_cube.intersection(
                    iris.coords.CoordExtent(
                        coord, np.min(trimmed_coord), np.max(trimmed_coord)
                    )
                )
    return trimmed_cube


def get_boundary(cube, coord_system_out=None):
    """
    Determines the boundary of the spatial grid of an :class:`iris.cube.Cube` \
    in a given coordinate system.

    Arguments:

    * **cube** - an :class:`iris.cube.Cube` object.

    Keyword arguments:

    * **coord_system_out** - an instance of \
                             :class:`iris.coord_systems.CoordSystem` that \
                             specifies the coordinate system the boundary is \
                             to be computed in. If not supplied, the boundary \
                             is determined in the same coordinate system as \
                             the input cube.

    Returns
    -------
    * **boundary** - a :class:`shapely.geometry.Polygon` object describing the \
                     boundary of the cube spatial grid in the specified \
                     coordinate system.
    """
    coord_system_in = cube.coord_system()
    if coord_system_out is None:
        coord_system_out = coord_system_in

    # Check desired coordinate system is either GeogCS or RotatedGeogCS
    if not isinstance(
        coord_system_out, (iris.coord_systems.GeogCS, iris.coord_systems.RotatedGeogCS)
    ):
        msg = ("Unsupported coordinate system supplied {0:s}").format(coord_system_out)
        raise NotImplementedError(msg)

    # Get x, y coordinates of cube spatial grid
    x, y = iris.analysis.cartography.get_xy_grids(cube)

    if coord_system_out == coord_system_in:
        # Nothing to do
        pass
    else:
        # Transform the x, y coordinates of the cube spatial grid to the
        # new coordinate system, coord_system_out
        xy = coord_system_out.as_cartopy_crs().transform_points(
            coord_system_in.as_cartopy_crs(), x, y
        )
        x = xy[:, :, 0]
        y = xy[:, :, 1]

    # Construct a Shapely Polygon object describing the boundary of the cube
    # spatial grid by taking the edges of the x, y coordinate arrays
    left = list(map(list, zip(*[x[:, 0], y[:, 0]], strict=False)))
    top = list(map(list, zip(*[x[-1, :], y[-1, :]], strict=False)))
    right = list(
        map(list, zip(*[np.flipud(x[:, -1]), np.flipud(y[:, -1])], strict=False))
    )
    bottom = list(
        map(list, zip(*[np.flipud(x[0, :]), np.flipud(y[0, :])], strict=False))
    )

    boundary = left + top + right + bottom
    boundary = sgeom.Polygon(boundary)

    return boundary


def mask_outside_boundary(cube, boundary, distance=None):
    """
    Masks cube data outside a given spatial boundary.

    Arguments:

    * **cube** - an :class:`iris.cube.Cube` object.
    * **boundary** - a :class:`shapely.geometry.Polygon` object specifying the \
                     boundary of a spatial region. Data at points outside this \
                     boundary will be masked.

    Keyword arguments:

    * **distance** - a factor to grow (distance > 0) or shrink (distance < 0) \
                     the specified boundary by.

    Returns
    -------
    * **masked_cube** - a new cube that is the same as the input \
                        :class:`iris.cube.Cube` but with data masked at points \
                        outside the supplied boundary.
    """
    # Get spatial grid of input cube
    grid_cube = get_grid(cube)

    # Get cube x, y coordinates of grid cube as a list of points
    x, y = iris.analysis.cartography.get_xy_grids(grid_cube)
    points = list(map(list, zip(x.ravel(), y.ravel(), strict=False)))

    # Grow or shrink boundary polygon by specified factor
    if distance is not None:
        boundary = boundary.buffer(distance)

    # Turn the boundary into a Path object
    x, y = boundary.exterior.xy
    x = np.asarray(x)
    y = np.asarray(y)
    boundary = list(map(list, zip(x.ravel(), y.ravel(), strict=False)))

    boundary = matplotlib.path.Path(boundary)

    # Find the points inside the boundary
    points_inside_boundary = boundary.contains_points(points)
    points_inside_boundary = points_inside_boundary.reshape(grid_cube.shape)

    # The array points_inside_boundary is boolean, with points inside the
    # boundary set to True and those outside set to False. To use this as
    # an array mask (see below), flip True <-> False (masked arrays have
    # masked elements set to True)
    points_inside_boundary = np.invert(points_inside_boundary)

    # Use points_inside_boundary as a mask on the data of the input cube
    x_dim, y_dim = get_spatial_coord_dims(cube)
    # Make a mask the same size as the input cube
    mask = iris.util.broadcast_to_shape(
        points_inside_boundary, cube.shape, [y_dim, x_dim]
    )
    # Take a copy of the input cube for masking
    masked_cube = cube.copy()
    if isinstance(masked_cube.data, np.ma.MaskedArray):
        # If the input cube already has a mask, combine it with the new mask
        mask = np.ma.mask_or(mask, masked_cube.data.mask)
        masked_cube.data.mask = mask
    else:
        # Mask the cube data
        masked_cube.data = np.ma.array(masked_cube.data, mask=mask)
    return masked_cube


def check_regrid_required(cube, grid_cube):
    """
    Given two :class:`iris.cube.Cube` objects - a data cube and a cube \
    defining a desired spatial grid - this tests if their coordinate systems \
    and grid spacings are the same. If not, a regrid of the data cube would \
    be required to get it onto the spatial grid defined by the grid cube.

    Arguments:

    * **cube** - an :class:`iris.cube.Cube` object holding the data that \
                 may need to be regridded.
    * **grid_cube** - an :class:`iris.cube.Cube` object defining the desired \
                      spatial grid.

    Returns
    -------
    * **regrid_required** - False if the coordinate systems and grid \
                            spacings of the data cube and grid cube are the \
                            same. True otherwise.
    """
    # Get the coordinate system and grid spacing of the input cube
    cube_coord_system = cube.coord_system()
    cube_grid_spacing = get_grid_spacing(cube)

    # Get the coordinate system and grid spacing of the cube defining the
    # desired spatial grid
    grid_coord_system = grid_cube.coord_system()
    grid_spacing = get_grid_spacing(grid_cube)

    # Start by assuming no regrid would be required
    regrid_required = False

    # Check if the coordinate systems of the cube and the desired grid
    # differ. If so, a regrid would be required.
    if cube_coord_system != grid_coord_system:
        regrid_required = True

    # Check if the resolution of the cube and the desired grid differ.
    # If so, a regrid would be required.
    if not all(np.isclose(np.asarray(cube_grid_spacing), np.asarray(grid_spacing))):
        regrid_required = True

    return regrid_required


def regrid_cube(cube, grid_cube, method="linear", mdtol=1):
    """
    Regrids a cube onto a specified spatial grid.

    Arguments:

    * **cube** - an input :class:`iris.cube.Cube` to be regridded.
    * **grid_cube** - an :class:`iris.cube.Cube` object defining the desired \
                      spatial grid.

    Keyword arguments:

    * **method** - string specifying the regridding method to use. Can be \
                   any of:

      * nearest - nearest-neighbour scheme :class:`iris.analysis.Nearest` \
                  (non-conservative).
      * linear - linear scheme :class:`iris.analysis.Linear` (non-conservative).
      * area_weighted - area-weighted scheme \
                        :class:`iris.analysis.AreaWeighted` (conservative).
      * esmpy - regrid using ESMPy :func:`iris.experimental.regrid_conservative\
.regrid_conservative_via_esmpy` (conservative).
      * agg - regrid using Anti-Grain Geometry (conservative).
      * two_stage - ANTS two-stage regridder (linear followed by \
                    area-weighted; approximately conservative).

    * **mdtol** - Tolerance of missing data. The value returned in each \
                  element of the returned array will be masked if the \
                  fraction of missing data exceeds mdtol. This fraction \
                  is calculated based on the area of masked cells within \
                  each target cell. mdtol=0 means no masked data is \
                  tolerated while mdtol=1 will mean the resulting \
                  element will be masked if and only if all the overlapping \
                  elements of the source grid are masked. Defaults to 1. \
                  This is only used for method="AREA_WEIGHTED".

    Returns
    -------
    * **result** - the input :class:`iris.cube.Cube` regridded onto the \
                   desired spatial grid.
    """
    # Guess spatial bounds on input cubes
    cube = guess_bounds(cube)
    grid_cube = guess_bounds(grid_cube)

    # Do regridding
    t_start = time.time()

    if method == "nearest":
        # Nearest-neighbour
        print("Nearest-neighbour regridding...")
        result = cube.regrid(
            grid_cube, iris.analysis.Nearest(extrapolation_mode="mask")
        )
    elif method == "linear":
        # Linear
        print("Linear regridding...")
        result = cube.regrid(grid_cube, iris.analysis.Linear(extrapolation_mode="mask"))
    elif method == "area_weighted":
        # Area-weighted
        # Requires cube and grid_cube to have the same coordinate system and
        # all spatial coordinates must be rectilinear (1D)
        print("Area-weighted regridding...")
        result = cube.regrid(grid_cube, iris.analysis.AreaWeighted(mdtol=mdtol))
    elif method == "esmpy":
        # ESMPy
        print("Regridding via ESMPy...")
        result = regrid_conservative_via_esmpy(cube, grid_cube)
    elif method == "agg":
        # AGG regrid
        print("Regridding via agg regrid...")
        result = cube.regrid(grid_cube, agg_regrid.AreaWeighted())
    elif method == "two_stage":
        # ANTS two_stage (linear followed by area-weighted) regrid
        with dask.config.set({"multiprocessing.context": "spawn"}):
            print("Regridding via ANTS two-stage...")
            result = cube.regrid(grid_cube, TwoStage(mdtol=mdtol))
    else:
        raise ValueError("Unrecognised regrid method {0:s}".format(method))

    # Timing information
    t_end = time.time()
    time_taken = t_end - t_start
    print("Time taken {0:.2f} s".format(time_taken))

    return result


def unrotate_pole(cube):
    """
    Transforms the spatial coordinates of an input :class:`iris.cube.Cube` \
    object from a rotated pole coordinate system to standard \
    latitude/longitude coordinates.
    """
    # Take a copy of the input cube
    unrot_cube = cube.copy()

    # If the cube has a coordinate system with a rotated pole, do the
    # unrotation
    coord_system = unrot_cube.coord_system()
    if isinstance(coord_system, iris.coord_systems.RotatedGeogCS):
        # Get the latitude/longitude of the rotated pole
        pole_lat = coord_system.grid_north_pole_latitude
        pole_lon = coord_system.grid_north_pole_longitude

        # x, y coordinates in the rotated pole coordinate system
        x, y = iris.analysis.cartography.get_xy_grids(unrot_cube)

        # Unrotate the x, y coordinates to standard lat/lon
        x, y = iris.analysis.cartography.unrotate_pole(x, y, pole_lon, pole_lat)

        # Remove the existing spatial coordinates of the cube (in the
        # rotated pole coordinate system)...
        x_coord, y_coord = get_spatial_coords(unrot_cube)
        x_dim, y_dim = get_spatial_coord_dims(unrot_cube)
        unrot_cube.remove_coord(x_coord)
        unrot_cube.remove_coord(y_coord)

        # ...and replace them with new standard lat/lon coordinates (2D)
        target_coord_system = iris.coord_systems.GeogCS(
            iris.fileformats.pp.EARTH_RADIUS
        )
        x_coord = iris.coords.AuxCoord(
            x,
            standard_name="longitude",
            units="degrees_east",
            coord_system=target_coord_system,
        )
        y_coord = iris.coords.AuxCoord(
            y,
            standard_name="latitude",
            units="degrees_north",
            coord_system=target_coord_system,
        )
        unrot_cube.add_aux_coord(x_coord, (y_dim, x_dim))
        unrot_cube.add_aux_coord(y_coord, (y_dim, x_dim))

    return unrot_cube


def rotate_pole(cube, pole_lat, pole_lon):
    """
    Transforms the spatial coordinates of an :class:`iris.cube.Cube` object \
    from standard latitude/longitude coordinates to a rotated pole coordinate \
    system.

    Arguments:

    * **cube** - an input :class:`iris.cube.Cube` object.
    * **pole_lat** - latitude of the rotated North pole.
    * **pole_lon** - longitude of the rotated North pole.
    """
    # Take a copy of the input cube
    rot_cube = cube.copy()

    # If the cube has a standard latitude/longitude coordinate system, do the
    # rotation
    coord_system = rot_cube.coord_system()
    if isinstance(coord_system, iris.coord_systems.GeogCS):
        # Get the standard lat/lon x, y coordinates
        x, y = iris.analysis.cartography.get_xy_grids(rot_cube)

        # Rotate the x, y coordinates to the rotated pole coordinate system
        x, y = iris.analysis.cartography.rotate_pole(x, y, pole_lon, pole_lat)

        # Remove the existing spatial coordinates of the cube...
        x_coord, y_coord = get_spatial_coords(rot_cube)
        x_dim, y_dim = get_spatial_coord_dims(rot_cube)
        rot_cube.remove_coord(x_coord)
        rot_cube.remove_coord(y_coord)

        # ...and replace them with new (2D) coordinates in the rotated
        # pole coordinate system
        target_coord_system = iris.coord_systems.RotatedGeogCS(
            pole_lat, pole_lon, ellipsoid=coord_system
        )
        x_coord = iris.coords.AuxCoord(
            x,
            standard_name="grid_longitude",
            units="degrees",
            coord_system=target_coord_system,
        )
        y_coord = iris.coords.AuxCoord(
            y,
            standard_name="grid_latitude",
            units="degrees",
            coord_system=target_coord_system,
        )
        rot_cube.add_aux_coord(x_coord, (y_dim, x_dim))
        rot_cube.add_aux_coord(y_coord, (y_dim, x_dim))

    return rot_cube


def remove_duplicates(cubelist):
    """
    Removes any duplicate :class:`iris.cube.Cube` objects from an \
    :class:`iris.cube.CubeList`.
    """
    # Nothing to do if the cubelist is empty
    if not cubelist:
        return cubelist
    # Build up a list of indices of the cubes to remove because they are
    # duplicated
    indices_to_remove = []
    for i in range(len(cubelist) - 1):
        cube_i = cubelist[i]
        for j in range(i + 1, len(cubelist)):
            cube_j = cubelist[j]
            if cube_i == cube_j:
                if j not in indices_to_remove:
                    indices_to_remove.append(j)
    # Only keep unique cubes
    cubelist = iris.cube.CubeList(
        [cube for index, cube in enumerate(cubelist) if index not in indices_to_remove]
    )
    return cubelist


def repeat_scalar_coord_along_dim_coord(cubelist, scalar_coord_name, dim_coord_name):
    """
    For each :class:`iris.cube.Cube` in a given :class:`iris.cube.CubeList`, \
    this extends (by repetition) a specified scalar coordinate along the \
    dimension corresponding to a specified dimension coordinate.
    """
    for cube in cubelist:
        scalar_coord = cube.coord(scalar_coord_name)
        # Check the coordinate referenced by scalar_coord_name is indeed
        # a scalar coordinate. Otherwise nothing to do.
        if scalar_coord.points.size == 1:
            # Get the data value held by the scalar coordinate...
            scalar_coord_val = scalar_coord.points[0]
            # ...then remove it from the cube
            cube.remove_coord(scalar_coord)
            # Extract the dimension coordinate matching dim_coord_name
            dim_coord = cube.coord(dim_coord_name)
            # Get the dimension spanned by this dimension coordinate...
            dim = cube.coord_dims(dim_coord_name)[0]
            # ...and its length
            dim_size = dim_coord.points.size
            # Construct an auxillary coordinate by replicating the data
            # value from the scalar coordinate to match the size of the
            # specified dimension coordinate
            scalar_coord = iris.coords.AuxCoord(
                np.repeat(scalar_coord_val, dim_size), long_name=scalar_coord_name
            )

            # Add the new auxillary coordinate to the cube
            cube.add_aux_coord(scalar_coord, dim)

    return cubelist


def extract_overlapping(cubelist, coord_name):
    """
    Extracts regions from cubes in a :class:`iris.cube.CubeList` such that \
    the specified coordinate is the same across all cubes.

    Arguments:

    * **cubelist** - an input :class:`iris.cube.CubeList`.
    * **coord_name** - a string specifying the name of the coordinate \
                       over which to perform the extraction.

    Returns a :class:`iris.cube.CubeList` where the coordinate corresponding \
    to coord_name is the same for all cubes.
    """
    # Build a list of all Cell instances for this coordinate by
    # looping through all cubes in the supplied cubelist
    all_cells = []
    for cube in cubelist:
        for cell in cube.coord(coord_name).cells():
            all_cells.append(cell)

    # Work out which coordinate Cell instances are common across
    # all cubes in the cubelist...
    cell_counts = collections.Counter(all_cells)
    # unique_cells = cell_counts.keys()
    unique_cells = list(cell_counts.keys())
    unique_cell_counts = list(cell_counts.values())
    num_cubes = len(cubelist)
    common_cells = [
        unique_cells[i]
        for i, count in enumerate(unique_cell_counts)
        if count == num_cubes
    ]
    # ...and use these to subset the cubes in the cubelist
    constraint = iris.Constraint(
        coord_values={coord_name: lambda cell: cell in common_cells}
    )

    cubelist = iris.cube.CubeList([cube.extract(constraint) for cube in cubelist])
    return cubelist


def cube_data_func(cube_data_1, cube_data_2):
    """
    Takes two :class:`numpy.ndarray` arrays and combines them in quadrature.
    """
    return np.sqrt(cube_data_1**2 + cube_data_2**2)


def cube_units_func(cube_1, cube_2):
    """
    Compares the units of two :class:`iris.cube.Cube` objects to see if \
    they are the same.
    """
    if cube_1.units != getattr(cube_2, "units", cube_1.units):
        raise ValueError("Cube units do not match")
    return cube_1.units


#: Function to compute the vector magnitude of two cubes (e.g. wind speed)
vector_magnitude = iris.analysis.maths.IFunc(cube_data_func, cube_units_func)
