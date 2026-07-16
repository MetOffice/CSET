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


def load(conf: Config):
    """Yield recipes from the given workflow configuration."""
    # Load a list of model detail dictionaries.
    models = get_models(conf.asdict())
    # Models are listed in order, so model 1 is the first element.

    if conf.SCORES_RMSE_SPATIAL or conf.SCORES_ALL:
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

    if conf.SCORES_RMSE_TIMESERIES or conf.SCORES_ALL:
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
