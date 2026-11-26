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

import iris
import numpy as np
from iris.cube import Cube

from CSET.operators._utils import _split_base_and_other


def bootstrap_significance(
    cubes,
    lower_percentile=5,
    upper_percentile=95,
    n_bootstrap=10000,
    seed=None,
    return_intervals=False,
):
    """
    Bootstrap significance test of the mean difference between models.

    Tests across forecast_reference_time, and test whether it is significantly different
    to zero. Can handle multiple models to be compared against the base model.

    Parameters
    ----------
    cubes: iris.cube.CubeList
        Containing both base cube and multiple other cubes, where cset_comparison_base
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
    sig_cube : iris.cube.CubeList
        Boolean significance mask list of cubes for each model.

    sig_vals : tuple of CubeLists
        if return_intervals is True.
        tuple containing iris cubelists containing the values of the percentiles and mean,
    """
    # Split out model base and test cube.
    base_cube, other_cubes = _split_base_and_other(cubes)

    sig_cubes = iris.cube.CubeList()
    if return_intervals:
        lowerint_cubes = iris.cube.CubeList()
        upperint_cubes = iris.cube.CubeList()
        mean_cubes = iris.cube.CubeList()

    # Generate seed for reproducibility
    rng = np.random.default_rng(seed)

    # Check for silly vals.
    if not (0 <= lower_percentile < upper_percentile <= 100):
        raise ValueError(
            "Percentiles must satisfy 0 <= lower_percentile < upper_percentile <= 100."
        )

    # Iterate over all test cubes
    for test_cube in other_cubes:
        # Defensive checks to ensure same shape.
        if base_cube.shape != test_cube.shape:
            raise ValueError("Input cubes must have identical shapes.")

        # Check there is a forecast_reference_time present as a coord_dim.
        try:
            frt_dim = test_cube.coord_dims("forecast_reference_time")[0]
        except IndexError as err:
            raise iris.exceptions.CoordinateNotFoundError(
                "Input cubes must contain a 'forecast_reference_time' coordinate."
            ) from err

        # Can't do a significance test if the dimension size is less than 2 (would
        # be continually resampling the same forecast).
        if test_cube.shape[frt_dim] < 2:
            raise ValueError("Need at least two forecast_reference_times.")

        # Compute differences between the two models for all points.
        delta = test_cube.data - base_cube.data

        # Ensure that forecast_reference_time is the lead dimension.
        delta = np.moveaxis(
            delta,
            frt_dim,
            0,
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

        # Compute lower, upper percentiles and mean differences.
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

        # Significant if lower confidence interval greater than 0 and upper confidence interval less than zero.
        # i.e. zero cannot lie within the confidence interval.
        significance = (lower_ci > 0) | (upper_ci < 0)

        # Extract all other coordinates other than the frt dim and reconstruct a
        # cube to store significance data in.
        dim_coords_and_dims = []

        # For each dim coord index, calculate where corodinate should live
        # after removing forecast reference time.
        for coord in test_cube.dim_coords:
            dim = test_cube.coord_dims(coord)[0]

            if dim == frt_dim:
                continue

            new_dim = dim if dim < frt_dim else dim - 1

            dim_coords_and_dims.append((coord.copy(), new_dim))

        # Add attributes
        attributes = base_cube.attributes.copy()

        # Could be useful for later plotting (legend for error bars).
        attributes.update(
            {
                "bootstrap_n_samples": n_bootstrap,
                "bootstrap_lower_percentile": lower_percentile,
                "bootstrap_upper_percentile": upper_percentile,
            }
        )

        # Create new significance cube.
        sig_cube = Cube(
            significance,
            long_name=(
                f"bootstrap_significance_{test_cube.name()}_minus_{base_cube.name()}"
            ),
            units="1",
            attributes=attributes,
            dim_coords_and_dims=dim_coords_and_dims,
        )

        sig_cubes.append(sig_cube)

        if return_intervals:
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

            lowerint_cubes.append(lower_cube)
            upperint_cubes.append(upper_cube)
            mean_cubes.append(mean_cube)

    if return_intervals:
        return sig_cubes, lowerint_cubes, upperint_cubes, mean_cubes
    else:
        return sig_cubes
