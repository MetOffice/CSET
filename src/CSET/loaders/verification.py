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

"""Load verification recipes."""

import itertools
import logging

from CSET.recipes import Config, RawRecipe, get_models

logger = logging.getLogger(__name__)


CONTINUOUS_METHODS = {
    "RMSE": "RMSE",
    "AB": "additive_bias",
    "MAE": "MAE",
    "PC": "correlation_pearsonr",
}
SPATIAL_METHODS = {k: v for k, v in CONTINUOUS_METHODS.items() if k != "PC"}
CATEGORICAL_METHODS = {"POD": "pod", "ETS": "ets", "FB": "fb", "PFD": "pfd"}


def _get_scores_spatial_methods(conf):
    """Compile list of the required scores spatial plots."""
    scores_spatial_methods = []

    for key, value in SPATIAL_METHODS.items():
        if getattr(conf, f"SCORES_SPATIAL_{key}") or conf.SCORES_ALL:
            scores_spatial_methods.append(value)
    return scores_spatial_methods


def _get_scores_spatial_methods_model_vs_obs(conf):
    """Compile list of the required scores spatial plots."""
    scores_spatial_methods_model_vs_obs = []
    for key, value in SPATIAL_METHODS.items():
        if (
            getattr(conf, f"SCORES_SPATIAL_{key}_MODEL_VS_OBS")
            or conf.SCORES_ALL_MODEL_VS_OBS
        ):
            scores_spatial_methods_model_vs_obs.append(value)
    return scores_spatial_methods_model_vs_obs


def _get_scores_timeseries_methods(conf):
    """Compile list of the required scores timeseries plots."""
    scores_timeseries_methods = []
    for key, value in CONTINUOUS_METHODS.items():
        if getattr(conf, f"SCORES_TIMESERIES_{key}") or conf.SCORES_ALL:
            scores_timeseries_methods.append(value)
    return scores_timeseries_methods


def _get_scores_timeseries_methods_model_vs_obs(conf):
    """Compile list of the required scores model vs observations timeseries plots."""
    scores_timeseries_methods_model_vs_obs = []
    for key, value in CONTINUOUS_METHODS.items():
        if (
            getattr(conf, f"SCORES_TIMESERIES_{key}_MODEL_VS_OBS")
            or conf.SCORES_ALL_MODEL_VS_OBS
        ):
            scores_timeseries_methods_model_vs_obs.append(value)
    return scores_timeseries_methods_model_vs_obs


def _get_scores_timeseries_categorical(conf):
    """List of categorical scores metrics, all model vs obs."""
    scores_timeseries_categorical = []
    for key, value in CATEGORICAL_METHODS.items():
        if getattr(conf, f"SCORES_CATEGORICAL_{key}") or conf.SCORES_ALL_MODEL_VS_OBS:
            scores_timeseries_categorical.append(value)
    return scores_timeseries_categorical


def _collapse_settings(method_from_recipe: str) -> tuple[str, list[str]]:
    """Get the collapse method and preserved coordinates for spatial scores metrics."""
    preserved_coords = ["time", "grid_latitude", "grid_longitude"]
    if method_from_recipe == "CASE":
        preserved_coords.remove("time")
        collapse_method = ""
    elif method_from_recipe == "SEQ":
        collapse_method = ""
    else:
        collapse_method = method_from_recipe
    return collapse_method, preserved_coords


def _subarea_variables(conf):
    """Get the subarea variables required for recipes."""
    if conf.SELECT_SUBAREA:
        subarea_vars = {
            "SUBAREA_NAME": conf.SUBAREA_NAME,
            "SUBAREA_TYPE": conf.SUBAREA_TYPE,
            "SUBAREA_EXTENT": conf.SUBAREA_EXTENT,
        }
    else:
        subarea_vars = {
            "SUBAREA_NAME": "",
            "SUBAREA_TYPE": None,
            "SUBAREA_EXTENT": None,
        }
    return subarea_vars


def load(conf: Config):
    """Yield recipes from the given workflow configuration."""
    # Load a list of model detail dictionaries.
    models = get_models(conf.asdict())
    if not models:
        return
    # Models are listed in order, so model 1 is the first element.
    base_model = models[0]

    scores_spatial_methods = _get_scores_spatial_methods(conf)
    scores_timeseries_methods = _get_scores_timeseries_methods(conf)
    scores_timeseries_methods_model_vs_obs = (
        _get_scores_timeseries_methods_model_vs_obs(conf)
    )
    scores_spatial_methods_model_vs_obs = _get_scores_spatial_methods_model_vs_obs(conf)
    scores_timeseries_categorical = _get_scores_timeseries_categorical(conf)

    subarea_vars = _subarea_variables(conf)

    # Produce 2D spatial plots of scores metrics.
    for model, field, method_from_recipe, scores_method in itertools.product(
        models[1:],
        conf.SURFACE_FIELDS,
        conf.SPATIAL_SCORES_FIELD_METHOD,
        scores_spatial_methods,
    ):
        collapse_method, preserved_coords = _collapse_settings(method_from_recipe)

        yield RawRecipe(
            recipe=f"surface_difference_scores_{scores_method}.yaml",
            variables={
                "VARNAME": field,
                "BASE_MODEL": base_model["name"],
                "OTHER_MODELS": model["name"],
                "COLLAPSE_METHOD": collapse_method,
                "PRESERVED_COORDS": preserved_coords,
                **subarea_vars,
            },
            model_ids=[base_model["id"], model["id"]],
            aggregation=False,
        )

    for field, model, method_from_recipe, scores_method in itertools.product(
        conf.POINT_OBS_FIELDS,
        models,
        conf.SPATIAL_SCORES_FIELD_METHOD_MODEL_VS_OBS,
        scores_spatial_methods_model_vs_obs,
    ):
        collapse_method, preserved_coords = _collapse_settings(method_from_recipe)

        yield RawRecipe(
            recipe=f"surface_scores_model_vs_obs_{scores_method}.yaml",
            variables={
                "VARNAME": field,
                "MODEL_NAME": ["OBS"] + [model["name"]],
                "COLLAPSE_METHOD": collapse_method,
                "PRESERVED_COORDS": preserved_coords,
                **subarea_vars,
            },
            model_ids=["OBS"] + [model["id"]],
            aggregation=False,
        )

    # Produce timeseries plots of scores metrics averaged over the domain for each case study.
    for field, scores_method in itertools.product(
        conf.SURFACE_FIELDS, scores_timeseries_methods
    ):
        yield RawRecipe(
            recipe=f"timeseries_surface_difference_scores_{scores_method}.yaml",
            variables={
                "VARNAME": field,
                "BASE_MODEL": base_model["name"],
                "OTHER_MODELS": [model["name"] for model in models[1:]],
                **subarea_vars,
            },
            model_ids=[base_model["id"]] + [model["id"] for model in models[1:]],
            aggregation=False,
        )

    # Produce model vs observation timeseries plots of scores metrics averaged over the domain for each case study.
    for field, scores_method in itertools.product(
        conf.POINT_OBS_FIELDS, scores_timeseries_methods_model_vs_obs
    ):
        yield RawRecipe(
            recipe=f"timeseries_surface_scores_model_vs_obs_{scores_method}.yaml",
            variables={
                "VARNAME": field,
                "MODEL_NAME": ["OBS"] + [model["name"] for model in models],
                **subarea_vars,
            },
            model_ids=["OBS"] + [model["id"] for model in models],
            aggregation=False,
        )

    # including AGGREGATION_MODE in the variables dictionary to allow for clearer labeling of plots.
    if conf.SCORES_RMSE_VERTICAL_PROFILES:
        for model, field in itertools.product(models[1:], conf.PRESSURE_LEVEL_FIELDS):
            yield RawRecipe(
                recipe="generic_level_rmse_scores_profile.yaml",
                variables={
                    "VARNAME": field,
                    "BASE_MODEL": base_model["name"],
                    "OTHER_MODELS": model["name"],
                    "PRESERVED_COORDS": ["pressure"],
                    "AGGREGATION_MODE": "Case-study RMSE",
                    **subarea_vars,
                },
                model_ids=[base_model["id"], model["id"]],
                aggregation=False,
            )

    # including AGGREGATION_MODE in the variables dictionary to allow for clearer labeling of plots.
    if conf.SCORES_RMSE_VERTICAL_PROFILES_SEQUENCE:
        for model, field in itertools.product(models[1:], conf.PRESSURE_LEVEL_FIELDS):
            yield RawRecipe(
                recipe="generic_level_rmse_scores_profile.yaml",
                variables={
                    "VARNAME": field,
                    "BASE_MODEL": base_model["name"],
                    "OTHER_MODEL": model["name"],
                    "PRESERVED_COORDS": ["time", "pressure"],
                    "AGGREGATION_MODE": "Time-step RMSE",
                    **subarea_vars,
                },
                model_ids=[base_model["id"], model["id"]],
                aggregation=False,
            )

    # Scores categorical metrics
    if scores_timeseries_categorical:
        # Produce timeseries plots of scores categorical metrics for each model.
        for field_and_method, scores_method in itertools.product(
            conf.SCORES_CATEGORICAL_ENTRIES, scores_timeseries_categorical
        ):
            try:
                var, op, value = field_and_method.split(",")
            except ValueError as err:
                logger.exception(
                    f"Invalid value in SCORES_CATEGORICAL_POD_ENTRIES: {field_and_method}",
                    exc_info=err,
                )
                # Skip invalid entry.
                continue

            yield RawRecipe(
                recipe=f"surface_categorical_model_obs_{scores_method}.yaml",
                variables={
                    "VARNAME": var,
                    "MODEL_NAME": ["OBS"] + [model["name"] for model in models],
                    "THRESHOLD": value,
                    "OPERATOR": op,
                    **subarea_vars,
                },
                model_ids=["OBS"] + [model["id"] for model in models],
                aggregation=False,
            )

    if conf.SCORES_CRPS_FOR_ENSEMBLE:
        for model, field in itertools.product(models, conf.SURFACE_FIELDS):
            yield RawRecipe(
                recipe="crps_for_ensemble.yaml",
                variables={
                    "VARNAME": field,
                    "CONTROL_MEMBER": conf.CONTROL_MEMBER,
                    "METHOD": conf.METHOD_FOR_CRPS,
                    **subarea_vars,
                },
                model_ids=[model["id"]],
                aggregation=False,
            )
    scores_timeseries_methods_model_vs_obs = (
        _get_scores_timeseries_methods_model_vs_obs(conf)
    )
