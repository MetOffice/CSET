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

from CSET.recipes import Config, RawRecipe, get_models


def _get_scores_spatial_methods(conf):
    """Compile list of the required scores spatial plots."""
    scores_spatial_methods = []
    if conf.SCORES_SPATIAL_RMSE or conf.SCORES_ALL:
        scores_spatial_methods.append("RMSE")
    if conf.SCORES_SPATIAL_AB or conf.SCORES_ALL:
        scores_spatial_methods.append("additive_bias")
    if conf.SCORES_SPATIAL_MAE or conf.SCORES_ALL:
        scores_spatial_methods.append("MAE")
    return scores_spatial_methods


def _get_scores_timeseries_methods(conf):
    """Compile list of the required scores timeseries plots."""
    scores_timeseries_methods = []
    if conf.SCORES_TIMESERIES_RMSE or conf.SCORES_ALL:
        scores_timeseries_methods.append("RMSE")
    if conf.SCORES_TIMESERIES_AB or conf.SCORES_ALL:
        scores_timeseries_methods.append("additive_bias")
    if conf.SCORES_TIMESERIES_MAE or conf.SCORES_ALL:
        scores_timeseries_methods.append("MAE")
    if conf.SCORES_TIMESERIES_PC or conf.SCORES_ALL:
        scores_timeseries_methods.append("correlation_pearsonr")
    return scores_timeseries_methods


def _get_scores_timeseries_methods_model_vs_obs(conf):
    """Compile list of the required scores model vs observations timeseries plots."""
    scores_timeseries_methods_model_vs_obs = []

    if conf.SCORES_TIMESERIES_RMSE_MODEL_VS_OBS or conf.SCORES_ALL_MODEL_VS_OBS:
        scores_timeseries_methods_model_vs_obs.append("RMSE")
    # TODO: uncomment remainder when backend code has been written
    # if conf.SCORES_TIMESERIES_AB_MODEL_VS_OBS or conf.SCORES_ALL_MODEL_VS_OBS:
    #    scores_timeseries_methods_model_vs_obs.append("additive_bias")
    # if conf.SCORES_TIMESERIES_MAE_MODEL_VS_OBS or conf.SCORES_ALL_MODEL_VS_OBS:
    #    scores_timeseries_methods_model_vs_obs.append("MAE")
    # if conf.SCORES_TIMESERIES_PC_MODEL_VS_OBS or conf.SCORES_ALL_MODEL_VS_OBS:
    #    scores_timeseries_methods_model_vs_obs.append("correlation_pearsonr")
    return scores_timeseries_methods_model_vs_obs


def _get_scores_spatial_methods_model_vs_obs(conf):
    """Compile list of the required scores spatial plots."""
    scores_spatial_methods_model_vs_obs = []
    if conf.SCORES_SPATIAL_RMSE_MODEL_VS_OBS or conf.SCORES_ALL_MODEL_VS_OBS:
        scores_spatial_methods_model_vs_obs.append("RMSE")
    # TODO: uncomment remainder when backend code has been written
    # if conf.SCORES_SPATIAL_AB_MODEL_VS_OBS or conf.SCORES_ALL_MODEL_VS_OBS:
    # scores_spatial_methods_model_vs_obs.append("additive_bias")
    # if conf.SCORES_SPATIAL_MAE_MODEL_VS_OBS or conf.SCORES_ALL_MODEL_VS_OBS:
    # scores_spatial_methods_model_vs_obs.append("MAE")
    return scores_spatial_methods_model_vs_obs


def load(conf: Config):
    """Yield recipes from the given workflow configuration."""
    # Load a list of model detail dictionaries.
    models = get_models(conf.asdict())
    if not models:
        return
    # Models are listed in order, so model 1 is the first element.
    base_model = models[0]

    scores_spatial_methods = _get_scores_spatial_methods(conf)
    if scores_spatial_methods:
        # Produce 2D spatial plots of scores metrics.
        for model, field, method, scores_method in itertools.product(
            models[1:],
            conf.SURFACE_FIELDS,
            conf.SPATIAL_SCORES_FIELD_METHOD,
            scores_spatial_methods,
        ):
            preserved_coords = ["time", "grid_latitude", "grid_longitude"]
            method_null = ""
            scores_method_case = "CASE"
            scores_coords_case = ["grid_latitude", "grid_longitude"]
            if scores_method == "RMSE" and method == scores_method_case:
                # Set the preserved coords and collapse method required
                # to produce RMSE spatial plot over an entire case study.
                preserved_coords = scores_coords_case
                method = method_null
            if scores_method == "MAE" and method == scores_method_case:
                # Set the preserved coords and collapse method required
                # to produce MAE spatial plot over an entire case study.
                preserved_coords = scores_coords_case
                method = method_null
            if scores_method == "additive_bias" and method == scores_method_case:
                # Set the preserved coords and collapse method required
                # to produce ME additive bias spatial plot over an entire case study.
                preserved_coords = scores_coords_case
                method = method_null
            yield RawRecipe(
                recipe=f"surface_difference_scores_{scores_method}.yaml",
                variables={
                    "VARNAME": field,
                    "BASE_MODEL": base_model["name"],
                    "OTHER_MODEL": model["name"],
                    "METHOD": method,
                    "PRESERVED_COORDS": preserved_coords,
                    "SUBAREA_NAME": conf.SUBAREA_NAME if conf.SELECT_SUBAREA else "",
                    "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                    "SUBAREA_EXTENT": conf.SUBAREA_EXTENT
                    if conf.SELECT_SUBAREA
                    else None,
                },
                model_ids=[base_model["id"], model["id"]],
                aggregation=False,
            )

    scores_timeseries_methods = _get_scores_timeseries_methods(conf)
    if scores_timeseries_methods:
        # Produce timeseries plots of scores metrics averaged over the domain for each case study.
        for model, field, scores_method in itertools.product(
            models[1:], conf.SURFACE_FIELDS, scores_timeseries_methods
        ):
            yield RawRecipe(
                recipe=f"timeseries_surface_difference_scores_{scores_method}.yaml",
                variables={
                    "VARNAME": field,
                    "BASE_MODEL": base_model["name"],
                    "OTHER_MODEL": model["name"],
                    "SUBAREA_NAME": conf.SUBAREA_NAME if conf.SELECT_SUBAREA else "",
                    "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                    "SUBAREA_EXTENT": conf.SUBAREA_EXTENT
                    if conf.SELECT_SUBAREA
                    else None,
                },
                model_ids=[base_model["id"], model["id"]],
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
                    "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                    "SUBAREA_EXTENT": conf.SUBAREA_EXTENT
                    if conf.SELECT_SUBAREA
                    else None,
                },
                model_ids=[model["id"]],
                aggregation=False,
            )
    scores_timeseries_methods_model_vs_obs = (
        _get_scores_timeseries_methods_model_vs_obs(conf)
    )

    if scores_timeseries_methods_model_vs_obs:
        # Produce model vs observation timeseries plots of scores metrics averaged over the domain for each case study.
        for field, scores_method in itertools.product(
            conf.POINT_OBS_FIELDS, scores_timeseries_methods_model_vs_obs
        ):
            yield RawRecipe(
                recipe=f"timeseries_surface_difference_scores_model_vs_obs_{scores_method}.yaml",
                variables={
                    "VARNAME": field,
                    "MODEL_NAME": ["OBS"] + [model["name"] for model in models],
                    "SUBAREA_NAME": conf.SUBAREA_NAME if conf.SELECT_SUBAREA else "",
                    "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                    "SUBAREA_EXTENT": conf.SUBAREA_EXTENT
                    if conf.SELECT_SUBAREA
                    else None,
                },
                model_ids=["OBS"] + [model["id"] for model in models],
                aggregation=False,
            )

    scores_spatial_methods_model_vs_obs = _get_scores_spatial_methods_model_vs_obs(conf)
    if scores_spatial_methods_model_vs_obs:
        # Produce 2D spatial plots of scores metrics.

        for field, model, method, scores_method in itertools.product(
            conf.POINT_OBS_FIELDS,
            models,
            conf.SPATIAL_SCORES_FIELD_METHOD_MODEL_VS_OBS,
            scores_spatial_methods_model_vs_obs,
        ):
            preserved_coords = ["time", "latitude", "longitude"]
            recipe_method = method
            if scores_method == "RMSE" and method == "CASE":
                preserved_coords = ["latitude", "longitude"]
                recipe_method = ""
            # TODO include these when backend code is added
            # if scores_method == "MAE" and method == scores_method_case:
            # Set the preserved coords and collapse method required
            # to produce MAE spatial plot over an entire case study.
            #   preserved_coords = scores_coords_case
            #  method = method_null
            # if scores_method == "additive_bias" and method == scores_method_case:
            # Set the preserved coords and collapse method required
            # to produce ME additive bias spatial plot over an entire case study.
            #   preserved_coords = scores_coords_case
            #   method = method_null

            yield RawRecipe(
                recipe=f"surface_difference_scores_model_vs_obs_{scores_method}.yaml",
                variables={
                    "VARNAME": field,
                    "MODEL_NAME": ["OBS"] + [model["name"]],
                    "METHOD": recipe_method,
                    "PRESERVED_COORDS": preserved_coords,
                    "SUBAREA_NAME": conf.SUBAREA_NAME if conf.SELECT_SUBAREA else "",
                    "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                    "SUBAREA_EXTENT": conf.SUBAREA_EXTENT
                    if conf.SELECT_SUBAREA
                    else None,
                },
                model_ids=["OBS"] + [model["id"]],
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
                    "OTHER_MODEL": model["name"],
                    "PRESERVED_COORDS": ["pressure"],
                    "AGGREGATION_MODE": "Case-study RMSE",
                    "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                    "SUBAREA_EXTENT": conf.SUBAREA_EXTENT
                    if conf.SELECT_SUBAREA
                    else None,
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
                    "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                    "SUBAREA_EXTENT": conf.SUBAREA_EXTENT
                    if conf.SELECT_SUBAREA
                    else None,
                },
                model_ids=[base_model["id"], model["id"]],
                aggregation=False,
            )
