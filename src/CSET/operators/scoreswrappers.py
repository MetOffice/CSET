# © Crown copyright, Met Office (2022-2026) and CSET contributors.
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

"""A module containing wrappers for the scores module."""

import logging
import operator

import iris
import iris.exceptions
import numpy as np
import scores
import scores.categorical
import scores.continuous
import scores.probability
import xarray as xr
from iris.cube import Cube, CubeList
from iris.util import reverse

from CSET._common import is_increasing
from CSET.operators._utils import fully_equalise_attributes, get_cube_yxcoordname
from CSET.operators.constraints import (
    generate_realization_constraint,
    generate_remove_single_ensemble_member_constraint,
)
from CSET.operators.misc import _extract_common_time_points
from CSET.operators.read import _realization_callback
from CSET.operators.regrid import regrid_onto_cube

logger = logging.getLogger(__name__)


def _sort_cubes_for_verification(cubes: CubeList):
    """Prepare cubes ready for verification in scores.

    Parameters
    ----------
    cubes: iris.cube.CubeList
        A CubeList of exact 2 cubes, one from each model.

    Returns
    -------
    base: iris.cube.Cube
        The cube from the "analysis" in the same format as the other model.
    other: iris.cube.Cube
        The cube from the model in the same format as the base model.

    Raises
    ------
    ValueError: "cubes should contain exactly 2 cubes."
        If any other number of cubes are present.

    Notes
    -----
    This operator is used for sorting the data into the correct format. It
    is likely going to need to be refactored out of CSET and perhaps moved into
    `CSET._utils` given common code between here and `misc.difference`.
    """
    # Set cubes into correct format using code from difference operator
    if len(cubes) != 2:
        raise ValueError("cubes should contain exactly 2 cubes.")
    base: Cube = cubes.extract_cube(iris.AttributeConstraint(cset_comparison_base=1))
    other: Cube = cubes.extract_cube(
        iris.Constraint(
            cube_func=lambda cube: "cset_comparison_base" not in cube.attributes
        )
    )

    # If cubes contain a pressure coordinate, ensure it is increasing.
    for cube in cubes:
        try:
            if len(cube.coord("pressure").points) > 2 and not is_increasing(
                cube.coord("pressure").points
            ):
                reverse(cube, "pressure")

        except iris.exceptions.CoordinateNotFoundError:
            pass

    # Extract just common time points.
    base, other = _extract_common_time_points(base, other)

    # Get spatial coord names.
    base_lat_name, base_lon_name = get_cube_yxcoordname(base)
    other_lat_name, other_lon_name = get_cube_yxcoordname(other)

    # Ensure cubes to compare are on common differencing grid.
    # This is triggered if either
    #      i) latitude and longitude shapes are not the same. Note grid points
    #         are not compared directly as these can differ through rounding
    #         errors.
    #     ii) or variables are known to often sit on different grid staggering
    #         in different models (e.g. cell center vs cell edge), as is the case
    #         for UM and LFRic comparisons.
    # In future greater choice of regridding method might be applied depending
    # on variable type. Linear regridding can in general be appropriate for smooth
    # variables. Care should be taken with interpretation of differences
    # given this dependency on regridding.
    if (
        base.coord(base_lat_name).shape != other.coord(other_lat_name).shape
        or base.coord(base_lon_name).shape != other.coord(other_lon_name).shape
    ) or (
        base.long_name
        in [
            "eastward_wind_at_10m",
            "northward_wind_at_10m",
            "northward_wind_at_cell_centres",
            "eastward_wind_at_cell_centres",
            "zonal_wind_at_pressure_levels",
            "meridional_wind_at_pressure_levels",
            "potential_vorticity_at_pressure_levels",
            "vapour_specific_humidity_at_pressure_levels_for_climate_averaging",
        ]
    ):
        logger.debug("Linear regridding base cube to other grid to compute differences")
        base = regrid_onto_cube(base, other, method="Linear")

    # Figure out if we are comparing between UM and LFRic; flip array if so.
    base_lat_direction = is_increasing(base.coord(base_lat_name).points)
    other_lat_direction = is_increasing(other.coord(other_lat_name).points)
    if base_lat_direction != other_lat_direction:
        # Copy base cube for correct coordinate information.
        other_tmp = base.copy()
        # Flip the data and place in the copied cube.
        other_tmp.data = np.flip(
            other.data, other.coord(other_lat_name).cube_dims(other)
        )
        # Use original name and units from the other cube.
        other_tmp.rename(other.name())
        other_tmp.units = other.units
        # Replace the cube.
        other = other_tmp

    # Equalise attributes so we can merge.
    fully_equalise_attributes(CubeList([base, other]))
    logger.debug("Base: %s\nOther: %s", base, other)

    return base, other


def _resolve_preserve_dims(
    cube: Cube,
    data_array: xr.DataArray,
    preserved_coordinates: list[str] | str | None,
) -> list[str] | None:
    """Resolve preserve coordinates to xarray dimension names.

    The ``scores`` package expects preserve dimensions to match xarray
    dimension names. In Iris data, commonly used coordinates such as ``time``
    may be auxiliary coordinates attached to a differently named dimension
    (e.g. ``dim0``). This helper maps coordinate names to their underlying
    dimension names and helps to convert from iris to xarray coordinate dimension names.
    """
    if preserved_coordinates is None:
        return None

    coord_names = (
        [preserved_coordinates]
        if isinstance(preserved_coordinates, str)
        else preserved_coordinates
    )
    preserve_dims: list[str] = []

    for coord_name in coord_names:
        # Already an xarray dimension name.
        if coord_name in data_array.dims:
            if coord_name not in preserve_dims:
                preserve_dims.append(coord_name)
            continue

        # Otherwise, map coordinate name to dimension index/indices.
        try:
            dim_indices = cube.coord_dims(coord_name)
        except iris.exceptions.CoordinateNotFoundError:
            # Keep original name so scores raises a clear error for unknown keys.
            if coord_name not in preserve_dims:
                preserve_dims.append(coord_name)
            continue

        for dim_index in dim_indices:
            dim_name = data_array.dims[dim_index]
            if dim_name not in preserve_dims:
                preserve_dims.append(dim_name)

    return preserve_dims


def scores_rmse_model_obs(
    cubes: CubeList, preserved_coordinates: list[str] | str | None = None
):
    r"""Calculate the Root Mean Square Error (RMSE) using scores.

    Acts as a wrapper around the RMSE calculation from ``scores`` ([scoresa]_, [scoresb]_).
    It is calculated as

    .. math:: RMSE = \sqrt{\frac{1}{N} \Sigma(forecast - observations)^2}

    Parameters
    ----------
    cubes: iris.cube.CubeList
        A CubeList containing an observation cube and at least one model cube.
    preserved_coordinates: list[str] | str | None, default is None.
        The coordinates that you wish to preserve in the calculaiton of the
        RMSE. For example if you want a map of each time you can preserve
        ["time","grid_latitude", "grid_longitude"] or if you want a time series
        you can preserve ["time"], if you want to collapse to a single value
        use `None`. The default is `None`.

    Returns
    -------
    scores_cube: iris.cube.Cube
        A cube containing the RMSE between the models and observation cube.
    """
    rmse_cubes = CubeList()
    model_list = CubeList()

    for cb in cubes:
        if "observed" in cb.long_name:
            observed = cb
        else:
            model_list.append(cb)

    for model in model_list:
        input_cubelist = CubeList()
        input_cubelist.append(observed)
        input_cubelist.append(model)
        rmse = scores_rmse(
            input_cubelist, preserved_coordinates, obs_model_comparison=True
        )
        model_name = model.attributes["model_name"]
        rmse.attributes["model_name"] = model_name
        rmse_cubes.append(rmse)

    return rmse_cubes


def scores_rmse(
    cubes: CubeList,
    preserved_coordinates: list[str] | str | None = None,
    obs_model_comparison: bool = False,
):
    r"""Calculate the Root Mean Square Error (RMSE) using scores.

    Acts as a wrapper around the RMSE calculation from ``scores`` ([scoresa]_, [scoresb]_).
    It is calculated as

    .. math:: RMSE = \sqrt{\frac{1}{N} \Sigma(forecast - observations)^2}

    Parameters
    ----------
    cubes: iris.cube.CubeList
        A CubeList containing exactly two cubes: a base and an "other" model,
        this can be an analysis and the model.
    preserved_coordinates: list[str] | str | None, default is None.
        The coordinates (or xarray dimension names) that you wish to preserve in the calculaiton of the
        RMSE. For example if you want a map of each time you can preserve
        ["time","grid_latitude", "grid_longitude"] or if you want a time series
        you can preserve ["time"], if you want to collapse to a single value
        use `None`. The default is `None`.

    Returns
    -------
    scores_cube: iris.cube.Cube
        A cube containing the RMSE between the base and other cube.
    """
    if obs_model_comparison:
        for cb in cubes:
            if "observed" in cb.long_name:
                base = cb
            else:
                other = cb
    else:
        base, other = _sort_cubes_for_verification(cubes)

    # Copy the coordinates of the input cubes.
    other_xr = xr.DataArray.from_iris(other)
    base_xr = xr.DataArray.from_iris(base)
    preserve_dims = _resolve_preserve_dims(other, other_xr, preserved_coordinates)

    # Scores operates on xarray data arrays, so we transform the iris cube into an array,
    # apply scores, and then transform it back.
    scores_cube = xr.DataArray.to_iris(
        scores.continuous.rmse(
            other_xr,
            base_xr,
            preserve_dims=preserve_dims,
        )
    )

    # If time is aggregated out, attach a scalar time coordinate with bounds
    # so plotting can display the aggregated period in the title.
    try:
        if not scores_cube.coords("time"):
            base_time = base.coord("time")
            time_vals = (
                base_time.bounds.flatten()
                if base_time.has_bounds()
                else base_time.points
            )
            t_start = float(time_vals[0])
            t_end = float(time_vals[-1])
            t_mid = 0.5 * (t_start + t_end)

            scores_cube.add_aux_coord(
                iris.coords.AuxCoord(
                    t_mid,
                    standard_name=base_time.standard_name,
                    long_name=base_time.long_name,
                    var_name=base_time.var_name,
                    units=base_time.units,
                    bounds=np.array([t_start, t_end]),
                    attributes=base_time.attributes.copy(),
                )
            )
    except iris.exceptions.CoordinateNotFoundError:
        pass

    scores_cube.rename(f"RMSE_of_{base.name()}")
    # if preserved_coordinates == ["grid_latitude", "grid_longitude"]:
    #   scores_cube.add_aux_coord(time_coord)
    return scores_cube


def scores_mae(cubes: CubeList, preserved_coordinates: list[str] | str | None = None):
    r"""Calculate the Mean Absolute Error (MAE) using scores.

    Acts as a wrapper around the MAE calculation from ``scores`` ([scoresa]_, [scoresb]_).

    Parameters
    ----------
    cubes: iris.cube.CubeList
        A CubeList containing exactly two cubes: a base and an "other" model,
        this can be an analysis and the model.
    preserved_coordinates: list[str] | str | None, default is None.
        The coordinates that you wish to preserve in the calculaiton of the
        MAE. For example if you want a map of each time you can preserve
        ["time","grid_latitude", "grid_longitude"] or if you want a time series
        you can preserve ["time"], if you want to collapse to a single value
        use `None`. The default is `None`.

    Returns
    -------
    scores_cube: iris.cube.Cube
        A cube containing the MAE between the base and other cube.
    """
    base, other = _sort_cubes_for_verification(cubes)

    # Copy the coordinates of the input cubes.
    other_xr = xr.DataArray.from_iris(other)
    base_xr = xr.DataArray.from_iris(base)
    preserve_dims = _resolve_preserve_dims(other, other_xr, preserved_coordinates)

    # Scores operates on xarray data arrays, so we transform the iris cube into an array,
    # apply scores, and then transform it back.
    scores_cube = xr.DataArray.to_iris(
        scores.continuous.mae(
            other_xr,
            base_xr,
            preserve_dims=preserve_dims,
        )
    )

    # If time is aggregated out, attach a scalar time coordinate with bounds
    # so plotting can display the aggregated period in the title.
    try:
        if not scores_cube.coords("time"):
            base_time = base.coord("time")
            time_vals = (
                base_time.bounds.flatten()
                if base_time.has_bounds()
                else base_time.points
            )
            t_start = float(time_vals[0])
            t_end = float(time_vals[-1])
            t_mid = 0.5 * (t_start + t_end)

            scores_cube.add_aux_coord(
                iris.coords.AuxCoord(
                    t_mid,
                    standard_name=base_time.standard_name,
                    long_name=base_time.long_name,
                    var_name=base_time.var_name,
                    units=base_time.units,
                    bounds=np.array([t_start, t_end]),
                    attributes=base_time.attributes.copy(),
                )
            )
    except iris.exceptions.CoordinateNotFoundError:
        pass

    scores_cube.rename(f"MAE_of_{base.name()}")
    return scores_cube


def scores_additive_bias(
    cubes: CubeList, preserved_coordinates: list[str] | str | None = None
):
    r"""Calculate the Additive Bias (Mean Error) using scores.

    Acts as a wrapper around the ME calculation from ``scores`` ([scoresa]_, [scoresb]_).

    Parameters
    ----------
    cubes: iris.cube.CubeList
        A CubeList containing exactly two cubes: a base and an "other" model,
        this can be an analysis and the model.
    preserved_coordinates: list[str] | str | None, default is None.
        The coordinates that you wish to preserve in the calculaiton of the
        ME. For example if you want a map of each time you can preserve
        ["time","grid_latitude", "grid_longitude"] or if you want a time series
        you can preserve ["time"], if you want to collapse to a single value
        use `None`. The default is `None`.

    Returns
    -------
    scores_cube: iris.cube.Cube
        A cube containing the ME between the base and other cube.
    """
    base, other = _sort_cubes_for_verification(cubes)

    # Copy the coordinates of the input cubes.
    other_xr = xr.DataArray.from_iris(other)
    base_xr = xr.DataArray.from_iris(base)
    preserve_dims = _resolve_preserve_dims(other, other_xr, preserved_coordinates)

    # Scores operates on xarray data arrays, so we transform the iris cube into an array,
    # apply scores, and then transform it back.
    scores_cube = xr.DataArray.to_iris(
        scores.continuous.additive_bias(
            other_xr,
            base_xr,
            preserve_dims=preserve_dims,
        )
    )

    # If time is aggregated out, attach a scalar time coordinate with bounds
    # so plotting can display the aggregated period in the title.
    try:
        if not scores_cube.coords("time"):
            base_time = base.coord("time")
            time_vals = (
                base_time.bounds.flatten()
                if base_time.has_bounds()
                else base_time.points
            )
            t_start = float(time_vals[0])
            t_end = float(time_vals[-1])
            t_mid = 0.5 * (t_start + t_end)

            scores_cube.add_aux_coord(
                iris.coords.AuxCoord(
                    t_mid,
                    standard_name=base_time.standard_name,
                    long_name=base_time.long_name,
                    var_name=base_time.var_name,
                    units=base_time.units,
                    bounds=np.array([t_start, t_end]),
                    attributes=base_time.attributes.copy(),
                )
            )
    except iris.exceptions.CoordinateNotFoundError:
        pass
    scores_cube.rename(f"Additive_Bias_of_{base.name()}")
    return scores_cube


def scores_correlation_pearsonr(
    cubes: CubeList, preserved_coordinates: list[str] | str | None = None
):
    r"""Calculate the Pearson's Correlation (PC) coefficient using scores.

    Acts as a wrapper around the PC calculation from ``scores`` ([scoresa]_, [scoresb]_).

    Parameters
    ----------
    cubes: iris.cube.CubeList
        A CubeList containing exactly two cubes: a base and an "other" model,
        this can be an analysis and the model.
    preserved_coordinates: list[str] | str | None, default is None.
        The coordinates that you wish to preserve in the calculation of the
        PC. For example if you want a map of each time you can preserve
        ["time","grid_latitude", "grid_longitude"] or if you want a time series
        you can preserve ["time"], if you want to collapse to a single value
        use `None`. The default is `None`.

    Returns
    -------
    scores_cube: iris.cube.Cube
        A cube containing the PC between the base and other cube.
    """
    base, other = _sort_cubes_for_verification(cubes)

    # Copy the coordinates of the input cubes.
    other_xr = xr.DataArray.from_iris(other)
    base_xr = xr.DataArray.from_iris(base)
    preserve_dims = _resolve_preserve_dims(other, other_xr, preserved_coordinates)

    # Scores operates on xarray data arrays, so we transform the iris cube into an array,
    # apply scores, and then transform it back.
    scores_cube = xr.DataArray.to_iris(
        scores.continuous.correlation.pearsonr(
            other_xr,
            base_xr,
            preserve_dims=preserve_dims,
        )
    )

    # If time is aggregated out, attach a scalar time coordinate with bounds
    # so plotting can display the aggregated period in the title.
    try:
        if not scores_cube.coords("time"):
            base_time = base.coord("time")
            time_vals = (
                base_time.bounds.flatten()
                if base_time.has_bounds()
                else base_time.points
            )
            t_start = float(time_vals[0])
            t_end = float(time_vals[-1])
            t_mid = 0.5 * (t_start + t_end)

            scores_cube.add_aux_coord(
                iris.coords.AuxCoord(
                    t_mid,
                    standard_name=base_time.standard_name,
                    long_name=base_time.long_name,
                    var_name=base_time.var_name,
                    units=base_time.units,
                    bounds=np.array([t_start, t_end]),
                    attributes=base_time.attributes.copy(),
                )
            )
    except iris.exceptions.CoordinateNotFoundError:
        pass

    scores_cube.rename(f"Pearson_Correlation_of_{base.name()}")
    return scores_cube


def scores_crps_for_ensemble(
    cubes: Cube | CubeList, method: str = "ecdf", control_member: int = 0
) -> iris.Constraint:
    r"""Calculate the CRPS for an ensemble.

    Acts as a wrapper around the crps_for_ensemble from ``scores`` ([scoresa]_, [scoresb]_).

    Lower CRPS values are better (implies experiment distribution is closer to control distribution/observations),
    larger values are worse (implies distributions are dissimilar).
    It is applicable across time and spatial scales as the focus is on the distribution of the values.
    Default method is ecdf.  ecdf is exact value from the empirical distributions,
    whereas fair produces an approximated value based on a random sample of the underlying distribution.

    See [CRPS]_ for further information.

    Parameters
    ----------
    cubes: iris.cube.Cube
        A Cube containing ensembles data

    Returns
    -------
    crps: iris.cube.Cube
        A cube containing the crps between the ensemble members and the control
    """
    if control_member != 0:
        logger.warning("control member is usual 0")

    if control_member not in cubes.coords("realization")[0].points:
        new_control_member = cubes.coords("realization")[0].points[0]
        logger.warning(
            f"control member value {control_member} out of bounds, defaulting to control member={new_control_member}"
        )
        control_member = new_control_member

    if cubes.coord("time").shape[0] == 1:
        raise ValueError("Cube has only one time point.")

    if cubes.coord("realization").shape[0] < 3:
        raise ValueError("Cube should have one control member and at least two members")

    ctrl = cubes.extract(generate_realization_constraint([control_member]))
    ens_mem = cubes.extract(
        generate_remove_single_ensemble_member_constraint(control_member)
    )

    # Realising the data in advance provides a large speedup
    _ = ctrl.data
    _ = ens_mem.data
    del _

    ctrl = xr.DataArray.from_iris(ctrl)
    ens_mem = xr.DataArray.from_iris(ens_mem)

    crps = xr.DataArray.to_iris(
        scores.probability.crps_for_ensemble(
            ens_mem,
            ctrl,
            ensemble_member_dim="realization",
            method=method,
            preserve_dims="time",
        )
    )

    crps.rename(f"CRPS_of_{cubes[0].name()}")
    _realization_callback(crps)
    return crps


def scores_pod_model_obs(
    cubes: CubeList,
    preserved_coordinates: list[str] | str | None,
    threshold: str,
    op_func: str,
):
    r"""
    Compute the Probability of Detection (POD) score using Scores ([scoresa]_ [scoresb]_).

    Parameters
    ----------
    cubes: iris.cube.CubeList
        An iris cubelist containing model(s) and an observation cube.
    preserved_coordinates: list | str | None
        An object containing which coordinates to preserve in the computation. For example, if cubes contain shape time, point location,
        then preserving coordinate 'time' will produce a probability of detection score for each timeslice (shape time). If None,
        then it will return a single value score for all times/point locations.
    threshold: str
        A str containing the threshold to use to generate the binary masks, which subsequently gets turned to a float (but passed as str around the recipe templating).
    op_func: str
        A string either containing 'lt' for less than or 'gt for greater than, to determine how the threshold is applied to the data
        to generate the mask.

    Returns
    -------
    cube: iris.cube
        An iris cube, containing the probability of detection score for further plotting.

    Notes
    -----
    The probability of detection calculates the proportion of observed events that meet a threshold that were correctly forecast by the model.
    For example, if threshold is 290K and op_func is gt (greater than), and at some station a temperature was recorded as 292K and the model produced
    295k, that would be a positive hit. It does not take into account how far above/below a threshold a model forecasts.

    It is calculated as .. math:: POD = \frac{true positives}{true positives + false negatives}

    It is equivalent to the hit rate. Note if there are no events that meet the threshold in model and observations, a POD of zero is returned.

    POD produces a range of 0 to 1, where 1 is a perfect score.
    """
    # Split out model(s) and obs
    models = CubeList()
    for c in cubes:
        if "observed" in c.long_name:
            observed = c
        else:
            models.append(c)

    # Setup cubelist to store results
    scores_results = iris.cube.CubeList()

    # Setup operators greater than, less than.
    ops = {
        "gt": operator.gt,
        "lt": operator.lt,
    }

    try:
        op = ops[op_func]
    except KeyError as err:
        raise ValueError(f"Operator {op_func} not supported.") from err

    for model in models:
        # Convert obs cubes to xarray and resolve preserved dimensions.
        other_xr = xr.DataArray.from_iris(model)
        base_xr = xr.DataArray.from_iris(observed)
        preserve_dims = _resolve_preserve_dims(
            observed, other_xr, preserved_coordinates
        )

        # Create event operator object using threshold and operator direction.
        event_operator = scores.categorical.ThresholdEventOperator(
            default_event_threshold=float(threshold), default_op_fn=op
        )

        # Generate binary fields using the event operator.
        forecast_binary, observed_binary = event_operator.make_event_tables(
            other_xr, base_xr
        )

        # Create binary contigency manager, as per Scores API, using transform to preserve preserve_dims
        contingency_manager = scores.categorical.BinaryContingencyManager(
            forecast_binary, observed_binary
        ).transform(preserve_dims=preserve_dims)

        # Get POD from the contigency manager, and convert back to an iris cube.
        scores_cube = xr.DataArray.to_iris(
            contingency_manager.probability_of_detection()
        )

        # Rename cube so it plots correctly alongside correcting cube units.
        scores_cube.rename(
            f"Probability_Of_Detection_{op_func}_{threshold}_{observed.name()}"
        )
        scores_cube.units = "1"
        scores_cube.attributes["model_name"] = model.attributes["model_name"]

        scores_results.append(scores_cube)

    return scores_results
