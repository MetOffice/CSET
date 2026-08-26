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
        base, other = _process_cubes_for_verification(base, other)

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
        base, other = _process_cubes_for_verification(base, other)

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
        base, other = _process_cubes_for_verification(base, other)

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
        base, other = _process_cubes_for_verification(base, other)

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
) -> iris.cube.CubeList:
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
) -> iris.cube.CubeList:
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
) -> iris.cube.CubeList:
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
) -> iris.cube.CubeList:
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
) -> iris.cube.CubeList:
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
