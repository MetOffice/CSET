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

import iris
import os 
import datetime
import numpy as np
import pandas as pd
import collections
import errno
import matplotlib.pyplot as plt
import matplotlib.dates as dates
import matplotlib
from CSET.operators.diagnostics.constants import MAX_TICK_OVERRIDE, HOUR_IN_SECONDS
matplotlib.use('Agg')

def get_spatial_coords(cube):
    '''Returns the x, y coordinates of an input :class:`iris.cube.Cube`.'''
    # Usual names for spatial coordinates
    X_COORD_NAMES = ["longitude", "grid_longitude",
                     "projection_x_coordinate", "x"]
    Y_COORD_NAMES = ["latitude", "grid_latitude",
                     "projection_y_coordinate", "y"]

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
    '''
    Returns a list of the non-spatial coordinates of an input \
    :class:`iris.cube.Cube`.
    '''
    # Get a list of the cube coordinates
    coords = cube.coords()
    # Get the spatial coordinates of the cube
    x_coord, y_coord = get_spatial_coords(cube)
    # Remove the spatial coordinates from the list of coordinates
    coords.remove(x_coord)
    coords.remove(y_coord)
    return coords

def extract_overlapping(cubelist, coord_name):
    '''
    Extracts regions from cubes in a :class:`iris.cube.CubeList` such that \
    the specified coordinate is the same across all cubes.

    Arguments:

    * **cubelist** - an input :class:`iris.cube.CubeList`.
    * **coord_name** - a string specifying the name of the coordinate \
                       over which to perform the extraction.

    Returns a :class:`iris.cube.CubeList` where the coordinate corresponding \
    to coord_name is the same for all cubes.
    '''
    # Build a list of all Cell instances for this coordinate by
    # looping through all cubes in the supplied cubelist
    all_cells = []
    for cube in cubelist:
        for cell in cube.coord(coord_name).cells():
            all_cells.append(cell)

    # Work out which coordinate Cell instances are common across
    # all cubes in the cubelist...
    cell_counts = collections.Counter(all_cells)
    #unique_cells = cell_counts.keys()
    unique_cells = list(cell_counts.keys())
    unique_cell_counts = list(cell_counts.values())
    num_cubes = len(cubelist)
    common_cells = [unique_cells[i] for i, count in
                    enumerate(unique_cell_counts) if count==num_cubes]
    # ...and use these to subset the cubes in the cubelist
    constraint = iris.Constraint(
        coord_values={coord_name: lambda cell: cell in common_cells})
    
    cubelist = iris.cube.CubeList([cube.extract(constraint)
                                   for cube in cubelist])
    
    return cubelist

def remove_duplicates(cubelist):
    '''
    Removes any duplicate :class:`iris.cube.Cube` objects from an \
    :class:`iris.cube.CubeList`.
    '''
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
    cubelist = iris.cube.CubeList([cube for index, cube in
                                   enumerate(cubelist) if index
                                   not in indices_to_remove])
    return cubelist

def identify_unique_times(cubelist, time_coord_name):
    '''
    Given a :class:`iris.cube.CubeList`, this finds the set of unique times \
    which occur across all cubes in the cubelist.

    Arguments:

    * **cubelist** - a :class:`iris.cube.CubeList` of :class:`iris.cube.Cube` \
                     objects.
    * **time_coord_name** - the name of the time coordinate to select, \
                            typically "time", "forecast_period" or "hour".

    Returns:

    * **time_coord** - an :class:`iris.coords.Coord` instance containing the \
                       unique times that occur across the cubes in the \
                       input cubelist.
    '''
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

def hour_from_time(coord, point):
    '''
    Category function to calculate the hour given a time, for use in \
    :func:`iris.coord_categorisation.add_categorised_coord`.
    '''
    time = coord.units.num2date(point)
    day_start = datetime.datetime(time.year, time.month, time.day)
    seconds_since_day_start = (time - day_start).total_seconds()
    hours_since_day_start = (seconds_since_day_start
                             / float(HOUR_IN_SECONDS))
    return hours_since_day_start

def remove_cell_method(cube, cell_method):
    '''
    Removes the supplied :class:`iris.coords.CellMethod` from an input
    :class:`iris.cube.Cube`, then returns the cube.
    '''
    cell_methods = [cm for cm in cube.cell_methods if cm != cell_method]
    cube.cell_methods = ()
    for cm in cell_methods:
        cube.add_cell_method(cm)
    return cube

def aggregate_at_time(input_params):
    '''
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

    Returns:

    * **aggregated_cubes** - an :class:`iris.cube.CubeList` of \
                             :class:`iris.cube.Cube` objects holding the \
                             aggregated data.
    '''
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

    # Extract cubes matching the time specifed by the supplied time coordinate
    time_constraint = iris.Constraint(coord_values={time_coord_name:
                                                    lambda cell: cell.point in
                                                    time_coord.points})
    cubes_at_time = cubes.extract(time_constraint)

    # Add a temporary "number" coordinate to uniquely label the different
    # data points at this time.
    # An example of when there can be multiple data points at the time of
    # interest is if the time coordinate represents the hour of day.
    number = 0
    numbered_cubes = iris.cube.CubeList()
    for cube in cubes_at_time:
        for slc in cube.slices_over(time_coord_name):
            number_coord = iris.coords.AuxCoord(number, long_name='number')
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
        num_cases_coord = iris.coords.AuxCoord(num_cases, long_name='num_cases')
        cube.add_aux_coord(num_cases_coord)

        # Do aggregation across the temporary "number" coordinate
        if isinstance(aggregator, type(iris.analysis.PERCENTILE)):
            cube = cube.collapsed("number", aggregator, percent=percentile)
        else:
            cube = cube.collapsed("number", aggregator)

        # Now remove the "number" coordinate...
        cube.remove_coord("number")
        #...and associated cell method
        cell_method = iris.coords.CellMethod(aggregator.name(), coords="number")
        cube = remove_cell_method(cube, cell_method)

        aggregated_cubes.append(cube)

    return aggregated_cubes

def repeat_scalar_coord_along_dim_coord(cubelist, scalar_coord_name,
                                        dim_coord_name):
    '''
    For each :class:`iris.cube.Cube` in a given :class:`iris.cube.CubeList`, \
    this extends (by repetition) a specified scalar coordinate along the \
    dimension corresponding to a specified dimension coordinate.
    '''
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
                np.repeat(scalar_coord_val, dim_size),
                long_name=scalar_coord_name)
            
            # Add the new auxillary coordinate to the cube
            cube.add_aux_coord(scalar_coord, dim)

    return cubelist

def set_title_and_filename(group, time, short_name, threshold, grid_label):
    img_info = {}
    
    if group == "forecast_period":
        img_info["title"] = "T+{0:.1f}".format(time.points[0])
        img_info["filename"] = ("{0:s}{1:s}_thresh_{2:.1f}_T{3:.1f}"
                    .format(short_name,
                            grid_label, threshold,
                            time.points[0]))
    elif group == "time":
        time_unit = time.units
        datetime = time_unit.num2date(time.points[0])
        img_info["title"] = "{0:%Y/%m/%d} {1:%H%M}Z".format(datetime,
                                                datetime)
        img_info["filename"] = ("{0:s}{1:s}_thresh_{2:.1f}_"
                    "{3:%Y%m%d}_{4:%H%M}Z".format(
                short_name, grid_label,
                threshold, datetime, datetime))
    else:
        img_info["title"] = "{0:.1f}Z".format(time.points[0])
        img_info["filename"] = ("{0:s}{1:s}_thresh_{2:.1f}_{3:.1f}Z"
                    .format(short_name,
                            grid_label, threshold,
                            time.points[0]))
    
    return img_info

def get_valid_data(x, y, x_log=False, y_log=False):
    '''
    Returns the non-NaN elements of the input arrays. If the keyword log is \
    set, only non-NaN elements greater than zero are selected.
    '''
    # Check input
    if x is None or y is None:
        return None, None
    elif not isinstance(x, np.ndarray):
        raise ValueError("Input x must be a numpy array")
    elif not isinstance(y, np.ndarray):
        raise ValueError("Input y must be a numpy array")

    # Remove any NaNs from input x array
    # We use pandas.isnull instead of numpy.isnan here in case
    # arr contains datetime objects
    indices = np.where(~pd.isnull(x))
    x = x[indices]
    y = y[indices]
    if x_log:
        # only keep x values that are greater than zero
        indices = np.where(x>0)
        y = y[indices]
        x = x[indices]

    # Now do the same for y
    indices = np.where(~pd.isnull(y))
    y = y[indices]
    x = x[indices]
    if y_log:
        # Only keep y values that are greater than zero
        indices = np.where(y>0)
        y = y[indices]
        x = x[indices]

    # Return None if no valid data was extracted
    if x.size == 0 or y.size == 0:
        x = None
        y = None

    return x, y

def _mkdir_p(path):
    '''Makes a directory, mimicking mkdir -p behaviour.'''
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST:
            pass
        else: raise

def set_axis_limits(plot):
        '''
        #Guesses appropriate limits for the x and y axes using the coordinate \
        #values of each line in the :class:`LinePlot`. Nothing is done if x \
        #and y limits have been manually specifed.
        '''

        # First set up x-axis limits...
        if plot["x_limits"] is None:
            xmin, xmax = None, None
            x_log_possible = False
            for line in plot["lines"]:

                # Look for valid data to plot
                x, y = get_valid_data(
                    np.array(line["x"]), 
                    np.array(line["y"]),
                    x_log=plot["x_log"],
                    y_log=plot["y_log"]
                    )

                # If no data can be plotted, move on
                if x is None or y is None:
                    continue

                x_log_possible = True
                # This is useful to trim off lots of leading/trailing zeros
                # (e.g. for histograms with a wider range of bins than
                # necessary)
                x = x[np.nonzero(y)]

                # Update minimum x values
                if xmin is None or np.min(x) < xmin:
                    xmin = np.min(x)

                # Update maximum x values
                if xmax is None or np.max(x) > xmax:
                    xmax = np.max(x)

            # Turn off logarithmic x axis if it is not possible
            #if plot["x_log"] and not x_log_possible:
            #    plot["x_log"] = False

            if xmin == xmax:
                x_limits = None
            elif xmin is None or xmax is None:
                x_limits = None
            else:
                x_limits = (xmin, xmax)

            # Store the x axis limits
            plot["x_limits"] = x_limits

        # ...then set up y-axis limits
        if plot["y_limits"] is None:
            ymin, ymax = None, None
            y_log_possible = False
            for line in plot["lines"]:
                _, y = get_valid_data(
                    np.array(line["x"]), 
                    np.array(line["y"]),
                    x_log=plot["x_log"],
                    y_log=plot["y_log"]
                    )
                _, y_lower = get_valid_data(
                    np.array(line["x"]), 
                    plot["y_lower"],
                    x_log=plot["x_log"],
                    y_log=plot["y_log"]
                    )
                _, y_upper = get_valid_data(
                    np.array(line["x"]), 
                    plot["y_upper"],
                    x_log=plot["x_log"],
                    y_log=plot["y_log"]
                    )

                # If no data can be plotted, move on
                if y is None:
                    continue

                # Update minimum y values, using any lower bounds on y
                if y_lower is not None:
                    if ymin is None or np.min(y_lower) < ymin:
                        ymin = np.min(y_lower)
                else:
                    if ymin is None or np.min(y) < ymin:
                        ymin = np.min(y)

                # Update maximum y values, using any upper bounds on y
                if y_upper is not None:
                    if ymax is None or np.max(y_upper) > ymax:
                        ymax = np.max(y_upper)
                else:
                    if ymax is None or np.max(y) > ymax:
                        ymax = np.max(y)

            if ymin == ymax:
                y_limits = None
            elif ymin is None or ymax is None:
                y_limits = None
            else:
                y_limits = (ymin, ymax)

            # Store the y axis limits
            plot["y_limits"] = y_limits
            
        return plot

def plotfig(plot):
        '''
        Actually produce the :class:`LinePlot`. Returns an instance of \
        :class:`matplotlib.figure.Figure` for the plot, or None if no plot \
        was made.
        '''
        
        if len(plot["lines"]) == 0:
            #print("No lines to plot")
            return None
        
        # Open a new figure and set up axes
        fig, axes = plt.subplots()
        # Loop over lines on this plot
        for line in plot["lines"]:
            # Take a copy of the data for this line
            x = np.copy(line["x"])
            y = np.copy(line["y"]).astype(np.float64)

            if plot["x_log"]:
                x[np.where(x<=0)] = np.nan
            if plot["y_log"]:
                y[np.where(y<=0)] = np.nan

            axes.plot(
                x, 
                y, 
                linestyle=plot["linestyle"], 
                marker=plot["markers"],
                linewidth=plot["linewidth"], 
                color=line["colour"],
                label=line["label"]
                )         
        
        # set plot x and y axis limits
        #plot = set_axis_limits(plot)
        # Add user-specified text annotations
        
        if plot["annotations"] is not None:
            for annotation in plot["annotations"]:
                axes.annotate(annotation["text"],
                              xy=annotation["xy"],
                              xycoords="axes fraction",
                              fontsize=7
                              )
        
        # Set up Logarithmic axes if requested
        if plot["x_log"]:
            axes.set_xscale("log")
        if plot["y_log"]:
            axes.set_yscale("log")
        
        # Apply axis limits
        if plot["x_limits"] is not None:
            axes.set_xlim(plot["x_limits"])
        if plot["y_limits"] is not None:
            axes.set_ylim(plot["y_limits"])
        # Apply tick formatting
        x_is_time = True
        for line in plot["lines"]:
            if not all([isinstance(x, datetime.datetime) for x in line["x"]]):
                x_is_time = False
        
        if x_is_time:
            # Work out length of x-axis in days
            first_date, last_date = None, None
            for line in plot["lines"]:
                if first_date is None or np.min(line["x"]) < first_date:
                    first_date = np.min(line["x"])
                if last_date is None or np.max(line["x"]) > last_date:
                    last_date = np.max(line["x"])
            num_days = (last_date - first_date).days
            print('Number of days: ', num_days)
            # Set the spacing of ticks on the x-axis in such a way as to
            # prevent it becoming too crowded as the x-axis gets longer
            # (i.e. when analysing longer trials)
            x_tick_interval = (num_days / 10) + 1
            locator = dates.DayLocator(interval=int(x_tick_interval))
            
            locator.MAXTICKS = MAX_TICK_OVERRIDE
            axes.xaxis.set_major_locator(locator)
            axes.xaxis.set_major_formatter(dates.DateFormatter('%HZ\n%d/%m'))
            if x_tick_interval < 3:
                locator = dates.HourLocator(byhour=[0, 6, 12, 18])
            elif x_tick_interval < 6:
                locator = dates.HourLocator(byhour=[0, 12])
            else:
                locator = dates.DayLocator(interval=1)
            locator.MAXTICKS = MAX_TICK_OVERRIDE
            axes.xaxis.set_minor_locator(locator)
        
        # Add legend
        legend = axes.legend(loc='best')
        legend.draw_frame(False)
     
        # Add title and axis labels
        if plot["title"] is not None:
            axes.set_title(plot["title"])
        if plot["x_label"] is not None:
            axes.set_xlabel(plot["x_label"])
        if plot["y_label"] is not None:
            axes.set_ylabel(plot["y_label"])
    
        return fig

def save(plot, plotdir=None, db_file=None):
        '''
        Save the :class:`LinePlot` to a file.

        Keyword arguments:

        * **plotdir** - the name of the directory where the plot will be saved.
        * **db_file** - the name of the database file used to store image \
                        metadata for this plot.

        Returns:

        * The name of the file where the plot was saved.
        '''
        # Set a default plot directory if none given
        if plotdir is None:
            plotdir = "."
        
        # Remove any trailing slash
        if plotdir[-1] == "/":
            plotdir = plotdir[:-1]

        # Create plot directory if not present
        _mkdir_p(plotdir)

        # Generate a standard file name if none supplied
        if plot["filename"] is None:
            plot["filename"] = "lineplot"
        filename = "{0:s}/{1:s}.png".format(
            plotdir, 
            plot["filename"]
            )

        # Database file to store all image metadata in
        if db_file is None:
            db_file = "{0:s}/imt_db.db".format(plotdir)
       
        # Now save the figure using ImageMetaTag
        plt.savefig(filename)
        # Close the figure
        plt.close()

        return filename

def plot_and_save(input_params):

    '''
    Creates and saves a plot.

    Arguments (passed in as a tuple to allow parallelisation):

    * **input_params** - a two-element tuple consisting of:

      * **plot** - an instance of :class:`AreaAveragePlot`, \
                   :class:`HistogramPlot` or :class:`CellHistogramPlot` \
                   defining the plot to be made.
      * **plot_dir** - the name of the directory where the plot will be saved.

    Returns:

    * **db_file** - the name of the database file used to store image \
                    metadata for this plot, or None if no plot could be made.
    '''
    # Unpack input parameters tuple
    plot = input_params[0]
    plot_dir = input_params[1]
    # Produce the plot
    fig = plotfig(plot)

    if fig is None:
        db_file = None
    else:
        # Name of the database file to store all image metadata
        proc_id = os.getpid()
        db_file = "{0:s}/imt_tmp_db_{1:d}.db".format(plot_dir, proc_id)
        # Save the plot
        save(plot, plotdir=plot_dir, db_file=db_file)

def guess_bounds(cube):
    '''
    Takes an input :class:`iris.cube.Cube`, guesses bounds on the x, y \
    coordinates, then returns the cube. Such bounds are often required by \
    regridding algorithms.
    '''
    # Loop over spatial coordinates
    for axis in ["x", "y"]:
        coord = cube.coord(axis=axis)
        # Check that this is not a variable resolution grid
        # TODO: Does bounds really not work with variable resolution? AVD
        # seem to think it won't...
        try:
            _ = iris.util.regular_step(coord)
        except:
            raise ValueError("Cannot guess bounds for a variable "
                             "resolution grid")
        # Guess bounds if there aren't any
        if coord.bounds is None:
            coord.guess_bounds()
    return cube

def set_annotation(cubes):
    num_cases = []
    for cube in cubes:
        num_cases.extend(cube.coord("num_cases").points)
    num_cases = list(set(num_cases))
    if len(num_cases) != 1:
        annotation = None
    else:
        # Set up a text annotation showing the number of
        # cases that went into constructing histograms
        # at this time
        annotation = [
            {"text": "Number of cases: {:d}".format(
                    num_cases[0]),
                "xy": (0.0, 1.02)}
            ]
    return annotation

def set_general_axis_limits(plots):
    '''
    Guesses appropriate limits for the x and y axes using the extent \
    of each plot in the :class:`HistogramPlot`.

    Keyword arguments:

    * **plots** - only apply the axis limits to this subset of plots.
    '''
    # Set the axis limits for each plot
    for plot in plots:
        plot = set_axis_limits(plot)
    
    x_limits, y_limits = None, None
    
    # Work out the minimum/maximum x values based on all of the plots
    xmin, xmax = None, None
    for plot in plots:
        if plot["x_limits"] is not None:
            if xmin is None or np.min(plot["x_limits"]) < xmin:
                xmin = np.min(plot["x_limits"])
            if xmax is None or np.max(plot["x_limits"]) > xmax:
                xmax = np.max(plot["x_limits"])
    
    if xmin is None or xmax is None:
        x_limits = None
    else:
        x_limits = (xmin, xmax)

    # Work out the minimum/maximum y values based on all of the plots
    ymin, ymax = None, None
    for plot in plots:
        if plot["y_limits"] is not None:
            if ymin is None or np.min(plot["y_limits"]) < ymin:
                ymin = np.min(plot["y_limits"])
            if ymax is None or np.max(plot["y_limits"]) > ymax:
                ymax = np.max(plot["y_limits"])
    if ymin is None or ymax is None:
        y_limits = None
    else:
        y_limits = (ymin, ymax)

    # Now impose the same axis limits on all of the plots
    for plot in plots:
        plot["x_limits"] = x_limits
        plot["y_limits"] = y_limits

    return plots

  
