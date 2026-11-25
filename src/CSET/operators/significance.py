# © Crown copyright, Met Office (2022-2024) and CSET contributors.
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

"""Operators to compute statistical significance."""

import logging
import numpy as np
from iris.cube import Cube
from CSET.operators.scoreswrappers import _split_base_and_other

def bootstrap_significance(
    cubes,
    lower_percentile=5,
    upper_percentile=95,
    n_bootstrap=10000,
    seed=None,
    return_intervals=False):
    """
    Bootstrap significance test of the mean difference between two cubes
    across forecast_reference_time, and test whether it is significantly different
    to zero.

    Parameters
    ----------
    cubes: iris.cube.CubeList
        Containing both base cube and other cube, where cset_comparison_base
        will be used to split the cubes.

    lower_percentile : float
        Lower confidence interval percentile.

    upper_percentile : float
        Upper confidence interval percentile.

    n_bootstrap : int
        Number of bootstrap resamples.

    seed : int, optional
        Random seed, for reproducing results (used for testing)

    return_intervals : bool, optional
        If True also return lower, upper and mean cubes.

    Returns
    -------
    sig_cube : iris.cube.Cube
        Boolean significance mask.

    sig_vals : iris.cube.Cube, optional
        Iris cube containing the values of the percentiles and mean, if
        return_intervals is True.
    """

    # Split out model base and test cube.
    base_cube, other_cube = _split_base_and_other(cubes)

    # Defensive checks to ensure same shape.
    if base_cube.shape != other_cube.shape:
        raise ValueError(
            "Input cubes must have identical shapes."
        )

    # Check there is a forecast_reference_time present as a coord_dim.
    try:
        frt_dim = base_cube.coord_dims(
            "forecast_reference_time"
        )[0]
    except IndexError:
        raise ValueError(
            "Input cubes must contain a "
            "'forecast_reference_time' coordinate."
        )

    # Check for silly vals.
    if not (
    0 <= lower_percentile < upper_percentile <= 100):
        raise ValueError(
        "Percentiles must satisfy "
        "0 <= lower_percentile < upper_percentile <= 100."
    )

    # Can't do a significance test if the dimension size is less than 2 (would
    # be continually resampling the same forecast).
    if base_cube.shape[frt_dim] < 2:
        raise ValueError(
            "Need at least two forecast_reference_times."
        )

    # Generate seed for reproducibility
    rng = np.random.default_rng(seed)

    # Compute differences between the two models for all points.
    delta = other_cube.data - base_cube.data

    # Ensure that forecast_reference_time is the lead dimension.
    delta = np.moveaxis(
        delta,
        frt_dim,
        0,
    )

    # Tuple to set shape of output, excluding forecast_reference_time dimension.
    output_shape = delta.shape[1:]

    # Initialise empty cubes to store significance bool and percentiles/mean, if required.
    significance = np.zeros(
        output_shape,
        dtype=bool,
    )

    # Bootstrap indices. We know delta is order frt first, so we can use that to
    # find the size of the array.
    indices = rng.integers(
        0,
        delta.shape[0],
        size=(n_bootstrap, delta.shape[0]),
    )

    # Shape (n_bootstrap, n_frt, ...)
    resampled = delta[indices]

    # Shape:
    # (n_bootstrap, ...)
    bootstrap_means = np.mean(
        resampled,
        axis=1,
    )

    lower_ci = np.percentile(
        bootstrap_means,
        lower_percentile,
        axis=0,
    )

    upper_ci = np.percentile(
        bootstrap_means,
        upper_percentile,
        axis=0,
    )

    mean_diff = np.mean(
        delta,
        axis=0,
    )

    significance = (
        (lower_ci > 0)
        | (upper_ci < 0)
    )


    # Extract all other coordinates other than the frt dim and reconstruct a
    # cube to store signficance data in.
    dim_coords_and_dims = []

    for coord in base_cube.dim_coords:
        dim = base_cube.coord_dims(coord)[0]

        if dim == frt_dim:
            continue

        new_dim = dim if dim < frt_dim else dim - 1

        dim_coords_and_dims.append(
            (coord.copy(), new_dim)
        )

    # Add attributes
    attributes = base_cube.attributes.copy()

    attributes.update(
        {
            "bootstrap_n_samples": n_bootstrap,
            "bootstrap_lower_percentile": lower_percentile,
            "bootstrap_upper_percentile": upper_percentile,
        }
    )

    sig_cube = Cube(
        significance,
        long_name=(
            f"bootstrap_significance_"
            f"{other_cube.name()}_minus_"
            f"{base_cube.name()}"
        ),
        units="1",
        attributes=attributes,
        dim_coords_and_dims=dim_coords_and_dims,
    )

    if not return_intervals:
        return sig_cube

    lower_cube = sig_cube.copy(
        data=lower_ci,
    )
    lower_cube.rename("lower_confidence_limit")

    upper_cube = sig_cube.copy(
        data=upper_ci,
    )
    upper_cube.rename("upper_confidence_limit")

    mean_cube = sig_cube.copy(
        data=mean_diff,
    )
    mean_cube.rename("mean_difference")

    return (
        sig_cube,
        lower_cube,
        upper_cube,
        mean_cube,
    )
