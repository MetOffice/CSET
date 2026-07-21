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

import iris
import iris.exceptions
import numpy as np
import scores
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
            if len(cube.coord("pressure").points) > 2:
                if not is_increasing(cube.coord("pressure").points):
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
        logging.debug(
            "Linear regridding base cube to other grid to compute differences"
        )
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
    logging.debug("Base: %s\nOther: %s", base, other)

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


def scores_rmse(cubes: CubeList, preserved_coordinates: list[str] | str | None = None):
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
        The coordinates that you wish to preserve in the calculaiton of the
        RMSE. For example if you want a map of each time you can preserve
        ["time","grid_latitude", "grid_longitude"] or if you want a time series
        you can preserve ["time"], if you want to collapse to a single value
        use `None`. The default is `None`.

    Returns
    -------
    scores_cube: iris.cube.Cube
        A cube containing the RMSE between the base and other cube.

    References
    ----------
    .. [scoresa] Leeuwenburg, T., Loveday, N., Ebert, E. E., Cook, H.,
        Khanarmuei, M., Taggart, R. J., Ramanathan, N., Carroll, M., Chong, S.,
        Griffiths, A., & Sharples, J. (2024) "scores: A Python package for
        verifying and evaluating models and predictions with xarray". Journal
        of Open Source Software, vol. 9, 6889. doi: 10.21105/joss.06889

    .. [scoresb] Leeuwenburg, T., Loveday, N., Ramanathan, N., Chong, S.,
        Taggart, R. J., Shrestha, D., Khanarmuei, M., Cook, H., Bluett, L., Ebert,
        E. E., Carroll, M., Trotta, B., Bishop, S., Squire, D. T., Griffiths, A.,
        Pagano, T. C., Fisher, A. J., Mandelbaum, T., Jinghan, F., … Smallwood, J.
        (2026) "scores: Metrics for the verification, evaluation and optimisation of
        forecasts, predictions or models (2.5.0)". Zenodo. doi: 10.5281/zenodo.18638494
    """
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

    References
    ----------
    .. [scoresa] Leeuwenburg, T., Loveday, N., Ebert, E. E., Cook, H.,
        Khanarmuei, M., Taggart, R. J., Ramanathan, N., Carroll, M., Chong, S.,
        Griffiths, A., & Sharples, J. (2024) "scores: A Python package for
        verifying and evaluating models and predictions with xarray". Journal
        of Open Source Software, vol. 9, 6889. doi: 10.21105/joss.06889

    .. [scoresb] Leeuwenburg, T., Loveday, N., Ramanathan, N., Chong, S.,
        Taggart, R. J., Shrestha, D., Khanarmuei, M., Cook, H., Bluett, L., Ebert,
        E. E., Carroll, M., Trotta, B., Bishop, S., Squire, D. T., Griffiths, A.,
        Pagano, T. C., Fisher, A. J., Mandelbaum, T., Jinghan, F., … Smallwood, J.
        (2026) "scores: Metrics for the verification, evaluation and optimisation of
        forecasts, predictions or models (2.5.0)". Zenodo. doi: 10.5281/zenodo.18638494
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

    References
    ----------
    .. [scoresa] Leeuwenburg, T., Loveday, N., Ebert, E. E., Cook, H.,
        Khanarmuei, M., Taggart, R. J., Ramanathan, N., Carroll, M., Chong, S.,
        Griffiths, A., & Sharples, J. (2024) "scores: A Python package for
        verifying and evaluating models and predictions with xarray". Journal
        of Open Source Software, vol. 9, 6889. doi: 10.21105/joss.06889

    .. [scoresb] Leeuwenburg, T., Loveday, N., Ramanathan, N., Chong, S.,
        Taggart, R. J., Shrestha, D., Khanarmuei, M., Cook, H., Bluett, L., Ebert,
        E. E., Carroll, M., Trotta, B., Bishop, S., Squire, D. T., Griffiths, A.,
        Pagano, T. C., Fisher, A. J., Mandelbaum, T., Jinghan, F., … Smallwood, J.
        (2026) "scores: Metrics for the verification, evaluation and optimisation of
        forecasts, predictions or models (2.5.0)". Zenodo. doi: 10.5281/zenodo.18638494
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
        The coordinates that you wish to preserve in the calculaiton of the
        PC. For example if you want a map of each time you can preserve
        ["time","grid_latitude", "grid_longitude"] or if you want a time series
        you can preserve ["time"], if you want to collapse to a single value
        use `None`. The default is `None`.

    Returns
    -------
    scores_cube: iris.cube.Cube
        A cube containing the PC between the base and other cube.

    References
    ----------
    .. [scoresa] Leeuwenburg, T., Loveday, N., Ebert, E. E., Cook, H.,
        Khanarmuei, M., Taggart, R. J., Ramanathan, N., Carroll, M., Chong, S.,
        Griffiths, A., & Sharples, J. (2024) "scores: A Python package for
        verifying and evaluating models and predictions with xarray". Journal
        of Open Source Software, vol. 9, 6889. doi: 10.21105/joss.06889

    .. [scoresb] Leeuwenburg, T., Loveday, N., Ramanathan, N., Chong, S.,
        Taggart, R. J., Shrestha, D., Khanarmuei, M., Cook, H., Bluett, L., Ebert,
        E. E., Carroll, M., Trotta, B., Bishop, S., Squire, D. T., Griffiths, A.,
        Pagano, T. C., Fisher, A. J., Mandelbaum, T., Jinghan, F., … Smallwood, J.
        (2026) "scores: Metrics for the verification, evaluation and optimisation of
        forecasts, predictions or models (2.5.0)". Zenodo. doi: 10.5281/zenodo.18638494
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

    Acts as a wrapper around the crps_for_ensemble from ``scores`` ([scores_a]_, [scores_b]_).

    Lower CRPS values are better (implies experiment distribution is closer to control distribution/observations),
    larger values are worse (implies distributions are dissimilar).
    It is applicable across time and spatial scales as the focus is on the distribution of the values.
    Default method is ecdf.  ecdf is exact value from the empirical distributions,
    whereas fair produces an approximated value based on a random sample of the underlying distribution.

    See [CRPS] for further information.

    Parameters
    ----------
    cubes: iris.cube.Cube
        A Cube containing ensembles data

    Returns
    -------
    crps: iris.cube.Cube
        A cube containing the crps between the ensemble members and the control

    References
    ----------
    .. [scores_a] Leeuwenburg, T., Loveday, N., Ebert, E. E., Cook, H.,
        Khanarmuei, M., Taggart, R. J., Ramanathan, N., Carroll, M., Chong, S.,
        Griffiths, A., & Sharples, J. (2024) "scores: A Python package for
        verifying and evaluating models and predictions with xarray". Journal
        of Open Source Software, vol. 9, 6889. doi: 10.21105/joss.06889

    .. [scores_b] Leeuwenburg, T., Loveday, N., Ramanathan, N., Chong, S.,
        Taggart, R. J., Shrestha, D., Khanarmuei, M., Cook, H., Bluett, L., Ebert,
        E. E., Carroll, M., Trotta, B., Bishop, S., Squire, D. T., Griffiths, A.,
        Pagano, T. C., Fisher, A. J., Mandelbaum, T., Jinghan, F., … Smallwood, J.
        (2026) "scores: Metrics for the verification, evaluation and optimisation of
        forecasts, predictions or models (2.5.0)". Zenodo. doi: 10.5281/zenodo.18638494

    .. [CRPS]
        Hersbach, H., 2000: Decomposition of the Continuous Ranked
        Probability Score for Ensemble Prediction Systems. Wea.
        Forecasting, 15, 559–570, https://doi.org/10.1175/1520-0434(2000)015<0559:DOTCRP>2.0.CO;2.
    """
    if control_member != 0:
        logging.warning("control member is usual 0")

    if control_member not in cubes.coords("realization")[0].points:
        new_control_member = cubes.coords("realization")[0].points[0]
        logging.warning(
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
