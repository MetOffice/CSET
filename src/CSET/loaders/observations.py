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

"""Load observations recipes."""

import itertools

from CSET.recipes import Config, RawRecipe, get_models


def load(conf: Config):
    """Yield recipes from the given workflow configuration."""
    # Load a list of model detail dictionaries.
    models = get_models(conf.asdict())

    # Observation spatial plot, no model data.
    if conf.POINT_OBS_SPATIAL:
        for obs_field, method in itertools.product(
            conf.POINT_OBS_FIELDS, conf.POINT_OBS_FIELD_METHOD
        ):
            yield RawRecipe(
                recipe="generic_obs_spatial_plot.yaml",
                variables={
                    "VARNAME": obs_field,
                    "METHOD": method,
                    "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                    "SUBAREA_EXTENT": conf.SUBAREA_EXTENT
                    if conf.SELECT_SUBAREA
                    else None,
                    "SUBAREA_NAME": conf.SUBAREA_NAME if conf.SELECT_SUBAREA else None,
                },
                model_ids="OBS",
                aggregation=False,
            )

    # Spatial plot of model output and overlay of point observations.
    if conf.POINT_OBS_MODEL_SPATIAL:
        for model, field, method in itertools.product(
            models, conf.POINT_OBS_FIELDS, conf.POINT_OBS_FIELD_METHOD
        ):
            yield RawRecipe(
                recipe="generic_model_obs_spatial_sequence.yaml",
                variables={
                    "VARNAME": field,
                    "MODEL_NAME": model["name"],
                    "METHOD": method,
                    "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                    "SUBAREA_EXTENT": conf.SUBAREA_EXTENT
                    if conf.SELECT_SUBAREA
                    else None,
                    "SUBAREA_NAME": conf.SUBAREA_NAME if conf.SELECT_SUBAREA else None,
                },
                model_ids=["OBS", model["id"]],
                aggregation=False,
            )

    # Spatial scatter plot of differences between models and obs.
    if conf.POINT_OBS_MODEL_DIFFERENCE:
        for model, field, method in itertools.product(
            models, conf.POINT_OBS_FIELDS, conf.POINT_OBS_FIELD_METHOD
        ):
            yield RawRecipe(
                recipe="generic_model_obs_spatial_difference.yaml",
                variables={
                    "VARNAME": field,
                    "MODEL_NAME": model["name"],
                    "METHOD": method,
                    "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                    "SUBAREA_EXTENT": conf.SUBAREA_EXTENT
                    if conf.SELECT_SUBAREA
                    else None,
                    "SUBAREA_NAME": conf.SUBAREA_NAME if conf.SELECT_SUBAREA else None,
                },
                model_ids=["OBS", model["id"]],
                aggregation=False,
            )
