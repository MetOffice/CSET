"""Unit tests for loaders/verification.py."""

from unittest.mock import MagicMock, patch

from CSET.loaders.verification import (
    _get_scores_spatial_methods,
    _get_scores_timeseries_methods,
    load,
)
from CSET.recipes import Config, RawRecipe


class TestGetScoresSpatialMethods:
    """Test the _get_scores_spatial_methods helper."""

    def make_conf(self, **kwargs):
        """Test make_conf."""
        conf = MagicMock(spec=Config)
        conf.SCORES_SPATIAL_RMSE = kwargs.get("SCORES_SPATIAL_RMSE", False)
        conf.SCORES_SPATIAL_AB = kwargs.get("SCORES_SPATIAL_AB", False)
        conf.SCORES_SPATIAL_MAE = kwargs.get("SCORES_SPATIAL_MAE", False)
        return conf

    def test_returns_empty_list_when_no_spatial_scores_enabled(self):
        """Test some code."""
        conf = self.make_conf()

        assert _get_scores_spatial_methods(conf) == []

    def test_returns_expected_spatial_score_methods(self):
        """Test some code."""
        conf = self.make_conf(
            SCORES_SPATIAL_RMSE=True,
            SCORES_SPATIAL_AB=True,
            SCORES_SPATIAL_MAE=True,
        )

        assert _get_scores_spatial_methods(conf) == [
            "RMSE",
            "additive_bias",
            "MAE",
        ]


class TestGetScoresTimeseriesMethods:
    """Test the _get_scores_timeseries_methods helper."""

    def make_conf(self, **kwargs):
        """Test some code."""
        conf = MagicMock(spec=Config)
        conf.SCORES_TIMESERIES_RMSE = kwargs.get("SCORES_TIMESERIES_RMSE", False)
        conf.SCORES_TIMESERIES_AB = kwargs.get("SCORES_TIMESERIES_AB", False)
        conf.SCORES_TIMESERIES_MAE = kwargs.get("SCORES_TIMESERIES_MAE", False)
        conf.SCORES_TIMESERIES_PC = kwargs.get("SCORES_TIMESERIES_PC", False)
        return conf

    def test_returns_empty_list_when_no_timeseries_scores_enabled(self):
        """Test some code."""
        conf = self.make_conf()

        assert _get_scores_timeseries_methods(conf) == []

    def test_returns_expected_timeseries_score_methods(self):
        """Test some code."""
        conf = self.make_conf(
            SCORES_TIMESERIES_RMSE=True,
            SCORES_TIMESERIES_AB=True,
            SCORES_TIMESERIES_MAE=True,
            SCORES_TIMESERIES_PC=True,
        )

        assert _get_scores_timeseries_methods(conf) == [
            "RMSE",
            "additive_bias",
            "MAE",
            "correlation_pearsonr",
        ]


class TestLoadVerificationRecipes:
    """Test the load function in loaders/verification.py."""

    def make_conf(self, **kwargs):
        """Test some code."""
        conf = MagicMock(spec=Config)
        conf.SCORES_SPATIAL_RMSE = kwargs.get("SCORES_SPATIAL_RMSE", False)
        conf.SCORES_SPATIAL_AB = kwargs.get("SCORES_SPATIAL_AB", False)
        conf.SCORES_SPATIAL_MAE = kwargs.get("SCORES_SPATIAL_MAE", False)
        conf.SCORES_TIMESERIES_RMSE = kwargs.get("SCORES_TIMESERIES_RMSE", False)
        conf.SCORES_TIMESERIES_AB = kwargs.get("SCORES_TIMESERIES_AB", False)
        conf.SCORES_TIMESERIES_MAE = kwargs.get("SCORES_TIMESERIES_MAE", False)
        conf.SCORES_TIMESERIES_PC = kwargs.get("SCORES_TIMESERIES_PC", False)
        conf.SURFACE_FIELDS = kwargs.get("SURFACE_FIELDS", ["temperature"])
        conf.SPATIAL_SURFACE_FIELD_METHOD = kwargs.get(
            "SPATIAL_SURFACE_FIELD_METHOD", ["SEQ"]
        )
        conf.SELECT_SUBAREA = kwargs.get("SELECT_SUBAREA", False)
        conf.SUBAREA_TYPE = kwargs.get("SUBAREA_TYPE", None)
        conf.SUBAREA_EXTENT = kwargs.get("SUBAREA_EXTENT", None)
        conf.asdict.return_value = kwargs.get("asdict", {})
        return conf

    @patch("CSET.loaders.verification.get_models")
    def test_load_yields_no_recipes_when_no_scores_selected(self, mock_get_models):
        """Test some code."""
        mock_get_models.return_value = [
            {"name": "base", "id": 1},
            {"name": "other", "id": 2},
        ]
        conf = self.make_conf()

        assert list(load(conf)) == []
        mock_get_models.assert_called_once_with(conf.asdict.return_value)

    @patch("CSET.loaders.verification.get_models")
    def test_load_yields_spatial_score_recipes(self, mock_get_models):
        """Test some code."""
        mock_get_models.return_value = [
            {"name": "base_model", "id": 10},
            {"name": "other_model", "id": 20},
        ]
        conf = self.make_conf(
            SCORES_SPATIAL_RMSE=True,
            SCORES_SPATIAL_MAE=True,
            SURFACE_FIELDS=["v1", "v2"],
            SPATIAL_SURFACE_FIELD_METHOD=["SEQ", "AVE"],
            SELECT_SUBAREA=True,
            SUBAREA_TYPE="UK",
            SUBAREA_EXTENT=[0, 1, 2, 3],
            asdict={"dummy": "value"},
        )

        recipes = list(load(conf))

        assert len(recipes) == 8
        for recipe in recipes:
            assert isinstance(recipe, RawRecipe)
            assert recipe.recipe == "surface_difference_scores.yaml"
            assert recipe.variables["BASE_MODEL"] == "base_model"
            assert recipe.variables["OTHER_MODEL"] == "other_model"
            assert recipe.variables["SUBAREA_TYPE"] == "UK"
            assert recipe.variables["SUBAREA_EXTENT"] == [0, 1, 2, 3]
            assert recipe.model_ids == [10, 20]

        mock_get_models.assert_called_once_with(conf.asdict.return_value)

    @patch("CSET.loaders.verification.get_models")
    def test_load_yields_timeseries_score_recipes(self, mock_get_models):
        """Test some code."""
        mock_get_models.return_value = [
            {"name": "reference", "id": 1},
            {"name": "comparison", "id": 2},
        ]
        conf = self.make_conf(
            SCORES_TIMESERIES_RMSE=True,
            SCORES_TIMESERIES_PC=True,
            SURFACE_FIELDS=["t2m"],
            SELECT_SUBAREA=False,
            asdict={"dummy": "value"},
        )

        recipes = list(load(conf))

        assert len(recipes) == 2
        assert {recipe.recipe for recipe in recipes} == {
            "timeseries_surface_difference_scores.yaml"
        }

        for recipe in recipes:
            assert isinstance(recipe, RawRecipe)
            assert recipe.variables["BASE_MODEL"] == "reference"
            assert recipe.variables["OTHER_MODEL"] == "comparison"
            assert recipe.variables["SUBAREA_TYPE"] is None
            assert recipe.variables["SUBAREA_EXTENT"] is None
            assert recipe.model_ids == [1, 2]

        score_methods = {recipe.variables["SCORES_METHOD"] for recipe in recipes}
        assert score_methods == {"RMSE", "correlation_pearsonr"}
