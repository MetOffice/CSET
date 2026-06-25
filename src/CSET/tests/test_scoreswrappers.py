"""Unit tests for operators/scoreswrappers.py."""

from unittest.mock import patch

import iris
import numpy as np
import pytest

from CSET.operators import scoreswrappers


def create_cube(data, name="test", units="m"):
    """Create a simple 1D Iris cube for testing."""
    return iris.cube.Cube(
        np.array(data, dtype=float),
        long_name=name,
        units=units,
        dim_coords_and_dims=[
            (iris.coords.DimCoord(np.arange(len(data)), standard_name="latitude"), 0)
        ],
    )


class TestScoresMetrics:
    """Tests for the scores_metrics function."""

    @pytest.mark.parametrize(
        "scores_method,wrapper_name",
        [
            ("RMSE", "scores_rmse"),
            ("MAE", "scores_mae"),
            ("additive_bias", "scores_additive_bias"),
            ("correlation_pearsonr", "scores_correlation_pearsonr"),
        ],
    )
    def test_calls_correct_scores_wrapper(self, scores_method, wrapper_name):
        """The scores_metrics dispatcher should call the right wrapper."""
        cube_a = create_cube([1.0, 2.0], name="base")
        cube_b = create_cube([1.5, 2.5], name="other")
        cubes = iris.cube.CubeList([cube_a, cube_b])
        expected_cube = create_cube([0.0, 0.0], name="expected")

        with patch(
            f"CSET.operators.scoreswrappers.{wrapper_name}",
            return_value=expected_cube,
        ) as mock_wrapper:
            result = scoreswrappers.scores_metrics(
                cubes,
                preserved_coordinates=["time"],
                scores_method=scores_method,
            )

        mock_wrapper.assert_called_once_with(cubes, ["time"])
        assert isinstance(result, iris.cube.CubeList)
        assert len(result) == 1
        assert result[0] is expected_cube

    @pytest.mark.parametrize("scores_method", [None, "", "invalid_method"])
    def test_returns_empty_cubelist_for_unknown_method(self, scores_method):
        """Unknown or missing methods should return an empty CubeList."""
        cube_a = create_cube([1.0])
        cube_b = create_cube([2.0])
        cubes = iris.cube.CubeList([cube_a, cube_b])

        result = scoreswrappers.scores_metrics(
            cubes,
            preserved_coordinates=None,
            scores_method=scores_method,
        )

        assert isinstance(result, iris.cube.CubeList)
        assert len(result) == 0
