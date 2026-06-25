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
    if conf.SCORES_SPATIAL_RMSE:
        scores_spatial_methods.append("RMSE")
    if conf.SCORES_SPATIAL_AB:
        scores_spatial_methods.append("additive_bias")
    if conf.SCORES_SPATIAL_MAE:
        scores_spatial_methods.append("MAE")
    return scores_spatial_methods


def _get_scores_timeseries_methods(conf):
    """Compile list of the required scores timeseries plots."""
    scores_timeseries_methods = []
    if conf.SCORES_TIMESERIES_RMSE:
        scores_timeseries_methods.append("RMSE")
    if conf.SCORES_TIMESERIES_AB:
        scores_timeseries_methods.append("additive_bias")
    if conf.SCORES_TIMESERIES_MAE:
        scores_timeseries_methods.append("MAE")
    if conf.SCORES_TIMESERIES_PC:
        scores_timeseries_methods.append("correlation_pearsonr")
    return scores_timeseries_methods


def load(conf: Config):
    """Yield recipes from the given workflow configuration."""
    # Load a list of model detail dictionaries.
    models = get_models(conf.asdict())
    # Models are listed in order, so model 1 is the first element.

    scores_spatial_methods = _get_scores_spatial_methods(conf)
    if scores_spatial_methods:
        """Produce 2-d spatial plots of scores metrics."""
        base_model = models[0]
        for model, field, method, scores_method in itertools.product(
            models[1:],
            conf.SURFACE_FIELDS,
            conf.SPATIAL_SURFACE_FIELD_METHOD,
            scores_spatial_methods,
        ):
            yield RawRecipe(
                recipe="surface_difference_scores.yaml",
                variables={
                    "VARNAME": field,
                    "BASE_MODEL": base_model["name"],
                    "OTHER_MODEL": model["name"],
                    "METHOD": method,
                    "SCORES_METHOD": scores_method,
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
        """Produce timeseries plots of scores metrics averaged over the domain."""
        base_model = models[0]
        for model, field, scores_method in itertools.product(
            models[1:], conf.SURFACE_FIELDS, scores_timeseries_methods
        ):
            yield RawRecipe(
                recipe="timeseries_surface_difference_scores.yaml",
                variables={
                    "VARNAME": field,
                    "BASE_MODEL": base_model["name"],
                    "OTHER_MODEL": model["name"],
                    "SCORES_METHOD": scores_method,
                    "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                    "SUBAREA_EXTENT": conf.SUBAREA_EXTENT
                    if conf.SELECT_SUBAREA
                    else None,
                },
                model_ids=[base_model["id"], model["id"]],
                aggregation=False,
            )

    if conf.SCORES_RMSE_SPATIAL:
        base_model = models[0]
        for model, field, method in itertools.product(
            models[1:], conf.SURFACE_FIELDS, conf.SPATIAL_SURFACE_FIELD_METHOD
        ):
            yield RawRecipe(
                recipe="surface_rmse_scores.yaml",
                variables={
                    "VARNAME": field,
                    "BASE_MODEL": base_model["name"],
                    "OTHER_MODEL": model["name"],
                    "METHOD": method,
                    "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                    "SUBAREA_EXTENT": conf.SUBAREA_EXTENT
                    if conf.SELECT_SUBAREA
                    else None,
                },
                model_ids=[base_model["id"], model["id"]],
                aggregation=False,
            )

    if conf.SCORES_RMSE_TIMESERIES:
        base_model = models[0]
        for model, field in itertools.product(models[1:], conf.SURFACE_FIELDS):
            yield RawRecipe(
                recipe="timeseries_surface_rmse_scores.yaml",
                variables={
                    "VARNAME": field,
                    "BASE_MODEL": base_model["name"],
                    "OTHER_MODEL": model["name"],
                    "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                    "SUBAREA_EXTENT": conf.SUBAREA_EXTENT
                    if conf.SELECT_SUBAREA
                    else None,
                },
                model_ids=[base_model["id"], model["id"]],
                aggregation=False,
            )
