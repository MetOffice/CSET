"""OMG YOU CAN'T COMMIT WITHOUT DOCSTRINGS, EVEN IN EXPLORATORY CODE."""

import iris.analysis
import iris.coords
import iris.cube
import iris.util
import numpy as np
from scipy import ndimage


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
    """OMG YOU CAN'T COMMIT WITHOUT DOCSTRINGS, EVEN IN EXPLORATORY CODE."""
    result = []
    for cube in cubes:
        if long_name and cube.long_name == long_name:
            result.append(cube)
        elif stash and "STASH" in cube.attributes and cube.attributes["STASH"] == stash:
            result.append(cube)

    return iris.cube.CubeList(result)


def get_cell_stat_vars(cubes):
    """OMG YOU CAN'T COMMIT WITHOUT DOCSTRINGS, EVEN IN EXPLORATORY CODE."""
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


def caller_thing(cell_attribute, **kwargs):
    """
    Create a histogram from the given cube, for every threshold and cell attribute.

    The cube will be "1-hourly mean precipitation rate" or "Large-scale rainfall rate".


    Also for:
        cell attribute
            effective_radius_in_km, mean_value

    """

    # todo: remove var_name? impedes merge

    # For each model, extract the two variables we're interested in.
    model_data = {}
    for model, cubes in kwargs.items():
        model_data[model] = get_cell_stat_vars(cubes)

    # For now, thresholds and cell attributes are hard coded.
    thresholds = [0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0, 128.0]

    # todo: what about different models? how are they loaded and labelled?

    # # For now, cell attributes are hard coded.
    # cell_attributes = ["effective_radius_in_km", "mean_value"]
    #
    # # For now, hard-code to these two, which is what we see in the res output.
    # # todo: there is also "time" in the res code
    # time_groupings = ["forecast_period", "hour"]

    # We need a list of times for each time grouping
    # For forecast time, this must contain "all", plus all the T+0.5 .. T+71.5
    # For hourly, this must contain "all", plus all the 0.5Z .. 23.5Z
    # todo: we should presumably get this from the cube.
    # assert False

    # todo: we need a land-sea split input?
    # for now, hard-code as false (this is what the res output had it set to)
    # land_sea_split = False

    # what about obs? GPM & UK_RADAR_2KM? ignore for now.

    # different bins for the two cell attributes
    bin_edges = {}

    bin_edges['effective_radius_in_km'] = 10**(np.arange(0.0, 3.12, 0.12))
    bin_edges['effective_radius_in_km'] = np.insert(bin_edges['effective_radius_in_km'], 0, 0)

    bin_edges['mean_value'] = 10**(np.arange(-1, 2.7, 0.12))
    bin_edges['mean_value'] = np.insert(bin_edges['mean_value'], 0, 0)



    model_histograms = {}
    for model, data in model_data.keys():
        for threshold in thresholds:
            something_like_cell_attribute_histogram(
                cube,
                attribute=cell_attribute,
                bin_edges=bin_edges[cell_attribute],
                threshold=threshold,
            )


    # return a cube for each model
    return model_histograms


def something_like_cell_attribute_histogram(cube, attribute, bin_edges, threshold=0.0):
    hist_cube = iris.cube.CubeList()
    coords = get_non_spatial_coords(cube)

    # Express histogram bins as an Iris coordinate
    bin_centres = 0.5 * (bin_edges[1:] + bin_edges[:-1])
    bins_as_coord = iris.coords.DimCoord(
        bin_centres, long_name=attribute, units=cube.units,
        coord_system=None, bounds=np.column_stack((bin_edges[0:-1], bin_edges[1:])))

    hist_cubes = iris.cube.CubeList()

    for slc in cube.slices_over(coords):
        # Identify connected cells in this spatial slice
        cells = find_cells(slc, threshold=threshold)

        if cells:
            # Extract values of the desired cell attribute
            cell_attributes = [cell.attributes[attribute] for cell in cells]

            # Construct a histogram of the desired cell attribute
            hist, _ = np.histogram(cell_attributes)
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


def connected_object_labelling(data, threshold=0.0, min_size=1, connectivity=1):
    '''
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

    Returns:

    * **label_array** - an integer array where each unique object in the input \
                        array has a unique label in the returned array.
    * **num_objects** - the number of objects found.
    '''
    # Apply the supplied threshold to the data to generate a binary array
    binary_data = data.copy()
    if np.ma.is_masked(binary_data):
        # If the data is masked, replace any masked values with (threshold - 1)
        # thus guaranteeing they will be below the threshold and thus set to 0
        # below
        binary_data = np.ma.filled(binary_data, fill_value=(threshold - 1))
    # Set values above and below the threshold to 1 and 0, respectively
    indices_above = (binary_data > threshold)
    indices_below = (binary_data <= threshold)
    binary_data[indices_above] = 1
    binary_data[indices_below] = 0

    # Construct a structuring element that defines how the neighbours of
    # a grid point are assigned
    structure_element = ndimage.morphology.generate_binary_structure(
        data.ndim, connectivity)

    # Label distinct (connected) objects in the binary array
    label_array, num_objects = ndimage.measurements.label(
        binary_data,
        structure=structure_element)

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

    Returns:

    * **cells** - a :class:`iris.cube.CubeList` of \
                  :class:`iris.cube.Cube` objects, each one corresponding to \
                  an identified cell.
    """

    # Convert input area threshold from km^2 to m^2
    M_IN_KM = 1000
    area_threshold = (float(M_IN_KM)**2) * area_threshold

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
        aux_coords = [(coord, []) for coord in
                      get_non_spatial_coords(slc)]

        # Find and label cells
        # Call connected object labelling function based on
        # scipy.ndimage.measurements.label
        cell_label_array, _ = connected_object_labelling(
            slc.data,
            threshold=threshold,
            min_size=1,
            connectivity=connectivity)

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
                raise ValueError("Masked data found in cell {0:d}"
                                 .format(cell_label))

            # If cell area is less than area_threshold, discard it
            # (by setting its label to the background value)
            cell_area = np.sum(cell_grid_areas, dtype=np.float64)
            if cell_area < area_threshold:
                cell_label_array[cell_indices] = 0
                continue

            # Estimate cell centre position
            # TODO Is there a better way of doing this? C.O.M?
            cell_centre = (np.mean(cell_x, dtype=np.float64),
                           np.mean(cell_y, dtype=np.float64))
            # Area-weighted mean value in cell
            cell_mean = (np.sum((cell_grid_areas * cell_values),
                                dtype=np.float64)
                         / cell_area)
            # Convert cell area from m^2 to km^2...
            cell_area /= (float(M_IN_KM)**2)
            # ...and then cell effective radius in km
            cell_radius = np.sqrt(cell_area / np.pi)

            # Create an Iris cube to store this cell
            cell_cube = iris.cube.Cube(
                cell_values,
                long_name="{:s} cell".format(cube.name()),
                units=cube.units,
                attributes=cube.attributes,
                cell_methods=cube.cell_methods,
                aux_coords_and_dims=aux_coords)

            # Set up x, y coordinates describing the grid points in the cell...
            cell_x_coord = iris.coords.AuxCoord(
                cell_x,
                standard_name=x_coord.standard_name,
                long_name=x_coord.long_name,
                units=x_coord.units,
                bounds=None,
                attributes=x_coord.attributes,
                coord_system=x_coord.coord_system)
            cell_y_coord = iris.coords.AuxCoord(
                cell_y,
                standard_name=y_coord.standard_name,
                long_name=y_coord.long_name,
                units=y_coord.units,
                bounds=None,
                attributes=y_coord.attributes,
                coord_system=y_coord.coord_system)
            # ...and add them to the cell cube
            cell_cube.add_aux_coord(cell_x_coord, 0)
            cell_cube.add_aux_coord(cell_y_coord, 0)

            # Set up a coordinate describing the areas of grid cells in
            # the cell object...
            cell_grid_area_coord = iris.coords.AuxCoord(cell_grid_areas,
                                                        long_name="grid_areas",
                                                        units="m2")
            #...and add it to the cell cube
            cell_cube.add_aux_coord(cell_grid_area_coord, 0)

            # Finally add some attriubtes to the cube that describe some
            # useful information about the cell
            #cell_cube.attributes["label"] = int(cell_label)
            cell_cube.attributes["centre"] = cell_centre
            cell_cube.attributes["area_in_km2"] = cell_area
            cell_cube.attributes["effective_radius_in_km"] = cell_radius
            cell_cube.attributes["mean_value"] = cell_mean
            #cell_cube.attributes["indices"] = cell_indices
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
