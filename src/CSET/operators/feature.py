# © Crown copyright, Met Office (2022-2025) and CSET contributors.
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
"""Operators for identifying and tracking features."""

import logging
import os

import iris
import iris.cube
import iris.util
import numpy as np
from simpletrack.track import Tracker

from CSET._common import iter_maybe


def track(
    cube: iris.cube.Cube,
    threshold: float,
    under_threshold: bool = False,
    min_size: int = 4,
    retain_lifetime_on_split: bool = True,
    tracking_nbhood: int = 5,
    overlap_threshold: float = 0.3,
    save_data: bool = False,
):
    """Track features between subsequent timesteps.

    Parameters
    ----------
    threshold: float
        The threshold value for feature detection.
    under_threshold: bool, optional
        If set to True, features are identified where the data is below the threshold.
        If set to False, features are identified where the data is above the threshold.
        Default is False.
    min_size: int, optional
        The minimum number of contiguous grid points required for a feature to be tracked.
        Default is 4.
    retain_lifetime_on_split: bool, optional
        If set to True, the lifetime of a feature is retained when it splits into
        multiple features. If set to False, the lifetime is reset when a feature splits.
        Default is True.
    tracking_nbhood: int, optional
        The size of the neighbourhood used for tracking features between timesteps.
        This dictates the maximum pixel radius from a feature centroid at which new features could
        reasonably be spawned.
        Default is 5.
    overlap_threshold: float, optional
        The minimum overlap required between features in consecutive timesteps for
        them to be considered the same feature.
        Default is 0.3.
    save_data: bool, optional
        If set to True, all tracking data is saved to disk for further analysis (including csv
        and txt files containing feature properties that are not returned in output cubes).
        Default is False.

    Returns
    -------
    tracking_cubes: iris.cube.CubeList
        A list of iris cubes containing tracking data, including feature ID, lifetime,
        and locations of initiating features.

    Notes
    -----
    This operator uses the Simple-Track package to track features between timesteps. Simple-Track is a
    data-agnostic, threshold-based object tracking algorithm for 2D data. Features are tracked between
    consecutive frames of data by projecting feature fields onto common timeframes and matching
    between them based on the degree of overlap. Matched features retain the same identification
    between all tracked fields, while new features are assigned a unique label.
    Thus, Simple-Track compiles comprehensive information about feature merging, splitting, accretion,
    initiation and dissipation.

    Currently outputs three cubes containing the following data:
        "feature_id":
            A 2D field containing the unique label assigned to each feature, which is retained
            if the feature is tracked across multiple timesteps. This cube can be used as a mask
            to identify the location of the tracked feature throughout the evaluation period.
        "feature_lifetime":
            A 2D field containing the lifetime of each feature in terms of the number of
            timesteps it has been tracked for. This cube can be used to distinguish between
            mature and fresh features.
        "feature_init":
            A 2D binary field indicating the location of newly initiated features at each timestep.
            These features are identified as having a lifetime of 1 AND have initiated sufficiently
            far from other, existing features that they are not considered to have spawned from them.

    Links
    ----------
    .. https://github.com/ParaChute-UK/simple-track

    Examples
    --------
    >>> tracking_cubes = feature.track(threshold=2)
    >>> lifetime_cube = tracking_cubes.extract_cube("feature_lifetime")
    # Plot the final timestep of lifetime cube. This will show
    # the lifetime of features that have been tracked for multiple previous
    # timesteps, as well as new features that have just been initiated.
    >>> iplt.pcolormesh(lifetime_cube[-1,:,:],cmap=mpl.cm.bwr)
    >>> plt.gca().coastlines('10m')
    >>> plt.clim(-5,5)
    >>> plt.colorbar()
    >>> plt.show()

    """
    # Setup config
    tracker_config = {
        "FEATURE": {
            "threshold": threshold,
            "under_threshold": under_threshold,
            "min_size": min_size,
        },
        "TRACKING": {
            "retain_lifetime_on_split": retain_lifetime_on_split,
            "overlap_nbhood": tracking_nbhood,
            "overlap_threshold": overlap_threshold,
        },
        "OUTPUT": {
            "save_data": save_data,
            "experiment_name": "feature_tracking",
            "path": f"{os.getcwd()}/tracking_data",
        },
    }
    logging.debug(f"Tracker config: {tracker_config}")

    # Get cube data into a dict to pass to Tracker
    times = cube.coord("time").points
    time_units = cube.coord("time").units
    times_dt = [time_units.num2pydate(t) for t in times]
    cube_dict = {
        time: cube_slice.data
        for time, cube_slice in zip(times_dt, cube.slices_over("time"), strict=True)
    }

    # Run tracking, returning Timeline object
    timeline = Tracker(tracker_config).run(cube_dict)
    logging.debug("Tracking completed")

    # Use input cube as template to make returned cube
    # By iterating over all cube times, this will ensure all data is present
    # If a Frame at the given time is not contained in the timeline, error is raised
    output_type_and_methods = {
        "lifetime": {
            "getter": "lifetime_field",
            "cube_name": "feature_lifetime",
        },
        "feature": {
            "getter": "feature_field",
            "cube_name": "feature_id",
        },
        "init": {
            "getter": "get_init_field",
            "cube_name": "feature_init",
        },
    }

    tracking_cubelist = iris.cube.CubeList()
    for output_type in output_type_and_methods:
        tracking_data = []
        for time in times_dt:
            frame = timeline.get_frame(time)
            getter = getattr(frame, output_type_and_methods[output_type]["getter"])
            if callable(getter):
                tracking_data.append(getter())
            else:
                tracking_data.append(getter)

        # Convert to numpy arrays
        tracking_data = np.stack(tracking_data, axis=0)

        # Create cubes
        tracking_cube = cube.copy(data=tracking_data)
        tracking_cube.long_name = output_type_and_methods[output_type]["cube_name"]
        tracking_cube.standard_name = None
        tracking_cube.var_name = None
        tracking_cube.units = "1"
        tracking_cubelist.append(tracking_cube)

    return tracking_cubelist


def cell_stats(
    cubes: iris.cube.Cube | iris.cube.CubeList,
    threshold: float,
    under_threshold: bool = False,
    min_size: int = 4,
    save_data: bool = False,
):
    """Identify features in each timestep and output statistics.

    Parameters
    ----------
    threshold: float
        The threshold value for feature detection.
    under_threshold: bool, optional
        If set to True, features are identified where the data is below the threshold.
        If set to False, features are identified where the data is above the threshold.
        Default is False.
    min_size: int, optional
        The minimum number of contiguous grid points required for a feature to be tracked.
        Default is 4.
    # feature_size_unit: str, optional
    #     The unit to define feature size output. Options are "feature_effective_radius"
    #     (the radius of a circle with the same area as the feature, in km) or "
    #     feature_grid_points" (the number of grid points contained in the feature).
    #     Default is "feature_effective_radius".
    save_data: bool, optional
        If set to True, all tracking data is saved to disk for further analysis (including csv
        and txt files containing feature properties that are not returned in output cubes).
        Default is False.

    Returns
    -------
    cell_stats_cubes: iris.cube.CubeList
        An iris CubeList containing "feature_size", "feature_mean", and "feature_max" cubes.

    Notes
    -----
    This operator uses the Simple-Track package with tracking disabled to identify features
    in each timestep and compile cell statistics. Outputs cubes containing feature size (number
    of grid points), mean value within features, and maximum value within features.

    Links
    ----------
    .. https://github.com/ParaChute-UK/simple-track

    Examples
    --------
    >>> cell_stats_cubes = feature.cell_stats(threshold=2)
    >>> feature_size_cube = cell_stats_cubes.extract_cube("feature_size")
    >>> plt.hist(feature_size_cube[-1])
    >>> plt.show()

    """
    # Check inputs
    cubes = iter_maybe(cubes)
    cell_stats_cubelist = iris.cube.CubeList()

    # Run tracking on all input data
    for cube in cubes:
        model_name = cube.attributes.get("model_name", None)
        # Setup config
        tracker_config = {
            "FEATURE": {
                "threshold": threshold,
                "under_threshold": under_threshold,
                "min_size": min_size,
            },
            "OUTPUT": {
                "save_data": save_data,
                "experiment_name": "feature_tracking",
                "path": f"{os.getcwd()}/{model_name}/cell-stats_data",
                "skip_tracking": True,
            },
        }
        logging.debug(f"Tracker config: {tracker_config}")

        # Get cube data into a dict to pass to Tracker
        times = cube.coord("time").points
        time_units = cube.coord("time").units
        times_dt = [time_units.num2pydate(t) for t in times]
        cube_dict = {
            time: cube_slice.data
            for time, cube_slice in zip(times_dt, cube.slices_over("time"), strict=True)
        }

        # Run tracking, returning Timeline object
        timeline = Tracker(tracker_config).run(cube_dict)

        logging.debug(f"Tracking completed for {model_name}")

        # Get feature data from each frame of data, append to list of lists
        # before conversion to numpy array (which requires knowledge of max
        # number of features before constructing array shape)
        size_data, mean_data, max_data = [], [], []
        number_of_features = []
        for time in times_dt:
            frame = timeline.get_frame(time)
            features = frame.features
            size_data.append([feature.get_size() for feature in features.values()])
            mean_data.append([feature.mean for feature in features.values()])
            max_data.append([feature.max for feature in features.values()])
            number_of_features.append(len(features))

        # Pad data with NaNs to create arrays of consistent shape (max number of features across
        # all timesteps)
        arr_size = max(number_of_features)

        # Size data is integer, but we need to pad with NaNs (which is a float), so fill
        # with invalid value first
        size_data = np.array(
            [
                np.pad(sizes, (0, arr_size - len(sizes)), constant_values=-100)
                for sizes in size_data
            ],
            dtype=float,
        )
        size_data[size_data == -100] = np.nan

        # Mean and max data are already float, so can be padded with NaNs directly.
        mean_data = np.array(
            [
                np.pad(means, (0, arr_size - len(means)), constant_values=np.nan)
                for means in mean_data
            ]
        )
        max_data = np.array(
            [
                np.pad(maxs, (0, arr_size - len(maxs)), constant_values=np.nan)
                for maxs in max_data
            ]
        )

        # Create cubes
        time_coord = cube.coord("time").copy()
        feature_coord = iris.coords.DimCoord(
            np.arange(arr_size),
            long_name="feature_number",
            var_name="feature_number",
            units="1",
        )
        coords = [time_coord, feature_coord]
        coords_and_dims = [(coord, i) for i, coord in enumerate(coords)]

        # Set cube properties
        cube_properties = {
            "feature_size": {
                "data": size_data,
                "long_name": "feature_size",
                "units": "1",
            },
            "feature_mean": {
                "data": mean_data,
                "long_name": "feature_mean",
                "units": 1,
            },
            "feature_max": {"data": max_data, "long_name": "feature_max", "units": 1},
        }
        # TODO: need to consider better implementation which doesn't overwrite feature_size cube
        # TODO: consider iris.analysis.cartography.area_weights() or hzntl_coord.is_regular()
        # to check for regular spacing
        # TODO: Check for hzntl_coords is empty list and handle elegantly
        # if feature_size_unit == "feature_effective_radius":
        #     # Convert feature size to effective radius, assuming uniform grid
        #     # Guess coord representing horizontal grid (choose first available)
        #     hzntl_coord = [
        #         coord
        #         for coord in cube.coords()
        #         if iris.util.guess_coord_axis(coord) in ["X", "Y"]
        #     ][0]
        #     logging.debug(f"Attempting to convert to effective radius using {hzntl_coord}")
        #     # Convert to km if possible
        #     # TODO: fall back to feature_size if this conversion fails
        #     # TODO: this will still add the name "feature_effective_radius" to the feature_size
        #     # cube, even though the data is actually pixel size. Figure out elegant solution.
        #     try:
        #         hzntl_coord.convert_units("km")
        #     except:
        #         pass
        #     # Naive grid spacing estimate, correct for regular grids, likely wildly
        #     # inaccruate for LFRic/irregular grids
        #     grid_spacing = np.abs(np.diff(hzntl_coord.points).mean())
        #     # Convert feature size in grid points to effective radius in km
        #     size_data = np.sqrt(size_data * grid_spacing**2 / np.pi)
        #     # Reset cube properties
        #     cube_properties["feature_size"]["data"] = size_data
        #     cube_properties["feature_size"]["units"] = "km"

        # Get list of coords to copy from input cube to output cubes
        copyable_coord_names = [
            "realization",
            "hour",
            "forecast_period",
            "forecast_reference_time",
            "model_name",
            "cset_comparison_base",
        ]
        input_cube_coord_names = []
        for coord in cube.coords():
            input_cube_coord_names.append(coord.standard_name)
            input_cube_coord_names.append(coord.long_name)

        coords_to_copy = [
            coord_name
            for coord_name in copyable_coord_names
            if coord_name in input_cube_coord_names
        ]

        # Populate cubelist
        for cb_props in cube_properties.values():
            cell_stats_cube = iris.cube.Cube(
                data=cb_props["data"],
                long_name=cb_props["long_name"],
                units=cb_props["units"],
                dim_coords_and_dims=coords_and_dims,
            )
            # Add other metadata from input cube
            for coord_name in coords_to_copy:
                coord = cube.coord(coord_name).copy()
                # Check if this coord represents a dimension of data
                dims = cube.coord_dims(coord)
                if len(dims) > 1:
                    cell_stats_cube.add_aux_coord(coord, dims)
                else:
                    cell_stats_cube.add_aux_coord(coord)

            # Copy over attributes
            cell_stats_cube.attributes = cube.attributes

            # Add to cubelist
            cell_stats_cubelist.append(cell_stats_cube)

    return cell_stats_cubelist
