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

"""Load spatial difference field recipes."""

import itertools

from CSET.recipes import Config, RawRecipe, get_models


def load(conf: Config):
    """Yield recipes from the given workflow configuration."""
    # Load a list of model detail dictionaries.
    models = get_models(conf.asdict())
    # Models are listed in order, so model 1 is the first element.

    # Surface (2D) fields.
    if conf.SPATIAL_DIFFERENCE_SURFACE_FIELD:
        base_model = models[0]
        for model, field, method in itertools.product(
            models[1:], conf.SURFACE_FIELDS, conf.SPATIAL_SURFACE_FIELD_METHOD
        ):
            yield RawRecipe(
                recipe="surface_spatial_difference.yaml",
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

    # Pressure level fields.
    if conf.SPATIAL_DIFFERENCE_PLEVEL_FIELD:
        base_model = models[0]
        for model, field, plevel, method in itertools.product(
            models[1:],
            conf.PRESSURE_LEVEL_FIELDS,
            conf.PRESSURE_LEVELS,
            conf.SPATIAL_PLEVEL_FIELD_METHOD,
        ):
            yield RawRecipe(
                recipe="level_spatial_difference.yaml",
                variables={
                    "VARNAME": field,
                    "LEVELTYPE": "pressure",
                    "LEVEL": plevel,
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

    # Model level fields.
    if conf.SPATIAL_MLEVEL_DIFFERENCE:
        base_model = models[0]
        for model, field, mlevel, method in itertools.product(
            models[1:],
            conf.MODEL_LEVEL_FIELDS,
            conf.MODEL_LEVELS,
            conf.SPATIAL_MLEVEL_FIELD_METHOD,
        ):
            yield RawRecipe(
                recipe="level_spatial_difference.yaml",
                variables={
                    "VARNAME": field,
                    "LEVELTYPE": "model_level_number",
                    "LEVEL": mlevel,
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
    # Specific diagnostics require their own recipes for traceability. Therefore, these also
    # require individual loaders.

    # Aviation Fog presence.
    if conf.AVIATION_FOG_PRESENCE_SPATIAL_DIFFERENCE:
        base_model = models[0]
        for model in models[1:]:
            yield RawRecipe(
                recipe="aviation_fog_presence_spatial_difference.yaml",
                variables={
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

    # Rain presence.
    if conf.RAIN_PRESENCE_SPATIAL_DIFFERENCE:
        base_model = models[0]
        for model in models[1:]:
            yield RawRecipe(
                recipe="rain_presence_spatial_difference.yaml",
                variables={
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

    # Surface winds on Beaufort Scale.
    if conf.SFC_WIND_BEAUFORT_SCALE_SPATIAL_DIFFERENCE:
        base_model = models[0]
        for model in models[1:]:
            yield RawRecipe(
                recipe="surface_wind_speed_on_beaufort_scale_spatial_difference.yaml",
                variables={
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

    # Daily maximum temperature.
    if conf.DAILY_09_MAXIMUM_TEMPERATURE_SPATIAL_DIFFERENCE:
        base_model = models[0]
        for model in models[1:]:
            yield RawRecipe(
                recipe="daily_09_maximum_temperature_spatial_difference.yaml",
                variables={
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

    # Create a list of case aggregation types.
    AGGREGATION_TYPES = ["lead_time", "hour_of_day", "validity_time", "all"]

    # Surface (2D) fields.
    for model, atype, field in itertools.product(
        models[1:], AGGREGATION_TYPES, conf.SURFACE_FIELDS
    ):
        if conf.SPATIAL_DIFFERENCE_SURFACE_FIELD_AGGREGATION[
            AGGREGATION_TYPES.index(atype)
        ]:
            base_model = models[0]
            yield RawRecipe(
                recipe=f"surface_spatial_difference_case_aggregation_mean_{atype}.yaml",
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
                aggregation=True,
            )

    # Pressure level fields.
    for model, atype, field, plevel in itertools.product(
        models[1:], AGGREGATION_TYPES, conf.PRESSURE_LEVEL_FIELDS, conf.PRESSURE_LEVELS
    ):
        if conf.SPATIAL_DIFFERENCE_PLEVEL_FIELD_AGGREGATION[
            AGGREGATION_TYPES.index(atype)
        ]:
            base_model = models[0]
            yield RawRecipe(
                recipe=f"level_spatial_difference_case_aggregation_mean_{atype}.yaml",
                variables={
                    "VARNAME": field,
                    "LEVELTYPE": "pressure",
                    "LEVEL": plevel,
                    "BASE_MODEL": base_model["name"],
                    "OTHER_MODEL": model["name"],
                    "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                    "SUBAREA_EXTENT": conf.SUBAREA_EXTENT
                    if conf.SELECT_SUBAREA
                    else None,
                },
                model_ids=[base_model["id"], model["id"]],
                aggregation=True,
            )

    # Model level fields.
    for model, atype, field, mlevel in itertools.product(
        models[1:], AGGREGATION_TYPES, conf.MODEL_LEVEL_FIELDS, conf.MODEL_LEVELS
    ):
        if conf.SPATIAL_DIFFERENCE_MLEVEL_FIELD_AGGREGATION[
            AGGREGATION_TYPES.index(atype)
        ]:
            base_model = models[0]
            yield RawRecipe(
                recipe=f"level_spatial_difference_case_aggregation_mean_{atype}.yaml",
                variables={
                    "VARNAME": field,
                    "LEVELTYPE": "model_level_number",
                    "LEVEL": mlevel,
                    "BASE_MODEL": base_model["name"],
                    "OTHER_MODEL": model["name"],
                    "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                    "SUBAREA_EXTENT": conf.SUBAREA_EXTENT
                    if conf.SELECT_SUBAREA
                    else None,
                },
                model_ids=[base_model["id"], model["id"]],
                aggregation=True,
            )
