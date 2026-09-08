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
import iris.coords
import numpy as np
import pytest
import scores
import scores.probability
import xarray as xr
from iris.cube import Cube, CubeList
from iris.util import reverse

from CSET.operators import scoreswrappers
from CSET.operators.constraints import (
    generate_realization_constraint,
    generate_remove_single_ensemble_member_constraint,
)


def test_scores_correlation_pearsonr(cube: Cube):
    """Test taking the Pearson correlation between two cubes."""
    # Data preparation.
    other_cube = cube.copy()
    del other_cube.attributes["cset_comparison_base"]
    cube.attributes["model_name"] = "model1"
    other_cube.attributes["model_name"] = "model2"
    cubes = CubeList([cube, other_cube])

    # Take difference.
    correlation_pearsonr_cube = scoreswrappers.scores_correlation_pearsonr(cubes)

    # As both cubes use the same data, check the Pearson correlation is one.
    assert isinstance(correlation_pearsonr_cube, Cube)
    assert np.allclose(
        correlation_pearsonr_cube.data,
        np.ones_like(correlation_pearsonr_cube.data),
        atol=1e-9,
    )
    assert correlation_pearsonr_cube.standard_name is None
    assert (
        correlation_pearsonr_cube.long_name == "Pearson_Correlation_of_air_temperature"
    )


def test_scores_additive_bias(cube: Cube):
    """Test taking the additive bias between two cubes."""
    # Data preparation.
    other_cube = cube.copy()
    del other_cube.attributes["cset_comparison_base"]
    cube.attributes["model_name"] = "model1"
    other_cube.attributes["model_name"] = "model2"
    cubes = CubeList([cube, other_cube])

    # Take difference.
    additive_bias_cube = scoreswrappers.scores_additive_bias(cubes)

    # As both cubes use the same data, check the additive bias is zero.
    assert isinstance(additive_bias_cube, Cube)
    assert np.allclose(
        additive_bias_cube.data, np.zeros_like(additive_bias_cube.data), atol=1e-9
    )
    assert additive_bias_cube.standard_name is None
    assert additive_bias_cube.long_name == "Additive_Bias_of_air_temperature"


def test_scores_mae(cube: Cube):
    """Test taking the mae between two cubes."""
    # Data preparation.
    other_cube = cube.copy()
    del other_cube.attributes["cset_comparison_base"]
    cube.attributes["model_name"] = "model1"
    other_cube.attributes["model_name"] = "model2"
    cubes = CubeList([cube, other_cube])

    # Take difference.
    mae_cube = scoreswrappers.scores_mae(cubes)

    # As both cubes use the same data, check the mae is zero.
    assert isinstance(mae_cube, Cube)
    assert np.allclose(mae_cube.data, np.zeros_like(mae_cube.data), atol=1e-9)
    assert mae_cube.standard_name is None
    assert mae_cube.long_name == "MAE_of_air_temperature"


def test_scores_rmse(cube: Cube):
    """Test taking the rmse between two cubes."""
    # Data preparation.
    other_cube = cube.copy()
    del other_cube.attributes["cset_comparison_base"]
    cube.attributes["model_name"] = "model1"
    other_cube.attributes["model_name"] = "model2"
    cubes = CubeList([cube, other_cube])

    # Take difference.
    rmse_cube = scoreswrappers.scores_rmse(cubes)

    # As both cubes use the same data, check the rmse is zero.
    assert isinstance(rmse_cube, Cube)
    assert np.allclose(rmse_cube.data, np.zeros_like(rmse_cube.data), atol=1e-9)
    assert rmse_cube.standard_name is None
    assert rmse_cube.long_name == "RMSE_of_air_temperature"


def test_scores_rmse_nonzero():
    """Test taking the rmse between two different cubes."""
    cube = Cube(
        np.zeros((2, 2)),
        dim_coords_and_dims=(
            (iris.coords.DimCoord([1, 2], var_name="x"), 0),
            (iris.coords.DimCoord([1, 2], var_name="y"), 1),
        ),
        var_name="test",
    )
    other_cube = cube.copy(data=np.ones((2, 2)))
    cube.attributes["cset_comparison_base"] = 1
    cube.attributes["model_name"] = "model1"
    other_cube.attributes["model_name"] = "model2"
    different_cubes = CubeList((cube, other_cube))
    # Take difference.
    rmse_cube = scoreswrappers.scores_rmse(different_cubes)

    # As both cubes use the same data, check the rmse is zero.
    assert isinstance(rmse_cube, Cube)
    assert np.allclose(rmse_cube.data, 1.0, atol=1e-9)
    assert rmse_cube.standard_name is None
    assert rmse_cube.long_name == "RMSE_of_test"


def test_scores_rmse_no_time_coord(cube):
    """RMSE of cubes with no time coordinate."""
    c1 = cube.extract(iris.Constraint(time=datetime.datetime(2022, 9, 21, 3, 0)))
    c1.remove_coord("time")
    c2 = c1.copy()
    del c2.attributes["cset_comparison_base"]
    c1.attributes["model_name"] = "model1"
    c2.attributes["model_name"] = "model2"
    cubes = CubeList([c1, c2])
    rmse_cube = scoreswrappers.scores_rmse(cubes)
    assert isinstance(rmse_cube, Cube)
    assert np.allclose(rmse_cube.data, np.zeros_like(rmse_cube.data), atol=1e-9)


def test_scores_rmse_no_common_points(cube):
    """Test exception when there are no common time points between cubes."""
    other_cube = cube.copy()
    # Offset times by 6 hours.
    new_times = other_cube.coord("time").points.copy()
    new_times += 6
    other_cube.coord("time").points = new_times
    del other_cube.attributes["cset_comparison_base"]
    cube.attributes["model_name"] = "model1"
    other_cube.attributes["model_name"] = "model2"
    cubes = CubeList([cube, other_cube])
    with pytest.raises(ValueError, match="No common time points found!"):
        scoreswrappers.scores_rmse(cubes)


def test_scores_rmse_different_data_shape_regrid(cube):
    """Test when data shape differs, but gets regridded.

    For any cube shapes differ.
    """
    rearranged_cube = cube.copy()
    rearranged_cube = rearranged_cube[:, :, 1:]
    del cube.attributes["cset_comparison_base"]
    rearranged_cube.attributes["model_name"] = "model1"
    cube.attributes["model_name"] = "model2"
    cubes = CubeList([rearranged_cube, cube])
    # Need to preserve coordinates to test shape.
    rmse = scoreswrappers.scores_rmse(
        cubes, preserved_coordinates=["time", "grid_latitude", "grid_longitude"]
    )
    assert isinstance(rmse, Cube)
    assert rmse.shape == cube.shape
    assert rmse.shape != rearranged_cube.shape


def test_rmse_grid_staggering_regrid(cube):
    """Test when data considered on staggered grid, so gets regridded."""
    rearranged_cube = cube.copy()
    rearranged_cube.rename("eastward_wind_at_10m")
    del cube.attributes["cset_comparison_base"]
    rearranged_cube.attributes["model_name"] = "model1"
    cube.attributes["model_name"] = "model2"
    cubes = CubeList([rearranged_cube, cube])
    # Need to preserve coordinates to test shape.
    rmse = scoreswrappers.scores_rmse(
        cubes, preserved_coordinates=["time", "grid_latitude", "grid_longitude"]
    )
    assert isinstance(rmse, Cube)
    assert rmse.shape == cube.shape


def test_difference_different_model_types(cube):
    """Other cube is flipped when model types differ."""
    flipped = cube.copy()
    reverse(flipped, "grid_latitude")
    del flipped.attributes["cset_comparison_base"]
    flipped.attributes["model_name"] = "model1"
    cube.attributes["model_name"] = "model2"
    cubes = CubeList([cube, flipped])

    # Take rmse.
    rmse_cube = scoreswrappers.scores_rmse(cubes)

    assert isinstance(rmse_cube, Cube)
    # As both cubes use the same data, check the difference is zero.
    assert np.allclose(rmse_cube.data, np.zeros_like(rmse_cube.data), atol=1e-9)


def test_difference_flip_pressure_order(transect_source_cube_readonly):
    """Test that pressure coord is flipped if decreasing."""
    flipped = transect_source_cube_readonly.copy()
    reverse(flipped, "pressure")
    del flipped.attributes["cset_comparison_base"]
    flipped.attributes["model_name"] = "model1"
    transect_source_cube_readonly.attributes["model_name"] = "model2"
    cubes = CubeList([transect_source_cube_readonly, flipped])

    # Take rmse.
    rmse_cube = scoreswrappers.scores_rmse(cubes)

    assert isinstance(rmse_cube, Cube)
    # As both cubes use the same data, check the difference is zero.
    assert np.allclose(rmse_cube.data, np.zeros_like(rmse_cube.data), atol=1e-9)


def test_crps(feature_cube):
    """Test basic crps functionality.

    Ensure wrapper gets same result as scores operator.
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

    assert isinstance(crps_cube_erps, Cube)
    assert feature_cube.coord("time").shape == crps_cube_erps.coord("time").shape

    assert isinstance(crps_cube_fair, Cube)
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


def test_model_obs_rmse_preserve_in_time(dummy_cubelist_model_obs):
    """RMSE collapsed over station, preserving only the time dimension."""
    rmse = scoreswrappers.scores_rmse(dummy_cubelist_model_obs, "time")
    assert isinstance(rmse, CubeList)
    assert len(rmse) == 2
    model_names = ["model_a", "model_b"]
    for cube, model_name in zip(rmse, model_names, strict=True):
        assert cube.name() == "RMSE_of_observed_temperature_at_screen_level"
        assert cube.units == "K"
        assert cube.shape == (36,)
        assert cube.attributes["model_name"] == model_name


def test_model_obs_rmse_preserve_in_latlon(dummy_cubelist_model_obs):
    """RMSE collapsed over time, preserving the station dimension via lat/lon."""
    rmse = scoreswrappers.scores_rmse(
        dummy_cubelist_model_obs, ["longitude", "latitude"]
    )
    assert isinstance(rmse, CubeList)
    assert len(rmse) == 2
    model_names = ["model_a", "model_b"]
    for cube, model_name in zip(rmse, model_names, strict=True):
        assert cube.name() == "RMSE_of_observed_temperature_at_screen_level"
        assert cube.units == "K"
        assert cube.shape == (28,)
        assert cube.attributes["model_name"] == model_name


def test_model_obs_rmse_preserve_in_timelatlon(dummy_cubelist_model_obs):
    """RMSE with nothing collapsed, preserving both time and station dimensions."""
    rmse = scoreswrappers.scores_rmse(
        dummy_cubelist_model_obs, ["time", "longitude", "latitude"]
    )
    assert isinstance(rmse, CubeList)
    assert len(rmse) == 2
    model_names = ["model_a", "model_b"]
    for cube, model_name in zip(rmse, model_names, strict=True):
        assert cube.name() == "RMSE_of_observed_temperature_at_screen_level"
        assert cube.units == "K"
        assert cube.shape == (36, 28)
        assert cube.attributes["model_name"] == model_name


def test_model_obs_mae_preserve_in_time(dummy_cubelist_model_obs):
    """MAE collapsed over station, preserving only the time dimension."""
    mae = scoreswrappers.scores_mae(dummy_cubelist_model_obs, "time")
    assert isinstance(mae, CubeList)
    assert len(mae) == 2
    model_names = ["model_a", "model_b"]
    for cube, model_name in zip(mae, model_names, strict=True):
        assert cube.name() == "MAE_of_observed_temperature_at_screen_level"
        assert cube.units == "K"
        assert cube.shape == (36,)
        assert cube.attributes["model_name"] == model_name


def test_model_obs_mae_preserve_in_latlon(dummy_cubelist_model_obs):
    """MAE collapsed over time, preserving the station dimension via lat/lon."""
    mae = scoreswrappers.scores_mae(dummy_cubelist_model_obs, ["longitude", "latitude"])
    assert isinstance(mae, CubeList)
    assert len(mae) == 2
    model_names = ["model_a", "model_b"]
    for cube, model_name in zip(mae, model_names, strict=True):
        assert cube.name() == "MAE_of_observed_temperature_at_screen_level"
        assert cube.units == "K"
        assert cube.shape == (28,)
        assert cube.attributes["model_name"] == model_name


def test_model_obs_mae_preserve_in_timelatlon(dummy_cubelist_model_obs):
    """MAE with nothing collapsed, preserving both time and station dimensions."""
    mae = scoreswrappers.scores_mae(
        dummy_cubelist_model_obs, ["time", "longitude", "latitude"]
    )
    assert isinstance(mae, CubeList)
    assert len(mae) == 2
    model_names = ["model_a", "model_b"]
    for cube, model_name in zip(mae, model_names, strict=True):
        assert cube.name() == "MAE_of_observed_temperature_at_screen_level"
        assert cube.units == "K"
        assert cube.shape == (36, 28)
        assert cube.attributes["model_name"] == model_name


def test_model_obs_pearson_correlation_preserve_in_time(dummy_cubelist_model_obs):
    """Pearson correlation collapsed over station, preserving only the time dimension."""
    corr = scoreswrappers.scores_correlation_pearsonr(dummy_cubelist_model_obs, "time")
    assert isinstance(corr, CubeList)
    assert len(corr) == 2
    model_names = ["model_a", "model_b"]
    for cube, model_name in zip(corr, model_names, strict=True):
        assert (
            cube.name() == "Pearson_Correlation_of_observed_temperature_at_screen_level"
        )
        assert cube.units == "K"
        assert cube.shape == (36,)
        assert cube.attributes["model_name"] == model_name


def test_model_obs_pearson_correlation_preserve_in_latlon(dummy_cubelist_model_obs):
    """Pearson correlation collapsed over time, preserving the station dimension via lat/lon."""
    corr = scoreswrappers.scores_correlation_pearsonr(
        dummy_cubelist_model_obs, ["longitude", "latitude"]
    )
    assert isinstance(corr, CubeList)
    assert len(corr) == 2
    model_names = ["model_a", "model_b"]
    for cube, model_name in zip(corr, model_names, strict=True):
        assert (
            cube.name() == "Pearson_Correlation_of_observed_temperature_at_screen_level"
        )
        assert cube.units == "K"
        assert cube.shape == (28,)
        assert cube.attributes["model_name"] == model_name


def test_model_obs_pearson_correlation_preserve_in_timelatlon(dummy_cubelist_model_obs):
    """Pearson correlation with nothing collapsed, preserving both time and station dimensions."""
    with pytest.raises(
        ValueError, match="You cannot preserve all dimensions with pearsonr."
    ):
        scoreswrappers.scores_correlation_pearsonr(
            dummy_cubelist_model_obs, ["time", "longitude", "latitude"]
        )


def test_model_obs_additive_bias_preserve_in_time(dummy_cubelist_model_obs):
    """Additive bias collapsed over station, preserving only the time dimension."""
    bias = scoreswrappers.scores_additive_bias(dummy_cubelist_model_obs, "time")
    assert isinstance(bias, CubeList)
    assert len(bias) == 2
    model_names = ["model_a", "model_b"]
    for cube, model_name in zip(bias, model_names, strict=True):
        assert cube.name() == "Additive_Bias_of_observed_temperature_at_screen_level"
        assert cube.units == "K"
        assert cube.shape == (36,)
        assert cube.attributes["model_name"] == model_name


def test_model_obs_additive_bias_preserve_in_latlon(dummy_cubelist_model_obs):
    """Additive bias collapsed over time, preserving the station dimension via lat/lon."""
    bias = scoreswrappers.scores_additive_bias(
        dummy_cubelist_model_obs, ["longitude", "latitude"]
    )
    assert isinstance(bias, CubeList)
    assert len(bias) == 2
    model_names = ["model_a", "model_b"]
    for cube, model_name in zip(bias, model_names, strict=True):
        assert cube.name() == "Additive_Bias_of_observed_temperature_at_screen_level"
        assert cube.units == "K"
        assert cube.shape == (28,)
        assert cube.attributes["model_name"] == model_name


def test_model_obs_additive_bias_preserve_in_timelatlon(dummy_cubelist_model_obs):
    """Additive bias with nothing collapsed, preserving both time and station dimensions."""
    bias = scoreswrappers.scores_additive_bias(
        dummy_cubelist_model_obs, ["time", "longitude", "latitude"]
    )
    assert isinstance(bias, CubeList)
    assert len(bias) == 2
    model_names = ["model_a", "model_b"]
    for cube, model_name in zip(bias, model_names, strict=True):
        assert cube.name() == "Additive_Bias_of_observed_temperature_at_screen_level"
        assert cube.units == "K"
        assert cube.shape == (36, 28)
        assert cube.attributes["model_name"] == model_name


def test_scores_categorical_metric_pod_gt_2x2_manual_case(
    make_cube_categorical_testing,
):
    """Test basic 2x2 case for manual validation."""
    obs = make_cube_categorical_testing(
        [[12, 5], [15, 8]],
        long_name="observed_temperature",
        model_name="obs",
    )
    obs.attributes["cset_comparison_base"] = 1

    model = make_cube_categorical_testing(
        [[14, 20], [7, 4]],
        long_name="temperature",
        model_name="test_model",
    )

    result = scoreswrappers._scores_categorical_metric(
        CubeList([model, obs]),
        preserved_coordinates=None,
        threshold="10",
        op_func="gt",
        metric="pod",
    )

    # Ensure 1 cube returned.
    assert len(result) == 1

    # Hits should be [[1,1],[0,0]] so hit rate of 0.5.
    assert np.allclose(result[0].data, 0.5, atol=1e-2, rtol=1e-6)


def test_scores_categorical_metric_pod_returns_one_when_all_events_perfect(
    make_cube_categorical_testing,
):
    """Test basic 2x2 case when all correct hits."""
    obs = make_cube_categorical_testing(
        [[1, 1], [1, 1]],
        long_name="observed_temperature",
        model_name="obs",
    )

    model = make_cube_categorical_testing(
        [[2, 2], [2, 2]],
        long_name="temperature",
        model_name="test_model",
    )

    result = scoreswrappers._scores_categorical_metric(
        CubeList([model, obs]),
        preserved_coordinates=None,
        threshold="0",
        op_func="gt",
        metric="pod",
    )

    # Hits should be [[1,1],[1,1]] so hit rate of 1.
    assert np.allclose(result[0].data, 1, atol=1e-2, rtol=1e-6)


def test_scores_categorical_metric_pod_returns_zero_when_all_events_missed(
    make_cube_categorical_testing,
):
    """Test basic 2x2 case when all events missed."""
    obs = make_cube_categorical_testing(
        [[12, 5], [15, 8]],
        long_name="observed_temperature",
        model_name="obs",
    )

    model = make_cube_categorical_testing(
        [[1, 1], [1, 1]],
        long_name="temperature",
        model_name="test_model",
    )

    result = scoreswrappers._scores_categorical_metric(
        CubeList([model, obs]),
        preserved_coordinates=None,
        threshold="10",
        op_func="gt",
        metric="pod",
    )

    # Hits will be [[0,0],[0,0]] so hit rate of zero.
    assert np.allclose(result[0].data, 0, atol=1e-2, rtol=1e-6)


def test_scores_categorical_metric_pod_preserve_time_dimension(
    make_cube_categorical_testing_with_time,
):
    """Ensure time dimension preserved when passed to function."""
    obs = make_cube_categorical_testing_with_time(
        [
            [[1, 1], [1, 1]],
            [[1, 1], [1, 1]],
            [[1, 1], [1, 1]],
        ],
        long_name="observed_temperature",
        model_name="obs",
    )

    model = make_cube_categorical_testing_with_time(
        [
            [[2, 2], [2, 2]],
            [[0, 0], [0, 0]],
            [[0, 0], [0, 0]],
        ],
        long_name="temperature",
        model_name="test_model",
    )

    result = scoreswrappers._scores_categorical_metric(
        CubeList([model, obs]),
        preserved_coordinates=["time"],
        threshold="0.5",
        op_func="gt",
        metric="pod",
    )

    assert np.allclose(result[0].data, np.array([1.0, 0.0, 0.0]), atol=1e-2, rtol=1e-6)


def test_returns_one_score_per_model(make_cube_categorical_testing):
    """Test POD for multiple models and return two results."""
    obs = make_cube_categorical_testing(
        [[12, 5], [15, 8]],
        long_name="observed_temperature",
        model_name="obs",
    )

    model_a = make_cube_categorical_testing(
        [[20, 1], [20, 1]],
        long_name="temperature",
        model_name="test_modelA",
    )

    model_b = make_cube_categorical_testing(
        [[1, 1], [1, 1]],
        long_name="temperature",
        model_name="test_modelB",
    )

    result = scoreswrappers._scores_categorical_metric(
        CubeList([model_a, model_b, obs]),
        preserved_coordinates=None,
        threshold="10",
        op_func="gt",
        metric="pod",
    )

    assert len(result) == 2
    assert result[0].attributes["model_name"] == "test_modelA"
    assert result[1].attributes["model_name"] == "test_modelB"


def test_output_metadata(make_cube_categorical_testing):
    """Test that cube has appropriate metadata preserved."""
    obs = make_cube_categorical_testing(
        [[12, 5], [15, 8]],
        long_name="observed_temperature",
        model_name="obs",
    )

    model = make_cube_categorical_testing(
        [[1, 1], [1, 1]],
        long_name="temperature",
        model_name="test_model",
    )

    result = scoreswrappers._scores_categorical_metric(
        CubeList([model, obs]),
        preserved_coordinates=None,
        threshold="10",
        op_func="gt",
        metric="pod",
    )

    cube = result[0]

    assert cube.units == "1"
    assert cube.attributes["model_name"] == "test_model"

    assert cube.name() == "Probability_Of_Detection_gt_10_observed_temperature"


def test_invalid_operator_raises(make_cube_categorical_testing):
    """Check that code raises exception if unsupported operator."""
    obs = make_cube_categorical_testing(
        [[12, 5], [15, 8]],
        long_name="observed_temperature",
        model_name="obs",
    )

    model = make_cube_categorical_testing(
        [[1, 1], [1, 1]],
        long_name="temperature",
        model_name="test_model",
    )

    with pytest.raises(
        ValueError,
        match=r"Operator gte not supported.",
    ):
        scoreswrappers._scores_categorical_metric(
            CubeList([model, obs]),
            preserved_coordinates=None,
            threshold="10",
            op_func="gte",
            metric="pod",
        )


def test_ets_gt_perfect_forecast(make_cube_categorical_testing):
    """Perfect forecast should give ETS=1."""
    obs = make_cube_categorical_testing(
        [[12, 5], [15, 8]],
        long_name="observed_temperature",
        model_name="obs",
    )
    obs.attributes["cset_comparison_base"] = 1

    model = make_cube_categorical_testing(
        [[12, 5], [15, 8]],
        long_name="temperature",
        model_name="test_model",
    )

    result = scoreswrappers._scores_categorical_metric(
        CubeList([model, obs]),
        preserved_coordinates=None,
        threshold="10",
        op_func="gt",
        metric="pod",
    )

    assert len(result) == 1
    assert np.allclose(result[0].data, 1.0, atol=1e-2, rtol=1e-6)


def test_ets_gt_mixed_case(make_cube_categorical_testing):
    """Manual ETS calculation for a mixed forecast."""
    obs = make_cube_categorical_testing(
        [[12, 5], [15, 8]],
        long_name="observed_temperature",
        model_name="obs",
    )
    obs.attributes["cset_comparison_base"] = 1

    model = make_cube_categorical_testing(
        [[14, 20], [7, 4]],
        long_name="temperature",
        model_name="test_model",
    )

    result = scoreswrappers._scores_categorical_metric(
        CubeList([model, obs]),
        preserved_coordinates=None,
        threshold="10",
        op_func="gt",
        metric="ets",
    )

    # Binary fields:
    #
    # Obs    = [[1,0],
    #           [1,0]]
    #
    # Model  = [[1,1],
    #           [0,0]]
    #
    # H=1, M=1, F=1, N=4
    # Hr=(2*2)/4=1
    # ETS=(1-1)/(1+1+1-1)=0

    assert len(result) == 1
    assert np.allclose(result[0].data, 0.0, atol=1e-2, rtol=1e-6)


def test_ets_gt_complete_miss(make_cube_categorical_testing):
    """No hits, all events misplaced."""
    obs = make_cube_categorical_testing(
        [[12, 12], [5, 5]],
        long_name="observed_temperature",
        model_name="obs",
    )
    obs.attributes["cset_comparison_base"] = 1

    model = make_cube_categorical_testing(
        [[5, 5], [12, 12]],
        long_name="temperature",
        model_name="test_model",
    )

    result = scoreswrappers._scores_categorical_metric(
        CubeList([model, obs]),
        preserved_coordinates=None,
        threshold="10",
        op_func="gt",
        metric="ets",
    )

    # H=0, M=2, F=2, N=4
    # Hr=(2*2)/4=1
    # ETS=(0-1)/(0+2+2-1)=-1/3

    assert len(result) == 1
    assert np.allclose(result[0].data, -1.0 / 3.0, atol=1e-2, rtol=1e-6)


def test_frequency_bias_gt_perfect_forecast(make_cube_categorical_testing):
    """Perfect forecast should give FB=1."""
    obs = make_cube_categorical_testing(
        [[12, 5], [15, 8]],
        long_name="observed_temperature",
        model_name="obs",
    )
    obs.attributes["cset_comparison_base"] = 1

    model = make_cube_categorical_testing(
        [[12, 5], [15, 8]],
        long_name="temperature",
        model_name="test_model",
    )

    result = scoreswrappers._scores_categorical_metric(
        CubeList([model, obs]),
        preserved_coordinates=None,
        threshold="10",
        op_func="gt",
        metric="fb",
    )

    assert len(result) == 1
    assert np.allclose(result[0].data, 1.0, atol=1e-2, rtol=1e-6)


def test_frequency_bias_gt_mixed_case(make_cube_categorical_testing):
    """Manual FB calculation for a mixed forecast."""
    obs = make_cube_categorical_testing(
        [[12, 5], [15, 8]],
        long_name="observed_temperature",
        model_name="obs",
    )
    obs.attributes["cset_comparison_base"] = 1

    model = make_cube_categorical_testing(
        [[14, 20], [7, 4]],
        long_name="temperature",
        model_name="test_model",
    )

    result = scoreswrappers._scores_categorical_metric(
        CubeList([model, obs]),
        preserved_coordinates=None,
        threshold="10",
        op_func="gt",
        metric="fb",
    )

    # Binary fields:
    #
    # Obs    = [[1,0],
    #           [1,0]]
    #
    # Model  = [[1,1],
    #           [0,0]]
    #
    # H=1, M=1, F=1
    # FB=(H+F)/(H+M)=2/2=1

    assert len(result) == 1
    assert np.allclose(result[0].data, 1.0, atol=1e-2, rtol=1e-6)


def test_frequency_bias_gt_complete_miss(make_cube_categorical_testing):
    """No hits, all events misplaced."""
    obs = make_cube_categorical_testing(
        [[12, 12], [5, 5]],
        long_name="observed_temperature",
        model_name="obs",
    )
    obs.attributes["cset_comparison_base"] = 1

    model = make_cube_categorical_testing(
        [[5, 5], [12, 12]],
        long_name="temperature",
        model_name="test_model",
    )

    result = scoreswrappers._scores_categorical_metric(
        CubeList([model, obs]),
        preserved_coordinates=None,
        threshold="10",
        op_func="gt",
        metric="fb",
    )

    # H=0, M=2, F=2
    # FB=(H+F)/(H+M)=2/2=1

    assert len(result) == 1
    assert np.allclose(result[0].data, 1.0, atol=1e-2, rtol=1e-6)


def test_pfd_gt_perfect_forecast(make_cube_categorical_testing):
    """Perfect forecast should give PFD=0."""
    obs = make_cube_categorical_testing(
        [[12, 5], [15, 8]],
        long_name="observed_temperature",
        model_name="obs",
    )
    obs.attributes["cset_comparison_base"] = 1

    model = make_cube_categorical_testing(
        [[12, 5], [15, 8]],
        long_name="temperature",
        model_name="test_model",
    )

    result = scoreswrappers._scores_categorical_metric(
        CubeList([model, obs]),
        preserved_coordinates=None,
        threshold="10",
        op_func="gt",
        metric="pfd",
    )

    assert len(result) == 1
    assert np.allclose(result[0].data, 0.0, atol=1e-2, rtol=1e-6)


def test_pfd_gt_mixed_case(make_cube_categorical_testing):
    """Manual PFD calculation for a mixed forecast."""
    obs = make_cube_categorical_testing(
        [[12, 5], [15, 8]],
        long_name="observed_temperature",
        model_name="obs",
    )
    obs.attributes["cset_comparison_base"] = 1

    model = make_cube_categorical_testing(
        [[14, 20], [7, 4]],
        long_name="temperature",
        model_name="test_model",
    )

    result = scoreswrappers._scores_categorical_metric(
        CubeList([model, obs]),
        preserved_coordinates=None,
        threshold="10",
        op_func="gt",
        metric="pfd",
    )

    # Binary fields:
    #
    # Obs    = [[1,0],
    #           [1,0]]
    #
    # Model  = [[1,1],
    #           [0,0]]
    #
    # H=1, M=1, F=1, TN=1
    # PFD=F/(F+TN)=1/(1+1)=0.5

    assert len(result) == 1
    assert np.allclose(result[0].data, 0.5, atol=1e-2, rtol=1e-6)


def test_pfd_gt_complete_miss(make_cube_categorical_testing):
    """No hits, all events misplaced."""
    obs = make_cube_categorical_testing(
        [[12, 12], [5, 5]],
        long_name="observed_temperature",
        model_name="obs",
    )
    obs.attributes["cset_comparison_base"] = 1

    model = make_cube_categorical_testing(
        [[5, 5], [12, 12]],
        long_name="temperature",
        model_name="test_model",
    )

    result = scoreswrappers._scores_categorical_metric(
        CubeList([model, obs]),
        preserved_coordinates=None,
        threshold="10",
        op_func="gt",
        metric="pfd",
    )

    # H=0, M=2, F=2, TN=0
    # PFD=F/(F+TN)=2/(2+0)=1

    assert len(result) == 1
    assert np.allclose(result[0].data, 1.0, atol=1e-2, rtol=1e-6)


def test_rmse_multiple_forecasts_preserve_forecast_reference_time(
    dummy_cubelist_model_obs_multiple_forecasts,
):
    """Make test cubes."""
    input_cubelist = dummy_cubelist_model_obs_multiple_forecasts
    obs, model = input_cubelist
    data_obs = obs.data
    data_model = model.data

    calculate_rmse = []
    for i in range(obs.coord("forecast_reference_time").shape[0]):
        calculate_rmse.append(
            np.sqrt(np.mean((data_obs[i, :, :] - data_model[i, :, :]) ** 2))
        )

    rmse_scores = scoreswrappers.scores_rmse(input_cubelist, "forecast_reference_time")
    np.allclose(rmse_scores.data, calculate_rmse, atol=1e-2, rtol=1e-6)


def test_rmse_multiple_forecasts_preserve_forecast_period(
    dummy_cubelist_model_obs_multiple_forecasts,
):
    """Make test cubes."""
    input_cubelist = dummy_cubelist_model_obs_multiple_forecasts
    obs, model = input_cubelist
    data_obs = obs.data
    data_model = model.data

    calculate_rmse = []
    for i in range(obs.coord("forecast_period").shape[0]):
        calculate_rmse.append(
            np.sqrt(np.mean((data_obs[:, i, :] - data_model[:, i, :]) ** 2))
        )

    rmse_scores = scoreswrappers.scores_rmse(input_cubelist, "forecast_period")
    assert np.allclose(rmse_scores.data, calculate_rmse, atol=1e-2, rtol=1e-6)


def test_rmse_multiple_forecasts_preserve_none(
    dummy_cubelist_model_obs_multiple_forecasts,
):
    """Make test cubes."""
    input_cubelist = dummy_cubelist_model_obs_multiple_forecasts
    obs, model = input_cubelist
    data_obs = obs.data
    data_model = model.data

    calculate_rmse = np.sqrt(np.mean((data_obs[:, :, :] - data_model[:, :, :]) ** 2))

    rmse_scores = scoreswrappers.scores_rmse(input_cubelist)
    assert np.allclose(rmse_scores.data, calculate_rmse, atol=1e-2, rtol=1e-6)


def test_rmse_multiple_forecasts_preserve_lat_lon(
    dummy_cubelist_model_obs_multiple_forecasts,
):
    """Make test cubes."""
    input_cubelist = dummy_cubelist_model_obs_multiple_forecasts
    obs, model = input_cubelist
    data_obs = obs.data
    data_model = model.data

    calculate_rmse = []
    for i in range(obs.coord("station").shape[0]):
        calculate_rmse.append(
            np.sqrt(np.mean((data_obs[:, :, i] - data_model[:, :, i]) ** 2))
        )

    rmse_scores = scoreswrappers.scores_rmse(
        input_cubelist, preserved_coordinates=["latitude", "longitude"]
    )

    assert np.allclose(rmse_scores.data, calculate_rmse, atol=1e-2, rtol=1e-6)
