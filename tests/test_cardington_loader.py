# © Crown copyright, Met Office (2022-2025) and CSET contributors.
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

"""Tests for the Cardington recipe loader."""

import pytest

from CSET.loaders import cardington
from CSET.recipes import Config

MODELS = [
    {"id": 2, "name": "Cardington"},
    {"id": 1, "name": "RAL3-LFRic"},
]


def _load_recipes(monkeypatch, **config):
    """Load Cardington recipes using a minimal two-model configuration."""
    monkeypatch.setattr(cardington, "get_models", lambda _: MODELS)
    variables = {
        "CARDINGTON_SINGLE_POINT_TIME_SERIES": True,
        "CARDINGTON_NET_DOWNWELLING_RADIATIVE_FLUX_SINGLE_POINT_TIME_SERIES": True,
        "CARDINGTON_TOTAL_NET_RADIATIVE_FLUX_SINGLE_POINT_TIME_SERIES": True,
        **config,
    }
    return list(cardington.load(Config(variables)))


def _find_recipe(recipes, recipe_name, **variables):
    """Return the unique recipe matching its name and selected variables."""
    matches = [
        recipe
        for recipe in recipes
        if recipe.recipe == recipe_name
        and all(recipe.variables.get(key) == value for key, value in variables.items())
    ]
    assert len(matches) == 1, (
        f"Expected one {recipe_name!r} recipe matching {variables!r}; "
        f"found {len(matches)}."
    )
    return matches[0]


@pytest.mark.parametrize(
    ("height", "expected"),
    [
        (1.2, "1p2m"),
        (2, "2m"),
        (10, "10m"),
        (0.5, "0p5m"),
    ],
)
def test_height_token(height, expected):
    """Cardington heights are converted to the variable-name token format."""
    assert cardington.height_token(height) == expected


def test_loader_sets_model_names_and_ids(monkeypatch):
    """Recipes use Cardington first and the forecast model second."""
    recipes = _load_recipes(monkeypatch)
    recipe = recipes[0]

    assert recipe.model_ids == [2, 1]
    assert recipe.variables["OBS_NAME"] == "Cardington"
    assert recipe.variables["MODEL_NAME"] == "RAL3-LFRic"
    assert recipe.aggregation is False


def test_surface_temperature_metadata(monkeypatch):
    """Surface temperature uses the verified 2 m Cardington metadata height."""
    recipes = _load_recipes(monkeypatch)
    recipe = _find_recipe(
        recipes,
        "cardington_generic_single_point_time_series.yaml",
        OBS_VARNAME="surface_temperature",
    )

    assert recipe.variables["VARNAME"] == "grid_surface_temperature"
    assert recipe.variables["OBS_HEIGHT"] == 2
    assert recipe.variables["UNITS"] == "°C"


def test_surface_pressure_metadata(monkeypatch):
    """Barometric pressure uses the verified 1.5 m Cardington metadata height."""
    recipes = _load_recipes(monkeypatch)
    recipe = _find_recipe(
        recipes,
        "cardington_generic_single_point_time_series.yaml",
        OBS_VARNAME="pressure_barometric",
    )

    assert recipe.variables["VARNAME"] == "surface_air_pressure"
    assert recipe.variables["OBS_HEIGHT"] == 1.5
    assert recipe.variables["UNITS"] == "hPa"


def test_wind_recipe_variables(monkeypatch):
    """Wind recipes request the Cardington observation and LFRic U/V components."""
    recipes = _load_recipes(monkeypatch)
    recipe = _find_recipe(
        recipes,
        "cardington_wind_single_point_time_series.yaml",
        OBS_VARNAME="wind_speed_vector_2m",
    )

    assert recipe.variables["U_VARNAME"] == "x_wind"
    assert recipe.variables["V_VARNAME"] == "y_wind"
    assert recipe.variables["OBS_HEIGHT"] == 2
    assert recipe.variables["PLOT_VARNAME"] == "wind_speed"


def test_net_radiation_observation_variables(monkeypatch):
    """Net SW and LW recipes use the var_names present in Cardington files."""
    recipes = _load_recipes(monkeypatch)

    shortwave = _find_recipe(
        recipes,
        "cardington_net_downwelling_radiative_flux_time_series.yaml",
        PLOT_VARNAME="shortwave",
    )
    assert shortwave.variables["OBS_DN"] == "swrad_downwelling"
    assert shortwave.variables["OBS_UP"] == "swrad_upwelling"
    assert shortwave.variables["VARNAME"] == "surface_net_downward_shortwave_flux"

    longwave = _find_recipe(
        recipes,
        "cardington_net_downwelling_radiative_flux_time_series.yaml",
        PLOT_VARNAME="longwave",
    )
    assert longwave.variables["OBS_DN"] == "lwrad_downwelling"
    assert longwave.variables["OBS_UP"] == "lwrad_upwelling"
    assert longwave.variables["VARNAME"] == "surface_net_downward_longwave_flux"


def test_total_net_radiation_variables(monkeypatch):
    """Total net radiation compares like-for-like net model and observed fluxes."""
    recipes = _load_recipes(monkeypatch)
    recipe = _find_recipe(
        recipes,
        "cardington_total_net_radiative_flux_time_series.yaml",
    )

    assert recipe.variables["OBS_SW_DN"] == "swrad_downwelling"
    assert recipe.variables["OBS_SW_UP"] == "swrad_upwelling"
    assert recipe.variables["OBS_LW_DN"] == "lwrad_downwelling"
    assert recipe.variables["OBS_LW_UP"] == "lwrad_upwelling"
    assert recipe.variables["MODEL_SW"] == "surface_net_downward_shortwave_flux"
    assert recipe.variables["MODEL_LW"] == "surface_net_downward_longwave_flux"


def test_cardington_loader_requires_exactly_one_cardington_model(monkeypatch):
    """Loader rejects configurations without exactly one Cardington input."""
    monkeypatch.setattr(
        cardington,
        "get_models",
        lambda _: [
            {"id": 1, "name": "RAL3-LFRic"},
            {"id": 3, "name": "RAL3-UM"},
        ],
    )

    conf = Config({"CARDINGTON_SINGLE_POINT_TIME_SERIES": True})
    with pytest.raises(ValueError, match="Exactly one Cardington input"):
        list(cardington.load(conf))


def test_cardington_loader_requires_exactly_one_forecast_model(monkeypatch):
    """Loader rejects configurations without exactly one comparison forecast model."""
    monkeypatch.setattr(
        cardington,
        "get_models",
        lambda _: [
            {"id": 2, "name": "Cardington"},
            {"id": 1, "name": "RAL3-LFRic"},
            {"id": 3, "name": "RAL3-UM"},
        ],
    )

    conf = Config({"CARDINGTON_SINGLE_POINT_TIME_SERIES": True})
    with pytest.raises(ValueError, match="Exactly one forecast model"):
        list(cardington.load(conf))


def test_loader_disabled_yields_no_recipes(monkeypatch):
    """The Cardington loader is inactive when its workflow switch is false."""
    monkeypatch.setattr(cardington, "get_models", lambda _: MODELS)
    conf = Config({"CARDINGTON_SINGLE_POINT_TIME_SERIES": False})

    assert list(cardington.load(conf)) == []
