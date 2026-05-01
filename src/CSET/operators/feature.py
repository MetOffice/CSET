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
        A list of iris cubes containing tracking data, including feauture ID, lifetime,
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
            far from other, existing features that they are not considered to have spawed from them.

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
    cube: iris.cube.Cube,
    threshold: float,
    under_threshold: bool = False,
    min_size: int = 4,
    feature_size_unit: str = "feature_effective_radius",
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
    feature_size_unit: str, optional
        The unit to define feature size output. Options are "feature_effective_radius"
        (the radius of a circle with the same area as the feature, in km) or "
        feature_grid_points" (the number of grid points contained in the feature).
        Default is "feature_effective_radius".
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
            "path": f"{os.getcwd()}/cell-stats_data",
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
    logging.debug("Tracking completed")

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
    cell_stats_cubelist = iris.cube.CubeList()

    # Set cube properties
    cube_properties = {
        "feature_size": {
            "data": size_data,
            "long_name": feature_size_unit,
            "units": "1",
        },
        "feature_mean": {"data": mean_data, "long_name": "feature_mean", "units": 1},
        "feature_max": {"data": max_data, "long_name": "feature_max", "units": 1},
    }
    if feature_size_unit == "feature_effective_radius":
        # Conert feature size to effective radius, assuming uniform grid
        # Guess coord representing horizontal grid (choose first available)
        hzntl_coord = [
            coord
            for coord in cube.coords()
            if iris.util.guess_coord_axis(coord) in ["X", "Y"]
        ][0]
        logging.debug(f"Attempting to convert to effective radius using {hzntl_coord}")
        # Convert to km if possible
        # TODO: fall back to feature_size if this conversion fails
        hzntl_coord.convert_units("km")
        # Naive grid spacing estimate, correct for regular grids, likely wildly
        # inaccruate for LFRic/irregular grids
        grid_spacing = np.abs(np.diff(hzntl_coord.points).mean())
        # Convert feature size in grid points to effective radius in km
        size_data = np.sqrt(size_data * grid_spacing**2 / np.pi)
        # Reset cube properties
        cube_properties["feature_size"]["data"] = size_data
        cube_properties["feature_size"]["units"] = "km"

    # Populate cubelist
    for cb_props in cube_properties.values():
        cell_stats_cube = iris.cube.Cube(
            data=cb_props["data"],
            long_name=cb_props["long_name"],
            units=cb_props["units"],
            dim_coords_and_dims=coords_and_dims,
        )
        cell_stats_cubelist.append(cell_stats_cube)

    return cell_stats_cubelist
