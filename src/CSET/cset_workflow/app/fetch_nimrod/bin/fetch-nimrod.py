#! /usr/bin/env python3

"""Retrieve UK radar observations. Specific to the Met Office."""

import datetime

# import cube_utils
import time

import dateutil
import iris
import iris.coords
import iris.cube

# import agg_regrid
import numpy as np
from iris.experimental.regrid_conservative import regrid_conservative_via_esmpy

# from ants.regrid.rectilinear import TwoStage
# from CSET._workflow_utils.fetch_data import FileRetrieverABC, fetch_nimrod
from CSET.cset_workflow.app.fetch_fcst.bin.fetch_data import (
    FileRetrieverABC,
    fetch_nimrod,
)


def insert_datetime(filename, date_time):
    """
    Insert a datetime.

    Inserts a datetime into a file name containing date formatting characters.

    Arguments:

    * **filename** - the name of a file. If this contains any of the special \
                     date formatting characters

      * %Y - 4-digit year
      * %m - 2-digit month
      * %d - 2-digit day
      * %H - 2-digit hour
      * %M - 2-digit minute

      then these are replaced with numeric values derived from the components \
      of the supplied :class:`datetime.datetime` object.
    * **date_time** - a :class:`datetime.datetime` object specifying the \
                      datetime to insert in the given filename.

    Returns the input filename with date formatting characters replaced by \
    the appropriate components of date_time.
    """
    filename = filename.replace("%Y", "{0:04d}".format(date_time.year))
    filename = filename.replace("%m", "{0:02d}".format(date_time.month))
    filename = filename.replace("%d", "{0:02d}".format(date_time.day))
    filename = filename.replace("%H", "{0:02d}".format(date_time.hour))
    filename = filename.replace("%M", "{0:02d}".format(date_time.minute))

    return filename


def get_mean_period(time_coord):
    """
    Get mean period.

    Use the bounds information of an input :class:`iris.coords.Coord` object \
    representing a time coordinate to determine a unique time period over \
    which to compute time means.
    """
    # Check that the input time coordinate has bounds
    if not time_coord.has_bounds():
        msg = (
            "Supplied time coordinate must have bounds to define time "
            "periods over which to compute time means"
        )
        raise ValueError(msg)

    # Check the input time intervals to make sure they specify a sensible
    # meaning period
    time_unit = time_coord.units
    mean_period = [
        (end_time - start_time)
        for start_time, end_time in time_unit.num2date(time_coord.bounds)
    ]
    mean_period = list(set(mean_period))
    if len(mean_period) != 1:
        msg = (
            "Could not determine a unique time meaning period from "
            "input time coordinate"
        )
        raise ValueError(msg)
        #: Number of seconds in an hour.
    HOUR_IN_SECONDS = 3600
    mean_period = mean_period[0].total_seconds() / float(HOUR_IN_SECONDS)

    return mean_period


def guess_bounds(cube):
    """
    Guess bounds.

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
        except ValueError as err:
            raise ValueError(
                "Cannot guess bounds for a variable resolution grid"
            ) from err
        # Guess bounds if there aren't any
        if coord.bounds is None:
            coord.guess_bounds()
    return cube


def get_spatial_coords(cube):
    """
    Get spatial coords.

    Returns the x, y coordinates of an input :class:`iris.cube.Cube`.
    """
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
    Get spatial coords dims.

    Returns a tuple of the dimensions corresponding to the x, y coordinates \
    of an input :class:`iris.cube.Cube`.
    """
    # Get the spatial coordinates of the cube...
    x_coord, y_coord = get_spatial_coords(cube)
    # ...then the cube dimensions corresponding to these coordinates
    x_dim = cube.coord_dims(x_coord)[0]
    y_dim = cube.coord_dims(y_coord)[0]
    return (x_dim, y_dim)


def get_grid_spacing(cube):
    """
    Grid spacing.

    Takes a :class:`iris.cube.Cube` and returns a tuple (dx, dy) of the grid \
    spacings in the x, y directions.
    """
    # Get the spatial coordinates of the cube
    x_coord, y_coord = get_spatial_coords(cube)
    # Note that regular_step will fail for variable resolution grids
    dx = iris.util.regular_step(x_coord)
    dy = iris.util.regular_step(y_coord)
    return (dx, dy)


def check_regrid_required(cube, grid_cube):
    """
    Check grid.

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
    Regrid a cube onto a specified spatial grid.

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
    #    elif method == "agg":
    #        # AGG regrid
    #        print("Regridding via agg regrid...")
    #        result = cube.regrid(grid_cube, agg_regrid.AreaWeighted())
    #    elif method == "two_stage":
    #        # ANTS two_stage (linear followed by area-weighted) regrid
    #        with dask.config.set({"multiprocessing.context": "spawn"}):
    #            print("Regridding via ANTS two-stage...")
    #            result = cube.regrid(grid_cube, TwoStage(mdtol=mdtol))
    else:
        raise ValueError("Unrecognised regrid method {0:s}".format(method))

    # Timing information
    t_end = time.time()
    time_taken = t_end - t_start
    print("Time taken {0:.2f} s".format(time_taken))

    return result


def get_spatial_extent(cube):
    """
    Get spatial extent.

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


def trim_cube(cube, xmin=None, xmax=None, ymin=None, ymax=None, ignore_bounds=True):
    """
    Trim a cube.

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
    REAL_MATCH_TOL = 1.0e-4

    # Take a copy of the input cube
    trimmed_cube = cube.copy()

    # Get the spatial coordinates of the cube
    x_coord, y_coord = get_spatial_coords(trimmed_cube)

    # First trim the cube in the x direction...
    if xmin is None:
        xmin = np.min(x_coord.points)
    xmin -= REAL_MATCH_TOL
    if xmax is None:
        xmax = np.max(x_coord.points)
    xmax += REAL_MATCH_TOL
    x_extent = iris.coords.CoordExtent(x_coord, xmin, xmax)

    trimmed_cube = trimmed_cube.intersection(x_extent, ignore_bounds=ignore_bounds)

    # ...now trim the cube in the y direction
    if ymin is None:
        ymin = np.min(y_coord.points)
    ymin -= REAL_MATCH_TOL
    if ymax is None:
        ymax = np.max(y_coord.points)
    ymax += REAL_MATCH_TOL
    y_extent = iris.coords.CoordExtent(y_coord, ymin, ymax)
    trimmed_cube = trimmed_cube.intersection(y_extent, ignore_bounds=ignore_bounds)

    return trimmed_cube


def get_grid(cube):
    """
    Get grid.

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


class NimrodRetriever(FileRetrieverABC):
    """
    Class for Nimrod.

    Class for UK precipitation radar observations, a subclass of \
    :class:`FileRetrieverABC`.
    """

    def __init__(
        self,
        name,
        data_dir,
        filename,
        weights_filename,
        temporal_range,
        regrid_method="linear",
        field_name=None,
    ):
        """
        Initialise class.

        Arguments:

        * **name** - name for this observational dataset.
        * **data_dir** - directory where UK radar 1-hourly accumulation data \
                         files are located.
        * **filename** - names of the UK radar 1-hourly accumulation data \
                         files. Can contain any of the following special date \
                         formatting characters:

          * %Y - 4-digit year
          * %m - 2-digit month
          * %d - 2-digit day
          * %H - 2-digit hour
          * %M - 2-digit minute

        * **weights_filename** - names of the files holding the corresponding \
                                 weights for the 1-hour radar accumulations. \
                                 Can contain any of the following special date \
                                 formatting characters:

          * %Y - 4-digit year
          * %m - 2-digit month
          * %d - 2-digit day
          * %H - 2-digit hour
          * %M - 2-digit minute

        * **temporal_range** - a list of the form [first_time, last_time] \
                               specifying the time range covered by available \
                               UK radar data. first_time and last_time can be \
                               either :class:`datetime.datetime` objects or \
                               None for an open-ended range.

        Keyword arguments:

        * **field_name** - name of the field to extract from data files for \
                           this dataset.
        """
        FileRetrieverABC.__init__(
            self,
            name,
            data_dir,
            filename,
            temporal_range,
            regrid_method=regrid_method,
            field_name=field_name,
        )
        self.weights_filename = weights_filename
        # UK radar accumulations have an hourly frequency
        self.__frequency_in_hours = 1.0
        # The minimum number of valid rainrate values there must be in an
        # hourly accumulation for it to be used (the maximum possible number
        # is 13)
        self.__min_weight = 11

    def get_native_grid(self, grid_shift=None):
        """
        Return the spatial grid.

        Returns the spatial grid this observational dataset is defined on \
        as an :class:`iris.cube.Cube` object.

        Keyword arguments:

        * **grid_shift** * - Which grid to shift to

        .. warning ::
           grid_shift is not implemented for this class and must be set to None

        Raises
        ------
          NotImplementedError: Raised if grid_shift is set to anything other than None
        """
        if grid_shift is not None:
            raise NotImplementedError("grid_shift is not implemented for %s")

        # Choose a random data file to extract the grid from
        sample_file = self.get_sample_file()
        if sample_file is None:
            raise ValueError("Cannot determine grid without a sample data file")

        # Load sample data
        if self.field_name is None:
            cube = iris.load_cube(sample_file)
        else:
            cube = iris.load_cube(sample_file, self.field_name)

        # Extract spatial grid

        grid_cube = get_grid(cube)

        return grid_cube

    def get_data(self, time_coord, grid_cube=None, cutout=None):
        """
        Compute mean UK radar precipitation rates over a given time period.

        Arguments:

        * **time_coord** - a :class:`iris.coords.Coord` instance defining the \
                           time periods to compute mean precipitation rates \
                           for. The coordinate must have bounds as these are \
                           used to compute the time meaning period to use.

        Keyword arguments:

        * **grid_cube** - an :class:`iris.cube.Cube` object defining a spatial \
                          grid to regrid UK radar data onto.
        * **cutout** - a list specifying the longitude/latitude extent of a \
                       subregion to extract from UK radar data, of the form \
                       [min lon, max lon, min lat, max lat].

        Returns
        -------
        * **uk_radar_mean_cube** - an :class:`iris.cube.Cube` object holding \
                                   time-meaned UK radar precipitation rates, \
                                   with a meaning period derived from the input \
                                   time coordinate.
        """
        # Work out the period over which to compute time means
        mean_period = get_mean_period(time_coord)

        # The meaning period must be an integer multiple of an hour to use
        # UK radar hourly accumulations
        if mean_period % self.__frequency_in_hours != 0:
            msg = (
                "Meaning period must be an integer multiple of an hour "
                "to use UK radar data. Currently {0:f} hours".format(mean_period)
            )
            raise ValueError(msg)
        # Number of hourly periods in this meaning period
        num_uk_radar_periods = int(mean_period / self.__frequency_in_hours)

        # Names of UK radar data files...
        uk_radar_filename = "/".join([self.data_dir, self.filename])
        # ...and associated weights
        uk_radar_weights_filename = "/".join([self.data_dir, self.weights_filename])

        # Determine the start and end points of the desired time range
        time_unit = time_coord.units
        first_time = time_unit.num2date(
            np.min(time_coord.bounds) + self.__frequency_in_hours
        )
        last_time = time_unit.num2date(np.max(time_coord.bounds))
        # Load all required data
        uk_radar_cubes = iris.cube.CubeList()
        uk_radar_weights_cubes = iris.cube.CubeList()
        for time_loop in dateutil.rrule.rrule(
            dateutil.rrule.HOURLY,
            interval=1,
            dtstart=datetime.datetime.fromisoformat(first_time.isoformat()),
            until=datetime.datetime.fromisoformat(last_time.isoformat()),
        ):
            # Load hourly accumulation data
            uk_radar_file = insert_datetime(uk_radar_filename, time_loop)
            uk_radar_cube = iris.load_cube(uk_radar_file)
            # Adjust the time coordinate to be the midpoint of the hourly-mean
            # period, which is how times are typically represented in Iris
            shifted_time_coord = uk_radar_cube.coord("time").copy(
                points=(uk_radar_cube.coord("time").points - 0.5),
                bounds=uk_radar_cube.coord("time").bounds,
            )
            uk_radar_cube.replace_coord(shifted_time_coord)

            # Load corresponding accumulation weights
            uk_radar_weights_file = insert_datetime(
                uk_radar_weights_filename, time_loop
            )
            uk_radar_weights_cube = iris.load_cube(uk_radar_weights_file)
            # Adjust the time coordinate to be the midpoint of the hourly-mean
            # period, which is how times are represented in Iris
            shifted_time_coord = uk_radar_weights_cube.coord("time").copy(
                points=(uk_radar_weights_cube.coord("time").points - 0.5),
                bounds=uk_radar_weights_cube.coord("time").bounds,
            )
            uk_radar_weights_cube.replace_coord(shifted_time_coord)

            # TODO: Do we want to mask out values below self.__min_weight
            # for each hourly accumulation, rather than after they have been
            # combined to make an X-hourly mean as below?
            # For example, imagine if we are producing 6-hourly accumulations
            # and the weights are 12, 12, 12, 12, 12, 7. The average weight
            # over the 6 hour period is then 11.17 which exceeds
            # self.__min_weight=11. However, the last rainrate value was
            # clearly dodgy (weight=7) so we may want to mask out this pixel
            # despite having 5 good rainrate values (weight=12).
            # Mask out data where the accumulation weights are below the
            # acceptable threshold
            # uk_radar_cube.data = np.ma.masked_where(
            #    uk_radar_weights_cube.data < self.__min_weight,
            #    uk_radar_cube.data)

            # Remove all attributes from the radar cubes to avoid future merge problems.
            # See https://code.metoffice.gov.uk/trac/rmedtoolbox/ticket/152#comment:24
            uk_radar_cube.attributes = None
            uk_radar_weights_cube.attributes = None

            # Store data for this hour
            uk_radar_cubes.append(uk_radar_cube)
            uk_radar_weights_cubes.append(uk_radar_weights_cube)

        # Merge all hourly radar accumulations and accumulation weights
        # into single cubes
        uk_radar_cube = uk_radar_cubes.merge_cube()
        uk_radar_weights_cube = uk_radar_weights_cubes.merge_cube()

        # Check that the number of times in the cube is a multiple of
        # num_uk_radar_periods, otherwise we cannot compute the mean over
        # the desired period
        num_times = uk_radar_cube.coord("time").points.size
        if num_times % num_uk_radar_periods != 0:
            msg = "Cannot compute {0:.1f}-hour mean due to missing times".format(
                mean_period
            )
            raise ValueError(msg)

        # Convert units from mm*32 to mm
        uk_radar_cube.data = uk_radar_cube.data.astype(np.float64) / 32.0
        uk_radar_cube.units = "mm"

        # Now compute the mean over the desired meaning period using a
        # rolling window (in mm/h)
        uk_radar_mean_data = iris.util.rolling_window(
            uk_radar_cube.data,
            window=num_uk_radar_periods,
            step=num_uk_radar_periods,
            axis=0,
        )
        uk_radar_mean_data = np.sum(
            uk_radar_mean_data, axis=1, dtype=np.float64
        ) / float(mean_period)

        # Do the same for the accumulation weights
        uk_radar_mean_weights = iris.util.rolling_window(
            uk_radar_weights_cube.data,
            window=num_uk_radar_periods,
            step=num_uk_radar_periods,
            axis=0,
        )
        uk_radar_mean_weights = np.sum(
            uk_radar_mean_weights, axis=1, dtype=np.float64
        ) / float(mean_period)

        # Mask out data where the accumulation weights, averaged over the
        # desired meaning period, are below the threshold
        mask = uk_radar_mean_weights < self.__min_weight
        uk_radar_mean_data = np.ma.array(uk_radar_mean_data, mask=mask)

        # Create an Iris cube to hold the UK radar data meaned over the
        # desired period
        x_coord, y_coord = get_spatial_coords(uk_radar_cube)
        x_dim, y_dim = get_spatial_coord_dims(uk_radar_cube)
        cell_method = iris.coords.CellMethod(
            method="mean", coords="time", intervals="{0:.1f} hour".format(mean_period)
        )
        uk_radar_mean_cube = iris.cube.Cube(
            uk_radar_mean_data,
            standard_name=uk_radar_cube.standard_name,
            units="mm h-1",
            dim_coords_and_dims=[(time_coord, 0), (y_coord, y_dim), (x_coord, x_dim)],
            cell_methods=(cell_method,),
        )

        # bmc debugging
        print(" Nimrod metadata  standard_name ", uk_radar_cube.standard_name)
        debug_dim_coords_and_dims=[(time_coord, 0), (y_coord, y_dim), (x_coord, x_dim)]
        print(" Nimrod metadata  dim_coords_and_dims ", debug_dim_coords_and_dims)
        print(" Nimrod metadata  cell_methods ", (cell_method))

        # Regrid UK radar data from its native grid onto the specified grid
        if grid_cube is not None:
            # Check if regridding is actually required
            regrid_required = check_regrid_required(uk_radar_mean_cube, grid_cube)
            if regrid_required:
                # Do the regrid
                uk_radar_mean_cube = regrid_cube(
                    uk_radar_mean_cube, grid_cube, method=self.regrid_method
                )
            else:
                # If both the coordinate system and resolution of the UK
                # radar data cube and the desired grid are the same, no need
                # to do any regridding, just take a cutout of the radar data
                # cube instead
                xmin, xmax, ymin, ymax = get_spatial_extent(grid_cube)
                uk_radar_mean_cube = trim_cube(
                    uk_radar_mean_cube, xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax
                )

            # Use any mask associated with the grid cube to mask the UK
            # radar data
            if isinstance(grid_cube.data, np.ma.MaskedArray):
                mask = grid_cube.data.mask
                # Make a mask the same size as the UK radar data cube
                mask = iris.util.broadcast_to_shape(
                    mask, uk_radar_mean_cube.shape, [y_dim, x_dim]
                )
                if isinstance(uk_radar_mean_cube.data, np.ma.MaskedArray):
                    # If the UK radar data cube already has a mask, combine it
                    # with the mask from the grid cube
                    mask = np.ma.mask_or(mask, uk_radar_mean_cube.data.mask)
                    uk_radar_mean_cube.data.mask = mask
                else:
                    # Mask the UK radar data using the mask from the grid cube
                    uk_radar_mean_cube.data = np.ma.array(
                        uk_radar_mean_cube.data, mask=mask
                    )

        # If required, take a spatial cutout
        # This can be helpful otherwise we can end up with large cubes!
        if cutout is not None:
            xmin, xmax, ymin, ymax = cutout
            uk_radar_mean_cube = trim_cube(
                uk_radar_mean_cube, xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax
            )
        return uk_radar_mean_cube

    def get_file(self, file_path: str, output_dir: str) -> bool:
        """Save a file from the filesystem to the output directory."""
        return True


# fetch_nimrod(NimrodRetriever())
fetch_nimrod()
