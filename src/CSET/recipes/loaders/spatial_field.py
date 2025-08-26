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

"""Load spatial field recipes."""

import itertools

from CSET.recipes import Config, RawRecipe, get_models


def load(conf: Config):
    """Yield recipes from the given workflow configuration."""
    # Load a list of model detail dictionaries.
    models = get_models(conf.asdict())

    # Surface (2D) fields.
    if conf.SPATIAL_SURFACE_FIELD:
        for model, field, method in itertools.product(
            models, conf.SURFACE_FIELDS, conf.SPATIAL_SURFACE_FIELD_METHOD
        ):
            yield RawRecipe(
                recipe="generic_surface_spatial_plot_sequence.yaml",
                model_ids=model["id"],
                variables={
                    "VARNAME": field,
                    "MODEL_NAME": model["name"],
                    "METHOD": method,
                    "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                    "SUBAREA_EXTENT": conf.SUBAREA_EXTENT
                    if conf.SELECT_SUBAREA
                    else None,
                },
                aggregation=False,
            )

    # Pressure level fields.
    if conf.SPATIAL_PLEVEL_FIELD:
        for model, field, plevel, method in itertools.product(
            models,
            conf.PRESSURE_LEVEL_FIELDS,
            conf.PRESSURE_LEVELS,
            conf.SPATIAL_PLEVEL_FIELD_METHOD,
        ):
            yield RawRecipe(
                recipe="generic_level_spatial_plot_sequence.yaml",
                variables={
                    "VARNAME": field,
                    "LEVELTYPE": "pressure",
                    "LEVEL": plevel,
                    "MODEL_NAME": model["name"],
                    "METHOD": method,
                    "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                    "SUBAREA_EXTENT": conf.SUBAREA_EXTENT
                    if conf.SELECT_SUBAREA
                    else None,
                },
                model_ids=model["id"],
                aggregation=False,
            )

    # Model level fields
    if conf.SPATIAL_MLEVEL_FIELD:
        for model, field, mlevel, method in itertools.product(
            models,
            conf.MODEL_LEVEL_FIELDS,
            conf.MODEL_LEVELS,
            conf.SPATIAL_MLEVEL_FIELD_METHOD,
        ):
            yield RawRecipe(
                recipe="generic_level_spatial_plot_sequence.yaml",
                variables={
                    "VARNAME": field,
                    "LEVELTYPE": "model_level_number",
                    "LEVEL": mlevel,
                    "MODEL_NAME": model["name"],
                    "METHOD": method,
                    "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                    "SUBAREA_EXTENT": conf.SUBAREA_EXTENT
                    if conf.SELECT_SUBAREA
                    else None,
                },
                model_ids=model["id"],
                aggregation=False,
            )

    # Rain presence
    if conf.RAIN_PRESENCE_SPATIAL_PLOT:
        for model in models:
            yield RawRecipe(
                recipe="rain_presence_spatial_plot.yaml",
                model_ids=model["id"],
                variables={
                    "MODEL_NAME": model["name"],
                    "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                    "SUBAREA_EXTENT": conf.SUBAREA_EXTENT
                    if conf.SELECT_SUBAREA
                    else None,
                },
                aggregation=False,
            )

    # Surface winds on Beaufort Scale
    if conf.SFC_WIND_BEAUFORT_SCALE_SPATIAL:
        for model in models:
            yield RawRecipe(
                recipe="surface_wind_speed_on_beaufort_scale_spatial_plot.yaml",
                model_ids=model["id"],
                variables={
                    "MODEL_NAME": model["name"],
                    "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                    "SUBAREA_EXTENT": conf.SUBAREA_EXTENT
                    if conf.SELECT_SUBAREA
                    else None,
                },
                aggregation=False,
            )

    # Create a list of case aggregation types.
    AGGREGATION_TYPES = ["lead_time", "hour_of_day", "validity_time", "all"]

    # Surface (2D) fields.
    for model, atype, field in itertools.product(
        models, AGGREGATION_TYPES, conf.SURFACE_FIELDS
    ):
        if conf.SPATIAL_SURFACE_FIELD_AGGREGATION[AGGREGATION_TYPES.index(atype)]:
            yield RawRecipe(
                recipe=f"generic_surface_spatial_plot_sequence_case_aggregation_mean_{atype}.yaml",
                variables={
                    "VARNAME": field,
                    "MODEL_NAME": model["name"],
                    "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                    "SUBAREA_EXTENT": conf.SUBAREA_EXTENT
                    if conf.SELECT_SUBAREA
                    else None,
                },
                model_ids=model["id"],
                aggregation=True,
            )

    # Pressure level fields.
    for model, atype, field, plevel in itertools.product(
        models, AGGREGATION_TYPES, conf.PRESSURE_LEVEL_FIELDS, conf.PRESSURE_LEVELS
    ):
        if conf.SPATIAL_PLEVEL_FIELD_AGGREGATION[AGGREGATION_TYPES.index(atype)]:
            yield RawRecipe(
                recipe=f"generic_level_spatial_plot_sequence_case_aggregation_mean_{atype}.yaml",
                variables={
                    "VARNAME": field,
                    "LEVELTYPE": "pressure",
                    "LEVEL": plevel,
                    "MODEL_NAME": model["name"],
                    "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                    "SUBAREA_EXTENT": conf.SUBAREA_EXTENT
                    if conf.SELECT_SUBAREA
                    else None,
                },
                model_ids=model["id"],
                aggregation=True,
            )

    # Model level fields.
    for model, atype, field, mlevel in itertools.product(
        models, AGGREGATION_TYPES, conf.MODEL_LEVEL_FIELDS, conf.MODEL_LEVELS
    ):
        if conf.SPATIAL_MLEVEL_FIELD_AGGREGATION[AGGREGATION_TYPES.index(atype)]:
            yield RawRecipe(
                recipe=f"generic_level_spatial_plot_sequence_case_aggregation_mean_{atype}.yaml",
                variables={
                    "VARNAME": field,
                    "LEVELTYPE": "model_level_number",
                    "LEVEL": mlevel,
                    "MODEL_NAME": model["name"],
                    "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                    "SUBAREA_EXTENT": conf.SUBAREA_EXTENT
                    if conf.SELECT_SUBAREA
                    else None,
                },
                model_ids=model["id"],
                aggregation=True,
            )
