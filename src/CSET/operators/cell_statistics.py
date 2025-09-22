"""OMG YOU CAN'T COMMIT WITHOUT DOCSTRINGS, EVEN IN EXPLORATORY CODE."""

import datetime
import inspect
import itertools
from copy import deepcopy
from typing import Callable

import cftime
import iris.analysis
import iris.coords
import iris.cube
import iris.util
import numpy as np
from iris.cube import CubeList
from scipy import ndimage

M_IN_KM = 1000
HOUR_IN_SECONDS = 3600


# some things from the res job
#
# DATES="20200801T0600Z 20200801T1800Z 20200802T0600Z"
# LAND_SEA_SPLIT="False"
# NUM_PROC="8"
# INPUT_DIR="/data/scratch/byron.blay/RES_RETRIEVAL_CACHE/test_quick"
# PLOT_DIR="/data/users/byron.blay/RES/test_full/diags"
# RECIPE="generic_basic_qq_plot.yaml"
# SHORT_NAMES="ral2 ral3"
# SITE="metoffice"
# Y_AXIS="frequency"
# PLOT_PARAM="$CYLC_TASK_PARAM_cellplots"


# is this going to be the cli usage?
# export $INPUT_DIR=$SCRATCH/RES_RETRIEVAL_CACHE/test_quick
# export OUTPUT_DIR=$SCRATCH/temp/cset
# export RECIPE=cell_statistics.yaml
# cset -v bake --input-dir=$INPUT_DIR --output-dir=$OUTPUT_DIR --recipe=$RECIPE
#   --LAND_SEA_SPLIT=False


def var_filter(cubes, long_name=None, stash=None):
    result = []
    for cube in cubes:
        if long_name and cube.long_name == long_name:
            result.append(cube)
        elif stash and "STASH" in cube.attributes and cube.attributes["STASH"] == stash:
            result.append(cube)

    return iris.cube.CubeList(result)


def get_cell_stat_vars(cubes):
    vars = {}

    # Large-scale rainfall rate
    vars["rainfall rate"] = var_filter(
        cubes, long_name="surface_microphysical_rainfall_rate", stash="m01s04i203"
    )

    # 1-hourly mean precipitation rate
    vars["rainfall amount"] = var_filter(
        cubes, long_name="surface_microphysical_rainfall_amount", stash="m01s04i201"
    )
    # vars["1-hourly mean precipitation rate"].extend(var_filter(cubes, stash="m01s04i202"))  # snow
    # todo: RES has a switch for the following
    # vars["1-hourly mean precipitation rate"].extend(var_filter(cubes, stash="m01s05i201"))
    # vars["1-hourly mean precipitation rate"].extend(var_filter(cubes, stash="m01s05i202"))

    # ensure at least one cube found for each variable
    for k, v in vars.items():
        assert len(v) > 0, f"No cubes found for variable '{k}'"

    # # strictly one cube per variable?
    # assert len(vars["Large-scale rainfall rate"]) == 1
    # assert len(vars["1-hourly mean precipitation rate"]) == 1
    # vars["Large-scale rainfall rate"] = vars["Large-scale rainfall rate"][0]
    # vars["1-hourly mean precipitation rate"] = vars["1-hourly mean precipitation rate"][0]

    return vars


def get_bin_edges(cell_attribute):
    # todo: we probably want to let the user specify the bins
    if cell_attribute == "effective_radius_in_km":
        bin_edges = 10 ** (np.arange(0.0, 3.12, 0.12))
        bin_edges = np.insert(bin_edges, 0, 0)
    elif cell_attribute == "mean_value":
        bin_edges = 10 ** (np.arange(-1, 2.7, 0.12))
        bin_edges = np.insert(bin_edges, 0, 0)
    else:
        raise ValueError(f"Unknown cell attribute '{cell_attribute}'")

    return bin_edges


def identify_unique_times(cubelist, time_coord_name):
    """
    Given a :class:`iris.cube.CubeList`, this finds the set of unique times \
    which occur across all cubes in the cubelist.

    Arguments:

    * **cubelist** - a :class:`iris.cube.CubeList` of :class:`iris.cube.Cube` \
                     objects.
    * **time_coord_name** - the name of the time coordinate to select, \
                            typically "time", "forecast_period" or "hour".

    Returns
    -------
    * **time_coord** - an :class:`iris.coords.Coord` instance containing the \
                       unique times that occur across the cubes in the \
                       input cubelist.
    """
    times = []
    time_unit = None
    # Loop over cubes
    for cube in cubelist:
        # Extract the desired time coordinate from the cube
        time_coord = cube.coord(time_coord_name)

        # Get the units for the specifed time coordinate
        if time_unit is None:
            time_unit = time_coord.units

        # Store the time coordinate points
        times.extend(time_coord.points)

    # Construct a list of unique times...
    times = sorted(list(set(times)))
    # ...and store them in a new time coordinate
    time_coord = iris.coords.DimCoord(times, units=time_unit)
    time_coord.rename(time_coord_name)

    return time_coord


def add_categorised_coord(
    cube: iris.cube.Cube,
    name: str,
    from_coord: iris.coords.DimCoord | iris.coords.AuxCoord | str,
    category_function: Callable,
    units: str = "1",
) -> None:
    """Add a new coordinate to a cube, by categorising an existing one.

    Make a new :class:`iris.coords.AuxCoord` from mapped values, and add
    it to the cube.

    Parameters
    ----------
    cube :
        The cube containing 'from_coord'. The new coord will be added into it.
    name :
        Name of the created coordinate.
    from_coord :
        Coordinate in 'cube', or the name of one.
    category_function :
        Function(coordinate, value), returning a category value for a coordinate
        point-value. If ``value`` has a type hint :obj:`cftime.datetime`, the
        coordinate points are translated to :obj:`cftime.datetime` s before
        calling ``category_function``.
    units :
        Units of the category value, typically 'no_unit' or '1'.
    """
    # Interpret coord, if given as a name
    coord = cube.coord(from_coord) if isinstance(from_coord, str) else from_coord

    if len(cube.coords(name)) > 0:
        msg = 'A coordinate "%s" already exists in the cube.' % name
        raise ValueError(msg)

    # Translate the coordinate points to cftime datetimes if requested.
    value_param = list(inspect.signature(category_function).parameters.values())[1]
    if issubclass(value_param.annotation, cftime.datetime):
        points = coord.units.num2date(coord.points, only_use_cftime_datetimes=True)
    else:
        points = coord.points

    # Construct new coordinate by mapping values, using numpy.vectorize to
    # support multi-dimensional coords.
    # Test whether the result contains strings. If it does we must manually
    # force the dtype because of a numpy bug (see numpy #3270 on GitHub).
    result = category_function(coord, points.ravel()[0])
    if isinstance(result, str):
        str_vectorised_fn = np.vectorize(category_function, otypes=[object])

        def vectorised_fn(*args):
            # Use a common type for string arrays (N.B. limited to 64 chars).
            return str_vectorised_fn(*args).astype("|U64")

    else:
        vectorised_fn = np.vectorize(category_function)
    new_coord = iris.coords.AuxCoord(
        vectorised_fn(coord, points),
        units=units,
        attributes=coord.attributes.copy(),
    )
    new_coord.rename(name)

    # Add into the cube
    cube.add_aux_coord(new_coord, cube.coord_dims(coord))


def hour_from_time(coord, point):
    """
    Category function to calculate the hour given a time, for use in \
    :func:`iris.coord_categorisation.add_categorised_coord`.
    """
    time = coord.units.num2date(point)
    day_start = datetime.datetime(time.year, time.month, time.day)
    seconds_since_day_start = (time - day_start).total_seconds()
    hours_since_day_start = seconds_since_day_start / float(HOUR_IN_SECONDS)
    return hours_since_day_start


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


def extract_unique(cubes, group):
    # Preparation of data for averaging and plotting
    if group == "time":
        # Identify a unique set of times
        times = identify_unique_times(cubes, group)

        # Now extract data at these times
        time_constraint = iris.Constraint(
            coord_values={group: lambda cell: cell.point in times.points}
        )
        cubes = cubes.extract(time_constraint)

        # Remove other time coordinates to allow a cube merge
        # later
        for cube in cubes:
            cube.remove_coord("forecast_reference_time")
            cube.remove_coord("forecast_period")
    elif group == "forecast_period":
        # Identify a unique set of lead times
        times = identify_unique_times(cubes, group)

        # Remove other time coordinates to allow a cube
        # merge later
        for cube in cubes:
            cube.remove_coord("forecast_reference_time")
            cube.remove_coord("time")
    elif group == "hour":
        # Categorise the time coordinate of each cube into
        # hours
        for cube in cubes:
            add_categorised_coord(
                cube, "hour", cube.coord("time"), hour_from_time, units="hour"
            )

        # Identify a unique set of times of day
        times = identify_unique_times(cubes, group)

        # Now extract data at these times
        time_constraint = iris.Constraint(
            coord_values={group: lambda cell: cell.point in times.points}
        )
        cubes = cubes.extract(time_constraint)

        # Remove other time coordinates to allow a cube
        # merge later
        for cube in cubes:
            cube.remove_coord("forecast_reference_time")
            cube.remove_coord("time")
            cube.remove_coord("forecast_period")

    # Remove any duplicate cubes to allow a successful merge
    # Note this is typcially because we have the same set of
    # observations associated with more than one model
    cubes = remove_duplicates(cubes)

    return cubes, times


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


def aggregate_at_time(input_params):
    """
    Extracts data valid at a given time from each cube in a list of cubes, \
    then performs an aggregation operation (e.g. mean) across this data.

    Arguments (passed in as a tuple to allow parallelisation):

    * **input_params** - a four-element tuple consisting of:

      * **cubes** - a :class:`iris.cube.CubeList` holding the \
                    :class:`iris.cube.Cube` objects to process.
      * **time_coord** - the time at which the aggregation should be performed, \
                         supplied as an :class:`iris.coords.Coord` object.
      * **aggregator** - the aggregator to use, which can be any from \
                         :mod:`iris.analysis`.
      * **percentile** - the value of the percentile rank at which to extract \
                         values, if the chosen aggregator is \
                         :class:`iris.analysis.PERCENTILE`. For other \
                         aggregators this not used.

    Returns
    -------
    * **aggregated_cubes** - an :class:`iris.cube.CubeList` of \
                             :class:`iris.cube.Cube` objects holding the \
                             aggregated data.
    """
    # Unpack input parameters tuple
    cubes = input_params[0]
    time_coord = input_params[1]
    aggregator = input_params[2]
    # TODO: Can we improve the handling of this with keyword arguments?
    percentile = input_params[3]

    # Check the supplied time coordinate to make sure it corresponds to a
    # single time only
    if len(time_coord.points) != 1:
        raise ValueError("Time coordinate should specify a single time only")

    # Remove any duplicate cubes in the input cubelist otherwise this
    # will break the aggregation
    cubes = remove_duplicates(cubes)

    # Name of the supplied time coordinate
    time_coord_name = time_coord.name()

    # Extract cubes matching the time specified by the supplied time coordinate.
    # Even though the source coord might have floats for its points,
    # the cell here will have cftime objects, such as DatetimeGregorian,
    # so we can't just compare against the time coord's points.
    time_constraint = iris.Constraint(
        coord_values={time_coord_name: lambda cell: cell.point in time_coord.cells()}
    )
    cubes_at_time = cubes.extract(time_constraint)

    # Add a temporary "number" coordinate to uniquely label the different
    # data points at this time.
    # An example of when there can be multiple data points at the time of
    # interest is if the time coordinate represents the hour of day.
    number = 0
    numbered_cubes = iris.cube.CubeList()
    for cube in cubes_at_time:
        for slc in cube.slices_over(time_coord_name):
            number_coord = iris.coords.AuxCoord(number, long_name="number")
            slc.add_aux_coord(number_coord)
            numbered_cubes.append(slc)
            number += 1
    cubes_at_time = numbered_cubes

    # Merge
    cubes_at_time = cubes_at_time.merge()

    # For each cube in the cubelist, aggregate over all cases at this time
    # using the supplied aggregator
    aggregated_cubes = iris.cube.CubeList()
    for cube in cubes_at_time:
        # If there was only a single data point at this time, then "number"
        # will be a scalar coordinate. If so, make it a dimension coordinate
        # to allow collapsing below
        if not cube.coord_dims("number"):
            cube = iris.util.new_axis(cube, scalar_coord="number")

        # Store the total number of data points found at this time
        num_cases = cube.coord("number").points.size
        num_cases_coord = iris.coords.AuxCoord(num_cases, long_name="num_cases")
        cube.add_aux_coord(num_cases_coord)

        # Do aggregation across the temporary "number" coordinate
        if isinstance(aggregator, type(iris.analysis.PERCENTILE)):
            cube = cube.collapsed("number", aggregator, percent=percentile)
        else:
            cube = cube.collapsed("number", aggregator)

        # Now remove the "number" coordinate...
        cube.remove_coord("number")
        # ...and associated cell method
        cell_method = iris.coords.CellMethod(aggregator.name(), coords="number")
        cube = remove_cell_method(cube, cell_method)

        aggregated_cubes.append(cube)

    return aggregated_cubes


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


def caller_thing(cubes: CubeList, cell_attribute: str, time_grouping: str):
    """
    Create a histogram from each given cube, for every threshold and cell attribute.

    The cube will be "1-hourly mean precipitation rate" or "Large-scale rainfall rate".

    Arguments
    ---------
    cubes: iris.cube.CubeList
        Cube(s) to filter. Will be "1-hourly mean precipitation rate" or "Large-scale rainfall rate".
        Assumed to be one cube per model, with the first being the control.
    cell_attribute: str
        "effective_radius_in_km" or "mean_value"
    time_grouping: str
        "forecast_period", "hour" or "time"

    """
    if not isinstance(cubes, CubeList):
        cubes = CubeList([cubes])

    # For now, thresholds are hard coded.
    thresholds = [0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0, 128.0]

    # Get a list of the common forecast periods and hours
    # todo: For forecast time, this must contain "all", plus all the T+0.5 .. T+71.5
    # todo: For hourly, this must contain "all", plus all the 0.5Z .. 23.5Z
    forecast_periods = set(cubes[0].coord("forecast_period").points)
    hours = set(cubes[0].coord("time").points)  # todo: check it's actually hourly?
    for cube in cubes[1:]:
        forecast_periods.intersection_update(set(cube.coord("forecast_period").points))
        hours.intersection_update(set(cube.coord("time").points))

    # todo: we need a land-sea split input?
    # for now, hard-code as false (this is what the res output had it set to)
    land_sea_split = False

    # what about obs? GPM & UK_RADAR_2KM? ignore for now.

    # different bins for the two cell attributes
    # bin_edges = {}
    #
    # bin_edges['effective_radius_in_km'] = 10**(np.arange(0.0, 3.12, 0.12))
    # bin_edges['effective_radius_in_km'] = np.insert(bin_edges['effective_radius_in_km'], 0, 0)
    #
    # bin_edges['mean_value'] = 10**(np.arange(-1, 2.7, 0.12))
    # bin_edges['mean_value'] = np.insert(bin_edges['mean_value'], 0, 0)

    # model_histograms = {}
    for cube in cubes:
        for threshold in thresholds:
            # todo: check var_name has been removed by this point, as RES removed it to help with merge
            hist_cubes = something_like_cell_attribute_histogram(
                cube,
                attribute=cell_attribute,
                bin_edges=get_bin_edges(cell_attribute),
                threshold=threshold,
            )

            # todo: res does a deep copy at this point for some reason - seems uneceeary? double check.

            # todo: RES calls this here, but we get a cube, not a cubelist so we can't.
            # RES used it's own version because Iris' was slow at the time. todo: is it fast now?
            # hist_cubes = cube_utils.extract_overlapping(cubes_group, "forecast_period")
            hist_cubes = hist_cubes.extract_overlapping("forecast_period")

            # Now we take the cell statistics and aggregate by "time_grouping".

            # We should deep copy the cubes here becuase there is cube wrangling below,
            # and it's possible that we'll be using the same cubes across iterations in this loop.
            # (as extract doesn't always create a new cube).
            hist_cubes = deepcopy(hist_cubes)

            # Res comment for this bit is: preparation of data for averaging and plotting
            hist_cubes, times = extract_unique(hist_cubes, time_grouping)

            # Sum cell statistic histograms at each time in parallel
            input_params = [
                (hist_cubes, time, iris.analysis.SUM, None) for time in times
            ]
            result_list = [
                aggregate_at_time(input_param) for input_param in input_params
            ]
            cubes_group = iris.cube.CubeList(itertools.chain.from_iterable(result_list))
            cubes_group = cubes_group.merge()

            # If the number of cases at each time is the same, the
            # above merge results in a scalar coordinate representing
            # the number of cases. Replace this scalar coordinate with
            # an auxillary coordinate that has the same length as the
            # time coordinate
            cubes_group = repeat_scalar_coord_along_dim_coord(
                cubes_group, "num_cases", time_grouping
            )

            # At this point, RES extracts every time point into a separate cube list and plots it.
            for time in times:
                # Extract histogram at this time
                time_constraint = iris.Constraint(
                    coord_values={time_grouping: lambda cell: cell.point in time.points}
                )
                cubes_at_time = cubes_group.extract(time_constraint)

                # todo: RES creates a plot title here.
                # Perhaps we should add a plot title attribute to each cube here?
                if time_grouping == "forecast_time":
                    title = "T+{0:.1f}".format(time.points[0])
                elif time_grouping == "hour":
                    title = "{0:.1f}Z".format(time.points[0])
                elif time_grouping == "time":
                    time_unit = time.units
                    datetime = time_unit.num2date(time.points[0])
                    title = "{0:%Y/%m/%d} {1:%H%M}Z".format(datetime, datetime)

                # todo: RES has some analysis of the number of cases used to construct the histogram at this point.

                # todo: RES plots each cube here.
                for cube in cubes_at_time:
                    # todo: Normalise histogram?
                    # if y_axis == "relative_frequency":
                    #     cube.data = ((100.0 * cube.data) / np.sum(cube.data, dtype=np.float64))

                    print(f'adding "{title}" plot for "{cube.name()}"')

            # Sum all histograms. This creates the data for the "all" time point.
            for cube in cubes_group:
                cube = cube.collapsed(time_grouping, iris.analysis.SUM)

                # todo: Normalise histogram?
                # if y_axis == "relative_frequency":
                #     cube.data = ((100.0 * cube.data) / np.sum(cube.data, dtype=np.float64))

                print(f'adding "all" plot for collapsed "{cube.name()}"')

    # return cubes to plot. todo: in what exact arrangement?
    return None


def something_like_cell_attribute_histogram(cube, attribute, bin_edges, threshold=0.0):
    # Express histogram bins as an Iris coordinate
    bin_centres = 0.5 * (bin_edges[1:] + bin_edges[:-1])
    bins_as_coord = iris.coords.DimCoord(
        bin_centres,
        long_name=attribute,
        units=cube.units,
        coord_system=None,
        bounds=np.column_stack((bin_edges[0:-1], bin_edges[1:])),
    )

    data_min, data_max = None, None
    hist_cubes = iris.cube.CubeList()
    coords = get_non_spatial_coords(cube)

    for slc in cube.slices_over(coords):
        # Identify connected cells in this spatial slice
        cells = find_cells(slc, threshold=threshold)

        if cells:
            # Extract values of the desired cell attribute
            cell_attributes = [cell.attributes[attribute] for cell in cells]

            # Store the minimum/maximum values of the cell attribute
            if data_min is None or np.min(cell_attributes) < data_min:
                data_min = np.min(cell_attributes)
            if data_max is None or np.max(cell_attributes) > data_max:
                data_max = np.max(cell_attributes)

            # Construct a histogram of the desired cell attribute
            hist, _ = np.histogram(cell_attributes, bin_edges)
        else:
            # Assign zeros to all bins
            hist = np.zeros(bin_centres.size).astype(np.int64)

        # Get a list of the non-spatial coordinates for this slice
        aux_coords = [(coord, []) for coord in get_non_spatial_coords(slc)]

        # Construct a cube to hold the cell statistic histogram for this slice
        hist_slc = iris.cube.Cube(
            hist,
            long_name=("{0:s} cell {1:s} histogram".format(slc.name(), attribute)),
            units="no_unit",
            attributes=slc.attributes,
            cell_methods=slc.cell_methods,
            dim_coords_and_dims=[(bins_as_coord, 0)],
            aux_coords_and_dims=aux_coords,
        )

        hist_cubes.append(hist_slc)

    hist_cube = hist_cubes.merge_cube()
    return hist_cube


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


def connected_object_labelling(data, threshold=0.0, min_size=1, connectivity=1):
    """
    Finds connected objects in an input array and assigns them unique labels.

    Arguments:

    * **data** - a :class:`numpy.ndarray` array in which to label objects.

    Keyword arguments:

    * **threshold** - if supplied, only regions where the input data exceeds \
                      the threshold will be considered when searching for \
                      connected objects.
    * **min_size** - minimum size in grids points for connected objects. Must \
                     be an integer >= 1.
    * **connectivity** - given a particular grid point, all grid points up to \
                         a squared distance of connectivity away are considered \
                         neighbours. Connectivity may range from 1 (only direct \
                         neighbours are considered) to :attr:`data.ndim`.

    Returns
    -------
    * **label_array** - an integer array where each unique object in the input \
                        array has a unique label in the returned array.
    * **num_objects** - the number of objects found.
    """
    # Apply the supplied threshold to the data to generate a binary array
    binary_data = data.copy()
    if np.ma.is_masked(binary_data):
        # If the data is masked, replace any masked values with (threshold - 1)
        # thus guaranteeing they will be below the threshold and thus set to 0
        # below
        binary_data = np.ma.filled(binary_data, fill_value=(threshold - 1))
    # Set values above and below the threshold to 1 and 0, respectively
    indices_above = binary_data > threshold
    indices_below = binary_data <= threshold
    binary_data[indices_above] = 1
    binary_data[indices_below] = 0

    # Construct a structuring element that defines how the neighbours of
    # a grid point are assigned
    structure_element = ndimage.morphology.generate_binary_structure(
        data.ndim, connectivity
    )

    # Label distinct (connected) objects in the binary array
    label_array, num_objects = ndimage.measurements.label(
        binary_data, structure=structure_element
    )

    # Throw away any objects smaller than min_size
    if min_size < 1:
        raise ValueError('"min_size" must be 1 or greater')
    elif min_size > 1:
        labels = np.unique(label_array)
        # Discard the background (which will be labelled as 0)
        labels = labels[(labels > 0)]
        # Loop over distinct objects
        for label in labels:
            # Find the indices of the grid points comprising this object
            indices = np.where(label_array == label)
            # If this object is smaller than min_size, set it as background
            if indices[0].size < min_size:
                label_array[indices] = 0
                num_objects -= 1

    return label_array, num_objects


def find_cells(cube, threshold=0.0, area_threshold=0.0, connectivity=1):
    """
    Finds connected objects (i.e. cells) in spatial slices of a given \
    :class:`iris.cube.Cube`.

    Arguments:

    * **cube** - an input :class:`iris.cube.Cube` object.

    Keyword arguments:

    * **threshold** - if supplied, only regions where the input data exceeds \
                      the threshold will be considered when identifying cells.
    * **area_threshold** - minimum area in km^2 that cells must have.
    * **connectivity** - given a particular grid point, all grid points up to a \
                         squared distance of connectivity away are considered \
                         neighbours. Connectivity may range from 1 (only \
                         direct neighbours are considered) to \
                         :attr:`cube.data.ndim`.

    Returns
    -------
    * **cells** - a :class:`iris.cube.CubeList` of \
                  :class:`iris.cube.Cube` objects, each one corresponding to \
                  an identified cell.
    """
    # Convert input area threshold from km^2 to m^2
    area_threshold = (float(M_IN_KM) ** 2) * area_threshold

    # Get x, y coordinates of input cube
    x_coord, y_coord = get_spatial_coords(cube)
    x, y = iris.analysis.cartography.get_xy_grids(cube)

    # Guess x, y coordinate bounds
    cube = guess_bounds(cube)

    # Loop over 2D spatial slices of the input cube and find cells in each
    # slice
    grid_areas = None
    cells = iris.cube.CubeList()
    coords = get_non_spatial_coords(cube)
    for slc in cube.slices_over(coords):
        if grid_areas is None:
            # Area of grid cells, in m^2
            grid_areas = iris.analysis.cartography.area_weights(slc)

        # Store a list of the non-spatial coordinates for this slice
        aux_coords = [(coord, []) for coord in get_non_spatial_coords(slc)]

        # Find and label cells
        # Call connected object labelling function based on
        # scipy.ndimage.measurements.label
        cell_label_array, _ = connected_object_labelling(
            slc.data, threshold=threshold, min_size=1, connectivity=connectivity
        )

        # Get a list of unique cell labels
        cell_labels = np.unique(cell_label_array)
        # Discard background (which has a label of 0)
        cell_labels = cell_labels[(cell_labels > 0)]
        # Loop over cell and store their properties
        for cell_label in cell_labels:
            # Find the indices of the grid points comprising this cell
            cell_indices = np.where(cell_label_array == cell_label)
            cell_x = x[cell_indices]
            cell_y = y[cell_indices]
            cell_values = slc.data[cell_indices]
            cell_grid_areas = grid_areas[cell_indices]

            # There should not be any masked data present in cells!
            if np.ma.is_masked(cell_values):
                raise ValueError("Masked data found in cell {0:d}".format(cell_label))

            # If cell area is less than area_threshold, discard it
            # (by setting its label to the background value)
            cell_area = np.sum(cell_grid_areas, dtype=np.float64)
            if cell_area < area_threshold:
                cell_label_array[cell_indices] = 0
                continue

            # Estimate cell centre position
            # TODO Is there a better way of doing this? C.O.M?
            cell_centre = (
                np.mean(cell_x, dtype=np.float64),
                np.mean(cell_y, dtype=np.float64),
            )
            # Area-weighted mean value in cell
            cell_mean = (
                np.sum((cell_grid_areas * cell_values), dtype=np.float64) / cell_area
            )
            # Convert cell area from m^2 to km^2...
            cell_area /= float(M_IN_KM) ** 2
            # ...and then cell effective radius in km
            cell_radius = np.sqrt(cell_area / np.pi)

            # Create an Iris cube to store this cell
            cell_cube = iris.cube.Cube(
                cell_values,
                long_name="{:s} cell".format(cube.name()),
                units=cube.units,
                attributes=cube.attributes,
                cell_methods=cube.cell_methods,
                aux_coords_and_dims=aux_coords,
            )

            # Set up x, y coordinates describing the grid points in the cell...
            cell_x_coord = iris.coords.AuxCoord(
                cell_x,
                standard_name=x_coord.standard_name,
                long_name=x_coord.long_name,
                units=x_coord.units,
                bounds=None,
                attributes=x_coord.attributes,
                coord_system=x_coord.coord_system,
            )
            cell_y_coord = iris.coords.AuxCoord(
                cell_y,
                standard_name=y_coord.standard_name,
                long_name=y_coord.long_name,
                units=y_coord.units,
                bounds=None,
                attributes=y_coord.attributes,
                coord_system=y_coord.coord_system,
            )
            # ...and add them to the cell cube
            cell_cube.add_aux_coord(cell_x_coord, 0)
            cell_cube.add_aux_coord(cell_y_coord, 0)

            # Set up a coordinate describing the areas of grid cells in
            # the cell object...
            cell_grid_area_coord = iris.coords.AuxCoord(
                cell_grid_areas, long_name="grid_areas", units="m2"
            )
            # ...and add it to the cell cube
            cell_cube.add_aux_coord(cell_grid_area_coord, 0)

            # Finally add some attriubtes to the cube that describe some
            # useful information about the cell
            # cell_cube.attributes["label"] = int(cell_label)
            cell_cube.attributes["centre"] = cell_centre
            cell_cube.attributes["area_in_km2"] = cell_area
            cell_cube.attributes["effective_radius_in_km"] = cell_radius
            cell_cube.attributes["mean_value"] = cell_mean
            # cell_cube.attributes["indices"] = cell_indices
            cells.append(cell_cube)

    return cells


# ignore

# def cell_statistics(LAND_SEA_SPLIT: bool):


# cell_attribute:
#   effective_radius_in_km
#   mean_value


# RAIN_RATE = diagnostics.Field(
#     long_name="Large-scale rainfall rate",
#     short_name="rain_rate",
#     stash=[diagnostics.STASHRequest(iris.fileformats.pp.STASH(1, 4, 203))],
#     units="mm h-1",
#     unit_conversion_factor=3600.0,
#     thresholds=[0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0, 128.0] if USE_LFRIC_CODE else None,
#     regrid_method="two_stage"
#     )


# PRECIP_1HR_MEAN = diagnostics.Field(
#     long_name="1-hourly mean precipitation rate",
#     short_name="1hr_mean_precip",
#     stash=PRECIP_1HR_MEAN_STASH,
#     stash_operator=diagnostics.STASH_OPERATORS["ADD"],
#     mean_period=1,
#     use_running_accumulations=not USE_LFRIC_CODE,
#     units="mm h-1",
#     observations=["GPM", "UK_radar_2km", "Darwin_radar_rain_2.5km"],
#     thresholds=[0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0, 128.0],
#     regrid_method="two_stage"
#     )

# PRECIP_1HR_MEAN_STASH = [
#         diagnostics.STASHRequest(iris.fileformats.pp.STASH(1, 4, 201)),
#         diagnostics.STASHRequest(iris.fileformats.pp.STASH(1, 4, 202))]
# if not USE_LFRIC_CODE:
#     PRECIP_1HR_MEAN_STASH.extend([
#         diagnostics.STASHRequest(iris.fileformats.pp.STASH(1, 5, 201), is_optional=True),
#         diagnostics.STASHRequest(iris.fileformats.pp.STASH(1, 5, 202), is_optional=True),
#     ])


# choose the thresholds according to the variable
# todo: should these be [optionally] parameterised?


# make a cube list of cell_attribute_histogram() for each cube


# return for plotting
# return some_cube


"""

category: Diagnostics
title: cell statistics plot
description: |
  TBD.

steps:

  - operator: cell_statistics.caller_thing

    # "effective_radius_in_km" or "mean_value"
    cell_attribute: $CELL_ATTRIBUTE

    uk_ctrl_um:
      operator: read.read_cubes
      file_paths:
        - "/data/scratch/byron.blay/RES_RETRIEVAL_CACHE/test_lfric/20240121T0000Z/uk_ctrl_um/20240121T0000Z_UK_672x672_1km_RAL3P3_pdiagb000.pp"
        - "/data/scratch/byron.blay/RES_RETRIEVAL_CACHE/test_lfric/20240121T0000Z/uk_ctrl_um/20240121T0000Z_UK_672x672_1km_RAL3P3_pdiagb012.pp"
    uk_expt_lfric:
      operator: read.read_cubes
      file_paths:
        - "/data/scratch/byron.blay/RES_RETRIEVAL_CACHE/test_lfric/20240121T0000Z/uk_expt_lfric/20240121T0000Z_UK_672x672_1km_RAL3P3_lfric_slam_timeproc_000_006.nc"
        - "/data/scratch/byron.blay/RES_RETRIEVAL_CACHE/test_lfric/20240121T0000Z/uk_expt_lfric/20240121T0000Z_UK_672x672_1km_RAL3P3_lfric_slam_timeproc_006_012.nc"

  - operator: write.write_cube_to_nc
    overwrite: True

  - operator: plot.plot_histogram_series

"""
