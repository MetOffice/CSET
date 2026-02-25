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

"""Operators to perform cell statistics diagnostics."""

import iris
import iris.analysis
import numpy as np
import itertools
import warnings
import glob
import copy
import iris.coord_categorisation as coord_cat
import dask
import dask.bag as db
from CSET.operators.diagnostics.diag_utils import compute_cell_stats
from CSET.operators.diagnostics.constants import COLOURS
import CSET.operators.diagnostics.config as config
import CSET.operators.diagnostics.utils as utils
import pickle
warnings.filterwarnings("ignore")
iris.FUTURE.datum_support = True

def cell_statistics(cubelist, input_params_dict):
        
    '''
    Produces histogram plots objects of cell statistics.

    For each cell statistic plot defined in :mod:`config.PLOTS`, the \
    necessary model (and possibly observational) data is read in from the \
    netCDF file regridded_cubes.nc in each model data directory. It is \
    assumed :func:`regrid.regrid` will have been run previously to create \
    this file. The netCDF file will contain the model fields (and any \
    corresponding gridded observations) required for each cell statistic \
    plot, on one or more common spatial grids. All of the data is read in, \
    a threshold is applied if required, then cells are identified and \
    histograms of the desired cell attribute (e.g. cell size, cell mean \
    value) are constructed.

    Given a particular spatial grid, a set of times is identified for which \
    there is matching data from all of the various model and observational \
    datasets available. The times will be either lead times, validity times \
    or hour of day, depending on how the parameter time_grouping is set.

    At each time, all of the cell statistic histograms valid at that time \
    for a particular model or observational dataset are summed to derive a \
    total histogram. This is repeated for all models and observational \
    datasets. A plot of the total histograms at that time is made and saved. \
    Similar cell statistic histogram plots are produced at all the other times.

    In addition, an overall plot is produced which displays cell statistic \
    histograms for each model and observational dataset constructed by \
    summing histograms across all times.

    The process is then repeated for all spatial grids and threshold values.

    Arguments
    _________

    cubelist 
        Cublist contains the regridded cubes of all models and cycles.
    input_params_dict
        input parameters dictionary contains following keys:
        Threshols: list containing range of threshols
        time_grouping: list contains time groups i.e. forecast_perios, time, hour
        cell_attribute: string, can be either "effective_radius_in_km" or "mean_value"
        plot_dir: string, output dir to save pickle file containing plot objects
    '''

    thresholds = input_params_dict["thresholds"]
    time_grouping = input_params_dict["time_grouping"]
    plot_dir = input_params_dict["plot_dir"]
    cell_attribute = input_params_dict["cell_attribute"]
    
    if cubelist == None:
        raise Exception("Cublist is empty")

    if cell_attribute == "effective_radius_in_km":
        bin_edges = 10**(np.arange(0.0, 3.12, 0.12))
    elif cell_attribute == "mean_value":
        bin_edges = 10**(np.arange(0.0, 3.12, 0.12))
    else: 
        raise Exception("Cell attribute is not correct")
        
    bin_edges = np.insert(bin_edges, 0, 0)
        
    # Set up y-axis label
    if config.y_axis == "frequency":
        y_label = "Frequency"
    elif config.y_axis == "relative_frequency":
        y_label = "Relative frequency [%]"
    else:
        y_label = None

    if time_grouping is None:
        time_grouping = ["forecast_period", "time", "hour"]
        
    colours = {}

    for threshold in thresholds:
        print('Threshold: {}'.format(threshold))

        lcube = compute_cell_stats(
            cubelist, 
            threshold, 
            bin_edges, 
            cell_attribute
            )
        
        all_cubes = iris.cube.CubeList(
                lcube
                )
        
        # Work out what models/observations we have and assign colours
        # to them
        labels = list(set([cube.attributes["data_source"] for
                            cube in all_cubes]))
        for icol, label in enumerate(labels):
            if label not in colours:
                colours[label] = COLOURS["brewer_paired"][icol]

        # Get a list of all grid details...
        grids = [(cube.attributes["grid_spacing"],
                  cube.attributes["observations"]) for cube in all_cubes]
        # ...and extract the unique ones
        grids = list(set(grids))
       
        # Loop over grids
        for (grid_spacing, observations) in grids:
            print("=> Grid: {0:s}, {1:s}".format(observations, grid_spacing))
            if observations == "None":
                grid_label = ""
            else:
                grid_label = "_{0:s}".format(observations)

            # Get cubes on this grid
            constraint = (
                iris.AttributeConstraint(grid_spacing=grid_spacing)
                & iris.AttributeConstraint(observations=observations))
            cubes = all_cubes.extract(constraint)

            
            # Loop over different choices for how data is grouped by time
            for group in time_grouping:
                print("     Time grouping: {0:s}...".format(group))
                # Take a copy of the cubes on this grid
                cubes_group = copy.deepcopy(cubes)

                cubes_group = utils.extract_overlapping(
                    cubes_group, 
                    "forecast_period"
                    )
                
                # Preparation of data for averaging and plotting
                if group == "time":
                    # Identify a unique set of times
                    times = utils.identify_unique_times(cubes_group, group)

                    # Now extract data at these times
                    time_constraint = iris.Constraint(
                        coord_values={group: lambda cell: cell.point in
                                        times.points}
                                        )
                    cubes_group = cubes_group.extract(time_constraint)

                    # Remove other time coordinates to allow a cube merge
                    # later
                    for cube in cubes_group:
                        cube.remove_coord("forecast_reference_time")
                        cube.remove_coord("forecast_period")
                elif group == "forecast_period":
                    # Identify a unique set of lead times
                    times = utils.identify_unique_times(cubes_group, group)

                    # Remove other time coordinates to allow a cube
                    # merge later
                    for cube in cubes_group:
                        cube.remove_coord("forecast_reference_time")
                        cube.remove_coord("time")
                elif group == "hour":
                    # Categorise the time coordinate of each cube into
                    # hours
                    for cube in cubes_group:
                        coord_cat.add_categorised_coord(
                            cube,
                            "hour",
                            cube.coord("time"),
                            utils.hour_from_time,
                            units="hour"
                            )

                    # Identify a unique set of times of day
                    times = utils.identify_unique_times(cubes_group, group)

                    # Now extract data at these times
                    time_constraint = iris.Constraint(
                        coord_values={group: lambda cell: cell.point
                                        in times.points})
                    cubes_group = cubes_group.extract(time_constraint)

                    # Remove other time coordinates to allow a cube
                    # merge later
                    for cube in cubes_group:
                        cube.remove_coord("forecast_reference_time")
                        cube.remove_coord("time")
                        cube.remove_coord("forecast_period")

                # Remove any duplicate cubes to allow a successful merge
                # Note this is typcially because we have the same set of
                # observations associated with more than one model
                cubes_group = utils.remove_duplicates(cubes_group)
                
                # Sum cell statistic histograms at each time in parallel
                input_params = [(cubes_group, time, iris.analysis.SUM,
                                 None) for time in times]
                
                n_proc_to_use = min(config.n_proc, len(input_params))
                if n_proc_to_use == 1:
                    result_list = [
                        utils.aggregate_at_time(input_param)
                        for input_param in input_params]
                else:           
                    with dask.config.set(num_workers=n_proc_to_use):
                        result_list = db.from_sequence(input_params).map(
                            utils.aggregate_at_time
                        ).compute()
                    
                # Gather cubes from each process into a cubelist
                cubes_group = iris.cube.CubeList(
                    itertools.chain.from_iterable(result_list))
                # Merge
                cubes_group = cubes_group.merge()
                # If the number of cases at each time is the same, the
                # above merge results in a scalar coordinate representing
                # the number of cases. Replace this scalar coordinate with
                # an auxillary coordinate that has the same length as the
                # time coordinate
                cubes_group = utils.repeat_scalar_coord_along_dim_coord(
                    cubes_group, 
                    "num_cases", 
                    group
                    )

                all_plots = []
                for time in times:
                 
                    # Extract histogram at this time
                    time_constraint = iris.Constraint(
                        coord_values={group: lambda cell: cell.point
                                        in time.points})
                    cubes_at_time = cubes_group.extract(time_constraint)

                    # Setting up figure title, name and annotation
                    img_prop = utils.set_title_and_filename(group, 
                                                            time, 
                                                            config.short_name, 
                                                            threshold, 
                                                            grid_label
                                                            )
                    annotation = utils.set_annotation(cubes_at_time)
                    
                    # New plot for models/observations on this grid at
                    # this time
                    plot = {}
                    plot = {
                        "title": img_prop["title"],
                        "filename": img_prop["filename"],
                        "annotations": annotation,
                        "field": config.long_name,
                        "bin_edges": list(bin_edges),
                        "x_label": "Cell effective radius [km]",
                        "x_limits": None,
                        "y_label": y_label,
                        "y_limits": None,
                        "cell_attribute": cell_attribute,
                        "long_name": "{0:s} histogram".format(config.long_name.lower()),
                        "short_name": "{0:s}_hist".format(config.short_name.lower()),
                        "plotdir": plot_dir,
                        "linestyle": "-",
                        "linewidth": 2,
                        "markers": "o",
                        "y_lower": None,
                        "y_upper": None,
                        "x_log": True,
                        "y_log": True
                    }
                    
                    # Loop over models/observations available on this
                    # grid at this time
                    lines = []
                    for cube in cubes_at_time:
                        line = {}
                        # Normalise histogram
                        if config.y_axis == "relative_frequency":
                            cube.data = ((100.0 * cube.data)
                                            / np.sum(cube.data,
                                                    dtype=np.float64))
                        # Add histogram to plot
                        line["x"] = list(cube.coord(cell_attribute).points)
                        line["y"] = list(cube.data)
                        line["label"] = ("{0:s}".format(cube.attributes["data_source"]))
                        line["colour"] = colours[cube.attributes["data_source"]]
                        lines.append(line)
                    plot["lines"] = lines

                    all_plots.append(plot)
                    # Set same axis limits to all plots
                    all_plots = utils.set_general_axis_limits(all_plots)
                    # New plot for models/observations on this grid, all
                    # times combined
                    all_times_agg_plot = {}
                    all_times_agg_plot = {
                        "title": img_prop["title"],
                        "annotations": annotation,
                        "field": config.long_name,
                        "bin_edges": list(bin_edges),
                        "x_label": "Cell effective radius [km]",
                        "x_limits": None,
                        "y_label": y_label,
                        "y_limits": None,
                        "cell_attribute": cell_attribute,
                        "long_name": "{0:s} histogram".format(config.long_name.lower()),
                        "short_name": "{0:s}_hist".format(config.short_name.lower()),
                        "plotdir": plot_dir,
                        "linestyle": "-",
                        "linewidth": 2,
                        "markers": "o",
                        "y_lower": None,
                        "y_upper": None,
                        "x_log": True,
                        "y_log": True
                    }
                    filename = ("{0:s}{1:s}_thresh_{2:.1f}_{3:s}"
                                .format(config.short_name, grid_label,threshold, group))
                    all_times_agg_plot["filename"] = filename
        
                    lines = []
                    # Loop over models/observations available on this grid
                    for cube in cubes_group:
                        line = {}
                        # Sum all histograms
                        cube = cube.collapsed(group, iris.analysis.SUM)

                        # Normalise histogram
                        if config.y_axis == "relative_frequency":
                            cube.data = ((100.0 * cube.data)
                                         / np.sum(cube.data, dtype=np.float64))
                            
                        line["x"] = list(cube.coord(cell_attribute).points)
                        line["y"] = list(cube.data)
                        line["label"] = ("{0:s}".format(cube.attributes["data_source"]))
                        line["colour"] = colours[cube.attributes["data_source"]]
                        lines.append(line)
                    all_times_agg_plot["lines"] = lines
                    all_times_agg_plot["y_limits"] = None
                    all_times_agg_plot["x_limits"] = None
                    # Set axis limits
                    all_times_agg_plot = utils.set_axis_limits(all_times_agg_plot)

                    all_plots.append(all_times_agg_plot)
    
                filename = "data/{}_{}_{}_plots.pkl".format(threshold, grid_spacing, group)
                with open(filename, "wb") as pickle_file:
                    pickle.dump(all_plots, pickle_file)
            
    print("Cell statistics done")
    return 0

def plot_cell_statistics(files, output_path):

    '''
    Produces histogram plots of cell statistics.

    Produces plots of each plot object produced by cell_statistics method

    Arguments
    _________

    file 
        path where all the pickle files (from cell_statistics method) reside
    putput_path
        plot dir where all plots in PNG will be saved 
    '''
    for file in files:
        # Load the JSON file as a dictionary
        with open(file, "rb") as pickle_file:
            plots = pickle.load(pickle_file)
            input_params = [(plot, output_path) for plot in plots]
            n_proc_to_use = min(config.n_proc, len(input_params))
            if n_proc_to_use == 1:
                [utils.plot_and_save(input_param)for input_param in input_params]
            else:
                with dask.config.set(num_workers=n_proc_to_use):
                    db.from_sequence(input_params).map(
                        utils.plot_and_save
                            ).compute()

