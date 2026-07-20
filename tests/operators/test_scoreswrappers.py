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

"""Test miscellaneous operators."""

import datetime

import iris
import iris.analysis.calculus
import iris.coords
import iris.cube
import iris.exceptions
import numpy as np
import pytest
import scores
import scores.continuous
import scores.probability
import xarray as xr
from iris.util import reverse

from CSET.operators import scoreswrappers
from CSET.operators.constraints import (
    generate_realization_constraint,
    generate_remove_single_ensemble_member_constraint,
)


def test_scores_correlation_pearsonr(cube: iris.cube.Cube):
    """Test taking the Pearson correlation between two cubes."""
    # Data preparation.
    other_cube = cube.copy()
    del other_cube.attributes["cset_comparison_base"]
    cubes = iris.cube.CubeList([cube, other_cube])

    # Take difference.
    correlation_pearsonr_cube = scoreswrappers.scores_correlation_pearsonr(cubes)

    # As both cubes use the same data, check the Pearson correlation is one.
    assert isinstance(correlation_pearsonr_cube, iris.cube.Cube)
    assert np.allclose(
        correlation_pearsonr_cube.data,
        np.ones_like(correlation_pearsonr_cube.data),
        atol=1e-9,
    )
    assert correlation_pearsonr_cube.standard_name is None
    assert (
        correlation_pearsonr_cube.long_name == "Pearson_Correlation_of_air_temperature"
    )


def test_scores_additive_bias(cube: iris.cube.Cube):
    """Test taking the additive bias between two cubes."""
    # Data preparation.
    other_cube = cube.copy()
    del other_cube.attributes["cset_comparison_base"]
    cubes = iris.cube.CubeList([cube, other_cube])

    # Take difference.
    additive_bias_cube = scoreswrappers.scores_additive_bias(cubes)

    # As both cubes use the same data, check the additive bias is zero.
    assert isinstance(additive_bias_cube, iris.cube.Cube)
    assert np.allclose(
        additive_bias_cube.data, np.zeros_like(additive_bias_cube.data), atol=1e-9
    )
    assert additive_bias_cube.standard_name is None
    assert additive_bias_cube.long_name == "Additive_Bias_of_air_temperature"


def test_scores_mae(cube: iris.cube.Cube):
    """Test taking the mae between two cubes."""
    # Data preparation.
    other_cube = cube.copy()
    del other_cube.attributes["cset_comparison_base"]
    cubes = iris.cube.CubeList([cube, other_cube])

    # Take difference.
    mae_cube = scoreswrappers.scores_mae(cubes)

    # As both cubes use the same data, check the mae is zero.
    assert isinstance(mae_cube, iris.cube.Cube)
    assert np.allclose(mae_cube.data, np.zeros_like(mae_cube.data), atol=1e-9)
    assert mae_cube.standard_name is None
    assert mae_cube.long_name == "MAE_of_air_temperature"


def test_scores_rmse(cube: iris.cube.Cube):
    """Test taking the rmse between two cubes."""
    # Data preparation.
    other_cube = cube.copy()
    del other_cube.attributes["cset_comparison_base"]
    cubes = iris.cube.CubeList([cube, other_cube])

    # Take difference.
    rmse_cube = scoreswrappers.scores_rmse(cubes)

    # As both cubes use the same data, check the rmse is zero.
    assert isinstance(rmse_cube, iris.cube.Cube)
    assert np.allclose(rmse_cube.data, np.zeros_like(rmse_cube.data), atol=1e-9)
    assert rmse_cube.standard_name is None
    assert rmse_cube.long_name == "RMSE_of_air_temperature"


def test_scores_rmse_nonzero():
    """Test taking the rmse between two different cubes."""
    # Data preparation.
    cube = iris.cube.Cube(
        np.ones((2, 2)),
        dim_coords_and_dims=[
            (iris.coords.DimCoord([1, 2], var_name="x"), 0),
            (iris.coords.DimCoord([1, 2], var_name="y"), 1),
        ],
        var_name="test",
        attributes={"cset_comparison_base": 1},
    )
    other_cube = iris.cube.Cube(
        np.zeros((2, 2)),
        dim_coords_and_dims=[
            (iris.coords.DimCoord([1, 2], var_name="x"), 0),
            (iris.coords.DimCoord([1, 2], var_name="y"), 1),
        ],
        var_name="test",
    )
    cubes = iris.cube.CubeList([cube, other_cube])
    # Take difference.
    rmse_cube = scoreswrappers.scores_rmse(cubes)

    # As both cubes use the same data, check the rmse is zero.
    assert isinstance(rmse_cube, iris.cube.Cube)
    assert np.allclose(rmse_cube.data, 1.0, atol=1e-9)
    assert rmse_cube.standard_name is None
    assert rmse_cube.long_name == "RMSE_of_test"


def test_scores_rmse_no_time_coord(cube):
    """RMSE of cubes with no time coordinate."""
    c1 = cube.extract(iris.Constraint(time=datetime.datetime(2022, 9, 21, 3, 0)))
    c1.remove_coord("time")
    c2 = c1.copy()
    del c2.attributes["cset_comparison_base"]
    cubes = iris.cube.CubeList([c1, c2])
    rmse_cube = scoreswrappers.scores_rmse(cubes)
    assert isinstance(rmse_cube, iris.cube.Cube)
    assert np.allclose(rmse_cube.data, np.zeros_like(rmse_cube.data), atol=1e-9)


def test_scores_rmse_no_common_points(cube):
    """Test exception when there are no common time points between cubes."""
    other_cube = cube.copy()
    # Offset times by 6 hours.
    new_times = other_cube.coord("time").points.copy()
    new_times += 6
    other_cube.coord("time").points = new_times
    del other_cube.attributes["cset_comparison_base"]
    cubes = iris.cube.CubeList([cube, other_cube])
    with pytest.raises(ValueError, match="No common time points found!"):
        scoreswrappers.scores_rmse(cubes)


def test_scores_rmse_incorrect_number_of_cubes(cube):
    """Test exception when incorrect number of cubes provided."""
    no_cubes = iris.cube.CubeList([])
    with pytest.raises(ValueError, match="cubes should contain exactly 2 cubes."):
        scoreswrappers.scores_rmse(no_cubes)

    one_cube = iris.cube.CubeList([cube])
    with pytest.raises(ValueError, match="cubes should contain exactly 2 cubes."):
        scoreswrappers.scores_rmse(one_cube)

    three_cubes = iris.cube.CubeList([cube, cube, cube])
    with pytest.raises(ValueError, match="cubes should contain exactly 2 cubes."):
        scoreswrappers.scores_rmse(three_cubes)


def test_scores_rmse_different_data_shape_regrid(cube):
    """Test when data shape differs, but gets regridded.

    For any cube shapes differ.
    """
    rearranged_cube = cube.copy()
    rearranged_cube = rearranged_cube[:, :, 1:]
    del cube.attributes["cset_comparison_base"]
    cubes = iris.cube.CubeList([rearranged_cube, cube])
    # Need to preserve coordinates to test shape.
    rmse = scoreswrappers.scores_rmse(
        cubes, preserved_coordinates=["time", "grid_latitude", "grid_longitude"]
    )
    assert isinstance(rmse, iris.cube.Cube)
    assert rmse.shape == cube.shape
    assert rmse.shape != rearranged_cube.shape


def test_rmse_grid_staggering_regrid(cube):
    """Test when data considered on staggered grid, so gets regridded."""
    rearranged_cube = cube.copy()
    rearranged_cube.rename("eastward_wind_at_10m")
    del cube.attributes["cset_comparison_base"]
    cubes = iris.cube.CubeList([rearranged_cube, cube])
    # Need to preserve coordinates to test shape.
    rmse = scoreswrappers.scores_rmse(
        cubes, preserved_coordinates=["time", "grid_latitude", "grid_longitude"]
    )
    assert isinstance(rmse, iris.cube.Cube)
    assert rmse.shape == cube.shape


def test_difference_different_model_types(cube):
    """Other cube is flipped when model types differ."""
    flipped = cube.copy()
    reverse(flipped, "grid_latitude")
    del flipped.attributes["cset_comparison_base"]
    cubes = iris.cube.CubeList([cube, flipped])

    # Take rmse.
    rmse_cube = scoreswrappers.scores_rmse(cubes)

    assert isinstance(rmse_cube, iris.cube.Cube)
    # As both cubes use the same data, check the difference is zero.
    assert np.allclose(rmse_cube.data, np.zeros_like(rmse_cube.data), atol=1e-9)


def test_difference_flip_pressure_order(transect_source_cube_readonly):
    """Test that pressure coord is flipped if discreasing."""
    flipped = transect_source_cube_readonly.copy()
    reverse(flipped, "pressure")
    del flipped.attributes["cset_comparison_base"]
    cubes = iris.cube.CubeList([transect_source_cube_readonly, flipped])

    # Take rmse.
    rmse_cube = scoreswrappers.scores_rmse(cubes)

    assert isinstance(rmse_cube, iris.cube.Cube)
    # As both cubes use the same data, check the difference is zero.
    assert np.allclose(rmse_cube.data, np.zeros_like(rmse_cube.data), atol=1e-9)


def test_crps(feature_cube):
    """Test basic crps functionality.

     Ensure wrapper gets same result as
    scores operator.
    """
    crps_cube_erps = scoreswrappers.scores_crps_for_ensemble(feature_cube)
    crps_cube_fair = scoreswrappers.scores_crps_for_ensemble(
        feature_cube, method="fair"
    )

    ctrl = feature_cube.extract(generate_realization_constraint([0]))
    ens_mem = feature_cube.extract(generate_remove_single_ensemble_member_constraint(0))

    ctrl = xr.DataArray.from_iris(ctrl)
    ens_mem = xr.DataArray.from_iris(ens_mem)
    scores_crps_erps = xr.DataArray.to_iris(
        scores.probability.crps_for_ensemble(
            ens_mem,
            ctrl,
            ensemble_member_dim="realization",
            method="ecdf",
            preserve_dims="time",
        )
    )

    scores_crps_fair = xr.DataArray.to_iris(
        scores.probability.crps_for_ensemble(
            ens_mem,
            ctrl,
            ensemble_member_dim="realization",
            method="fair",
            preserve_dims="time",
        )
    )

    assert isinstance(crps_cube_erps, iris.cube.Cube)
    assert feature_cube.coord("time").shape == crps_cube_erps.coord("time").shape

    assert isinstance(crps_cube_fair, iris.cube.Cube)
    assert feature_cube.coord("time").shape == crps_cube_fair.coord("time").shape

    assert np.allclose(crps_cube_erps.data, scores_crps_erps.data, atol=1e-2, rtol=1e-6)
    assert np.allclose(crps_cube_fair.data, scores_crps_fair.data, atol=1e-2, rtol=1e-6)


def test_crps_control_member_out_of_bounds(feature_cube):
    """Test handling of out of bounds control member value."""
    scoreswrappers.scores_crps_for_ensemble(feature_cube, control_member=1000)


def test_crps_one_time_coord(feature_cube):
    """Test handling of only one time point in cube provided."""
    feature_cube_one_time = feature_cube[:, 0, :, :]
    with pytest.raises(ValueError, match=r"Cube has only one time point."):
        scoreswrappers.scores_crps_for_ensemble(feature_cube_one_time)


def test_crps_less_than_3_realizations(feature_cube):
    """Test handling of less than 3 realizations in cube provided."""
    feature_cube_one_realization = feature_cube[0:1, :, :, :]
    with pytest.raises(
        ValueError,
        match=r"Cube should have one control member and at least two members",
    ):
        scoreswrappers.scores_crps_for_ensemble(feature_cube_one_realization)
