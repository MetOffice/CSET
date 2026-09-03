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
import iris.coords
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


def scores_rmse(
    cubes: CubeList,
    preserved_coordinates: list[str] | str | None = None,
) -> CubeList:
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
    scores_cubelist: iris.cube.CubeList
        A cubelist containing the RMSE between the base and other cube.
    """
    scores_cubelist = CubeList()

    base, others = _split_base_and_other(cubes)

    for other in others:

        scores_cube = _make_scores_cube(base, other, "rmse", preserved_coordinates)

        scores_cube.rename(f"RMSE_of_{base.name()}")
        scores_cubelist.append(scores_cube)

    return scores_cubelist[0] if len(scores_cubelist) == 1 else scores_cubelist


def scores_mae(
    cubes: CubeList,
    preserved_coordinates: list[str] | str | None = None,
) -> CubeList:
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
    scores_cubelist: iris.cube.CubeList
        A cubelist containing the MAE between the base and other cube(s).
    """
    scores_cubelist = CubeList()
    base, others = _split_base_and_other(cubes)

    for other in others:

        scores_cube = _make_scores_cube(base, other, "mae", preserved_coordinates)

        scores_cube.rename(f"MAE_of_{base.name()}")
        scores_cubelist.append(scores_cube)
        model_name = other.attributes["model_name"]
        scores_cube.attributes["model_name"] = model_name

    return scores_cubelist[0] if len(scores_cubelist) == 1 else scores_cubelist


def scores_additive_bias(
    cubes: CubeList,
    preserved_coordinates: list[str] | str | None = None,
) -> CubeList:
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
    scores_cubelist: iris.cube.CubeList
        A cubelist containing the ME between the base and other cube(s).
    """
    scores_cubelist = CubeList()
    base, others = _split_base_and_other(cubes)

    for other in others:

        scores_cube = _make_scores_cube(
            base, other, "additive_bias", preserved_coordinates
        )

        scores_cubelist.append(scores_cube)

    return scores_cubelist[0] if len(scores_cubelist) == 1 else scores_cubelist


def scores_correlation_pearsonr(
    cubes: CubeList,
    preserved_coordinates: list[str] | str | None = None,
) -> CubeList:
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
    scores_cubelist: iris.cube.CubeList
        A cubelist containing the PC between the base and other cube(s).
    """
    scores_cubelist = CubeList()
    base, others = _split_base_and_other(cubes)

    for other in others:

        scores_cube = _make_scores_cube(
            base, other, "pearson_correlation", preserved_coordinates
        )

        scores_cubelist.append(scores_cube)

    return scores_cubelist[0] if len(scores_cubelist) == 1 else scores_cubelist


def scores_crps_for_ensemble(
    cubes: Cube | CubeList, method: str = "ecdf", control_member: int = 0
) -> Cube:
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

    method: str ["ecfd" or "fair"]
        Determines the method to use for calculating the CRPS.  Defaults to "ecdf".

    control_member: int
        What the realisation the control member of the ensemble is.  Defaults to 0. Sometimes this is 1.

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


def _scores_categorical_metric(
    cubes: CubeList,
    preserved_coordinates: list[str] | str | None,
    threshold: str,
    op_func: str,
    metric: str,
) -> CubeList:
    """
    Prepare cubes for computing categorical metrics using Scores.

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
    metric: str
        The scores metric to compute.

    Returns
    -------
    scores_results: iris.cube.CubeList
        An iris cubelist, containing the scores metric for each model for further plotting.

    """
    # Split obs/models
    models = CubeList()
    for c in cubes:
        if "observed" in c.long_name:
            observed = c
        else:
            models.append(c)

    ops = {
        "gt": operator.gt,
        "lt": operator.lt,
    }

    # Check if this exists.
    try:
        op = ops[op_func]
    except KeyError as err:
        raise ValueError(f"Operator {op_func} not supported.") from err

    scores_results = CubeList()

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

        # Compute required categorical score.
        if metric == "pod":
            result = contingency_manager.probability_of_detection()
            name = "Probability_Of_Detection"

        elif metric == "ets":
            result = contingency_manager.equitable_threat_score()
            name = "Equitable_Threat_Score"

        elif metric == "fb":
            result = contingency_manager.frequency_bias()
            name = "Frequency_Bias"

        elif metric == "pfd":
            result = contingency_manager.probability_of_false_detection()
            name = "Probability_Of_False_Detection"

        else:
            raise ValueError(f"Unknown metric {metric}")

        scores_cube = xr.DataArray.to_iris(result)

        scores_cube.rename(f"{name}_{op_func}_{threshold}_{observed.name()}")
        scores_cube.units = "1"
        scores_cube.attributes["model_name"] = model.attributes["model_name"]

        scores_results.append(scores_cube)

    return scores_results


def scores_pod(
    cubes,
    preserved_coordinates,
    threshold,
    op_func,
) -> CubeList:
    r"""
    Compute the Probability of Detection (POD) score using Scores ([scoresa]_ [scoresb]_).

    Parameters
    ----------
    cubes: iris.cube.CubeList
        An iris cubelist containing model(s) and an observation cube.
    preserved_coordinates: list | str | None
        An object containing which coordinates to preserve in the computation. For example, if cubes contain shape time, point location,
        then preserving coordinate 'time' will produce the equitable threat score for each timeslice (shape time). If None,
        then it will return a single value score for all times/point locations.
    threshold: str
        A str containing the threshold to use to generate the binary masks, which subsequently gets turned to a float (but passed as str around the recipe templating).
    op_func: str
        A string either containing 'lt' for less than or 'gt for greater than, to determine how the threshold is applied to the data
        to generate the mask.

    Returns
    -------
    iris.cube.CubeList
        An iris cubelist, containing the probability of detection score for each model for further plotting.


    Notes
    -----
    The probability of detection calculates the proportion of observed events that meet a threshold that were correctly forecast by the model.
    For example, if threshold is 290K and op_func is gt (greater than), and at some station a temperature was recorded as 292K and the model produced
    295k, that would be a positive hit. It does not take into account how far above/below a threshold a model forecasts.

    It is calculated as .. math:: POD = \frac{true positives}{true positives + false negatives}

    It is equivalent to the hit rate. Note if there are no events that meet the threshold in model and observations, a POD of zero is returned.

    POD produces a range of 0 to 1, where 1 is a perfect score.
    """
    return _scores_categorical_metric(
        cubes,
        preserved_coordinates,
        threshold,
        op_func,
        "pod",
    )


def scores_ets(
    cubes: CubeList,
    preserved_coordinates: list[str] | str | None,
    threshold: str,
    op_func: str,
) -> CubeList:
    r"""
    Compute the Equitable Threat Score (ETS) score using Scores ([scoresa]_ [scoresb]_).

    Parameters
    ----------
    cubes: iris.cube.CubeList
        An iris cubelist containing model(s) and an observation cube.
    preserved_coordinates: list | str | None
        An object containing which coordinates to preserve in the computation. For example, if cubes contain shape time, point location,
        then preserving coordinate 'time' will produce the equitable threat score for each timeslice (shape time). If None,
        then it will return a single value score for all times/point locations.
    threshold: str
        A str containing the threshold to use to generate the binary masks, which subsequently gets turned to a float (but passed as str around the recipe templating).
    op_func: str
        A string either containing 'lt' for less than or 'gt for greater than, to determine how the threshold is applied to the data
        to generate the mask.

    Returns
    -------
    iris.cube.CubeList
        An iris cubelist, containing the probability of detection score for each model for further plotting.

    Notes
    -----
    The Equitable Threat Score (ETS) evaluates the accuracy of forecasts for events that meet a specified threshold,
    hile accounting for correct forecasts that could occur purely by chance. Unlike the Probability of Detection (POD),
    ETS considers hits, misses, and false alarms, providing a more balanced assessment of forecast skill.

    For example, if the threshold is 290 K and op_func is gt (greater than), an observation of 292 K and a forecast of 295 K
    would be counted as a hit. ETS adjusts the total number of hits by removing the number of hits expected due to random chance.

    It is calculated as:

    .. math::

    ETS = \frac{hits - hits_{random}}
    {hits + misses + false\ alarms - hits_{random}}

    where

    hits_{random} = \frac{(hits + misses)(hits + false\ alarms)}{total count}

    ETS ranges from -1/3 to 1, where 1 indicates a perfect forecast, 0 indicates no skill beyond random chance, and negative values indicate worse than
    random chance.
    """
    return _scores_categorical_metric(
        cubes,
        preserved_coordinates,
        threshold,
        op_func,
        "ets",
    )


def scores_pfd(
    cubes: CubeList,
    preserved_coordinates: list[str] | str | None,
    threshold: str,
    op_func: str,
) -> CubeList:
    r"""
    Compute the Probability of False Detection (PFD) score using Scores ([scoresa]_ [scoresb]_).

    Parameters
    ----------
    cubes: iris.cube.CubeList
        An iris cubelist containing model(s) and an observation cube.
    preserved_coordinates: list | str | None
        An object containing which coordinates to preserve in the computation. For example, if cubes contain shape time, point location,
        then preserving coordinate 'time' will produce the probability of false detection score for each timeslice (shape time). If None,
        then it will return a single value score for all times/point locations.
    threshold: str
        A str containing the threshold to use to generate the binary masks, which subsequently gets turned to a float (but passed as str around the recipe templating).
    op_func: str
        A string either containing 'lt' for less than or 'gt' for greater than, to determine how the threshold is applied to the data
        to generate the mask.

    Returns
    -------
    iris.cube.CubeList
        An iris cubelist, containing the probability of false detection score for each model for further plotting.

    Notes
    -----
    The Probability of False Detection (PFD) measures the proportion of observed non-events
    that were incorrectly forecast as events. It is a measure of the false alarm rate and
    provides information on how often a forecast system predicts threshold exceedances when
    none actually occurred.

    For example, if the threshold is 290 K and op_func is gt (greater than), an observation
    of 288 K and a forecast of 295 K would be considered a false alarm, since the model
    predicted an event but the observed value did not exceed the threshold.

    It is calculated as:

    .. math::

    POFD = \frac{false\ alarms}
                 {false\ alarms + true\ negatives}

    where

    false alarms
        Number of occasions where an event was forecast but did not occur.

    true negatives
        Number of occasions where neither the forecast nor the observations
        indicated an event.

    PFD ranges from 0 to 1, where 0 indicates a perfect score with no false alarms,
    and 1 indicates that every observed non-event was incorrectly forecast as an event.

    Lower values are therefore better.
    """
    return _scores_categorical_metric(
        cubes,
        preserved_coordinates,
        threshold,
        op_func,
        "pfd",
    )


def scores_frequency_bias(
    cubes: CubeList,
    preserved_coordinates: list[str] | str | None,
    threshold: str,
    op_func: str,
) -> CubeList:
    r"""
    Compute the Frequency Bias (FB) score using Scores ([scoresa]_ [scoresb]_).

    Parameters
    ----------
    cubes: iris.cube.CubeList
        An iris cubelist containing model(s) and an observation cube.
    preserved_coordinates: list | str | None
        An object containing which coordinates to preserve in the computation. For example, if cubes contain shape time, point location,
        then preserving coordinate 'time' will produce the frequency bias score for each timeslice (shape time). If None,
        then it will return a single value score for all times/point locations.
    threshold: str
        A str containing the threshold to use to generate the binary masks, which subsequently gets turned to a float (but passed as str around the recipe templating).
    op_func: str
        A string either containing 'lt' for less than or 'gt' for greater than, to determine how the threshold is applied to the data
        to generate the mask.

    Returns
    -------
    iris.cube.CubeList
        An iris cube, containing the frequency bias score for each model for further plotting.

    Notes
    -----
    The Frequency Bias (FB) measures whether a forecasting system predicts an
    event too frequently or too infrequently compared to observations. Unlike
    metrics such as the Probability of Detection (POD) or Equitable Threat Score (ETS),
    Frequency Bias does not assess the accuracy of forecast locations or timings,
    only the overall frequency with which events are forecast.

    For example, if the threshold is 290 K and op_func is gt (greater than), and
    events exceeding this threshold are forecast twice as often as they are observed,
    the frequency bias would be approximately 2. Conversely, if events are forecast
    only half as often as they occur, the frequency bias would be approximately 0.5.

    It is calculated as:

    .. math::

    Frequency\ Bias = \frac{hits + false\ alarms}
                            {hits + misses}

    where

    hits
        Number of occasions where an event was forecast and observed.

    false alarms
        Number of occasions where an event was forecast but not observed.

    misses
        Number of occasions where an event was observed but not forecast.

    Frequency Bias ranges from 0 to infinity, where:

    * 1 indicates the forecast predicts events at the correct frequency.
    * Greater than 1 indicates overforecasting of events.
    * Less than 1 indicates underforecasting of events.

    A perfect frequency bias score is therefore 1, although a value of 1 does not
    necessarily imply a skillful forecast, as hits and false alarms may compensate
    for one another.
    """
    return _scores_categorical_metric(
        cubes,
        preserved_coordinates,
        threshold,
        op_func,
        "fb",
    )


def _make_scores_cube(
    base: Cube, other: Cube, metric: str, preserved_coordinates: list[str]
) -> Cube:
    r"""Make the scores cube using the given scores metric.

    Parameters
    ----------
    base: iris.cube.Cube
        The cube from the "analysis" or observed cube.
    other: iris.cube.Cube
        The cube from the model.

    metric: str
        The scores metric to compute.

    preserved_coordinates: list[str]
        The list of preserved coordinates given by a user.

    Returns
    -------
    scores_cube: iris.cube.Cube
        The cube containing the calculated scores metric.


    """

    #base, other = _process_cubes_for_verification(base, other)

    other_xr = xr.DataArray.from_iris(other)
    base_xr = xr.DataArray.from_iris(base)
    preserve_dims = _resolve_preserve_dims(other, other_xr, preserved_coordinates)

    # Scores operates on xarray data arrays, so we transform the iris cube into an array,
    # apply scores, and then transform it back.
    if metric == "rmse":
        scores_cube = xr.DataArray.to_iris(
            scores.continuous.rmse(other_xr, base_xr, preserve_dims=preserve_dims)
        )
        scores_cube.rename(f"RMSE_of_{base.name()}")
    elif metric == "mae":
        scores_cube = xr.DataArray.to_iris(
            scores.continuous.mae(other_xr, base_xr, preserve_dims=preserve_dims)
        )
        scores_cube.rename(f"MAE_of_{base.name()}")
    elif metric == "additive_bias":
        scores_cube = xr.DataArray.to_iris(
            scores.continuous.additive_bias(
                other_xr, base_xr, preserve_dims=preserve_dims
            )
        )
        scores_cube.rename(f"Additive_Bias_of_{base.name()}")
    elif metric == "pearson_correlation":
        scores_cube = xr.DataArray.to_iris(
            scores.continuous.correlation.pearsonr(
                other_xr, base_xr, preserve_dims=preserve_dims
            )
        )
        scores_cube.rename(f"Pearson_Correlation_of_{base.name()}")
    else:
        raise ValueError(f"Scores Unknown metric: {metric}")
    breakpoint()
    _attach_scaler_time_coord_maybe(scores_cube, base)
    model_name = other.attributes["model_name"]
    scores_cube.attributes["model_name"] = model_name
    return scores_cube


def _sort_cube_into_base_and_other(cubes: CubeList) -> tuple[Cube, CubeList]:
    r"""Sorts cube into base and other models.

    Parameters
    ----------
    cubes: iris.cube.CubeList
        A CubeList of multiple cubes.  One base cube and other model cubes.

    Returns
    -------
    base: iris.cube.Cube
        The cube from the "analysis" or observed cube in the same format as the other model.
    others: iris.cube.CubeList
        The cube list of containing the cube(s) from the model in the same format as the base model.

    """
    base: Cube = cubes.extract_cube(iris.AttributeConstraint(cset_comparison_base=1))
    others: CubeList = cubes.extract(
        iris.Constraint(
            cube_func=lambda cube: "cset_comparison_base" not in cube.attributes
        )
    )

    return base, others


def _ensure_increasing_pressure_coordinates(cubes: CubeList) -> CubeList:
    r"""Ensure the pressure coordinate is increasing.

    Parameters
    ----------
    cubes: iris.cube.CubeList
        A CubeList of n cubes

    Returns
    -------
    Cubes: iris.cube.CubeList
        The original cube list but where each cube is ensured to have an increasing pressure coordinate.
    """
    for cube in cubes:
        try:
            if len(cube.coord("pressure").points) > 2 and not is_increasing(
                cube.coord("pressure").points
            ):
                reverse(cube, "pressure")

        except iris.exceptions.CoordinateNotFoundError:
            pass

def _process_cubes_for_verification(base: Cube, other: Cube) -> tuple[Cube, Cube]:
    r"""Prepare cubes ready for verification in scores.

    Parameters
    ----------
    base: iris.cube.Cube
        The cube from the "analysis" or observed cube.
    other: iris.cube.Cube
        The cube from the model.

    Returns
    -------
    base: iris.cube.Cube
        The cube from the "analysis" or observed cube in the same format as the other model.
    other: iris.cube.Cube
        The cube from the model in the same format as the base model.

    Notes
    -----
    This operator is used for sorting the data into the correct format. It
    is likely going to need to be refactored out of CSET and perhaps moved into
    `CSET._utils` given common code between here and `misc.difference`.
    """
    # Set cubes into correct format using code from difference operator

    # Extract just common time points.
    other_model_name = other.attributes["model_name"]

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

    other.attributes["model_name"] = other_model_name
    logger.debug("Base: %s\nOther: %s", base, other)

    return base, other


def _resolve_preserve_dims(
    cube: Cube,
    data_array: xr.DataArray,
    preserved_coordinates: list[str] | str | None,
) -> list[str] | None:
    r"""Resolve preserve coordinates to xarray dimension names.

    The ``scores`` package expects preserve dimensions to match xarray
    dimension names. In Iris data, commonly used coordinates such as ``time``
    may be auxiliary coordinates attached to a differently named dimension
    (e.g. ``dim0``). This helper maps coordinate names to their underlying
    dimension names and helps to convert from iris to xarray coordinate dimension names.

    Parameters
    ----------
    cube: iris.cube.Cube
        The ccomparison model cube.
    data_array: xr.DataArray
        The comparison model cube, but in xarray format.
    preserved_coordinates: list[str]
        The list of preserved coordinates given by a user.


    Returns
    -------
    preserved_dims : list[str]
        List of preserved dimension names in xarray convention.

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


def _attach_scaler_time_coord_maybe(scores_cube: Cube, base: Cube) -> None:
    r"""Attaches scaler time coordinate if time is aggregated out.

    In place function that attaches a scaler time coordinate to scores_cube
    if time is aggregated out so plotting can display the aggregated period in the title.

    Parameters
    ----------
    scores_cube: iris.cube.Cube
        The calculated scores cube.
    base: iris.cube.Cube
        The cube from the "analysis" or observed cube.

    Returns
    -------
    None

    """
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


def _split_base_and_other(cubes: CubeList):
    r"""Split the cube into base and other cubes.

    Split depends on whether there
    is an observed cube in the cubes.  If there is an observed cube,
    then 'base' is the observed cube, if not then 'base' is the comparison
    model cube.

    Parameters
    ----------
    cubes: iris.cube.CubeList
        Cubes to split into base and other cubes.

    Returns
    -------
    tuple
        A tuple containing a base cube, and other cube/cubelist.

    """
    obs_cube = [cb for cb in cubes if "observed" in (cb.long_name or "")]
    if obs_cube:
        if len(obs_cube) > 1:
            raise ValueError(
                f"Expected exactly one 'observed' cube, found {len(obs_cube)}"
            )
        base = obs_cube[0]
        others = CubeList(cb for cb in cubes if cb is not base)
        return base, others

    return _sort_cube_into_base_and_other(cubes)


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
    scores_cubelist: iris.cube.CubeList
        A cubelist containing the RMSE between the models and observation cube(s).
    """
    rmse_cubes = CubeList()
    model_list = CubeList()

    # Separate observations and models
    for cb in cubes:
        if "observed" in cb.long_name:
            observed = cb
        else:
            model_list.append(cb)

    for model in model_list:

        frt_coord = model.coord("forecast_reference_time")

        # Multiple forecast reference times
        if (
            model.coord_dims("forecast_reference_time")
            and frt_coord.shape[0] > 1
        ):

            obs_slices = list(
                observed.slices_over("forecast_reference_time")
            )

            model_slices = list(
                model.slices_over("forecast_reference_time")
            )

            for obs_slice, model_slice in zip(
                obs_slices,
                model_slices,
                strict=True,
            ):

                input_cubelist = CubeList([
                    obs_slice,
                    model_slice,
                ])

                rmse = scores_rmse(
                    input_cubelist,
                    preserved_coordinates,
                )

                rmse.attributes["model_name"] = (
                    model.attributes["model_name"]
                )

                # Preserve the forecast_reference_time value
                if not rmse.coords("forecast_reference_time"):
                    rmse.add_aux_coord(
                        model_slice.coord(
                            "forecast_reference_time"
                        ).copy()
                    )

                if rmse.coords("time"):
                    for coord in rmse.coords("time"):
                        rmse.remove_coord(coord)

                rmse_cubes.append(rmse)

        # Single forecast reference time
        else:

            input_cubelist = CubeList([
                observed,
                model,
            ])

            rmse = scores_rmse(
                input_cubelist,
                preserved_coordinates,
            )

            rmse.attributes["model_name"] = (
                model.attributes["model_name"]
            )

            rmse_cubes.append(rmse)


    if len(rmse_cubes) > 1:
        return rmse_cubes.merge()
    else:
        return rmse_cubes
