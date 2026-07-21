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


def load(conf: Config):
    """Yield recipes from the given workflow configuration."""
    # Load a list of model detail dictionaries.
    models = get_models(conf.asdict())
    # Models are listed in order, so model 1 is the first element.

    scores_spatial_methods = _get_scores_spatial_methods(conf)
    if scores_spatial_methods:
        # Produce 2D spatial plots of scores metrics.
        base_model = models[0]
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
        base_model = models[0]
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
