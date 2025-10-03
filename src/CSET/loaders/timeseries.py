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

"""Load timeseries recipes."""

import itertools

from CSET.recipes import Config, RawRecipe, get_models


def load(conf: Config):
    """Yield recipes from the given workflow configuration."""
    # Load a list of model detail dictionaries.
    models = get_models(conf.asdict())

    # Surface timeseries
    if conf.TIMESERIES_SURFACE_FIELD:
        for field in conf.SURFACE_FIELDS:
            yield RawRecipe(
                recipe="generic_surface_domain_mean_time_series.yaml",
                variables={
                    "VARNAME": field,
                    "MODEL_NAME": [model["name"] for model in models],
                    "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                    "SUBAREA_EXTENT": conf.SUBAREA_EXTENT
                    if conf.SELECT_SUBAREA
                    else None,
                },
                model_ids=[model["id"] for model in models],
                aggregation=False,
            )

    # Pressure level fields.
    if conf.TIMESERIES_PLEVEL_FIELD:
        for field, plevel in itertools.product(
            conf.PRESSURE_LEVEL_FIELDS, conf.PRESSURE_LEVELS
        ):
            yield RawRecipe(
                recipe="generic_level_domain_mean_time_series.yaml",
                variables={
                    "VARNAME": field,
                    "LEVELTYPE": "pressure",
                    "LEVEL": plevel,
                    "MODEL_NAME": [model["name"] for model in models],
                    "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                    "SUBAREA_EXTENT": conf.SUBAREA_EXTENT
                    if conf.SELECT_SUBAREA
                    else None,
                },
                model_ids=[model["id"] for model in models],
                aggregation=False,
            )

    # Model level fields
    if conf.TIMESERIES_MLEVEL_FIELD:
        for field, mlevel in itertools.product(
            conf.MODEL_LEVEL_FIELDS, conf.MODEL_LEVELS
        ):
            yield RawRecipe(
                recipe="generic_level_domain_mean_time_series.yaml",
                variables={
                    "VARNAME": field,
                    "LEVELTYPE": "model_level_number",
                    "LEVEL": mlevel,
                    "MODEL_NAME": [model["name"] for model in models],
                    "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                    "SUBAREA_EXTENT": conf.SUBAREA_EXTENT
                    if conf.SELECT_SUBAREA
                    else None,
                },
                model_ids=[model["id"] for model in models],
                aggregation=False,
            )

    # Aviation Fog presence
    if conf.AVIATION_FOG_PRESENCE_DOMAIN_MEAN_TIMESERIES:
        yield RawRecipe(
            recipe="aviation_fog_presence_domain_mean_time_series.yaml",
            variables={
                "MODEL_NAME": [model["name"] for model in models],
                "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                "SUBAREA_EXTENT": conf.SUBAREA_EXTENT if conf.SELECT_SUBAREA else None,
            },
            model_ids=[model["id"] for model in models],
            aggregation=False,
        )

    # Rain presence
    if conf.RAIN_PRESENCE_DOMAIN_MEAN_TIMESERIES:
        yield RawRecipe(
            recipe="rain_presence_domain_mean_time_series.yaml",
            variables={
                "MODEL_NAME": [model["name"] for model in models],
                "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                "SUBAREA_EXTENT": conf.SUBAREA_EXTENT if conf.SELECT_SUBAREA else None,
            },
            model_ids=[model["id"] for model in models],
            aggregation=False,
        )

    # Air frost presence
    if conf.AIR_FROST_PRESENCE_DOMAIN_MEAN_TIMESERIES:
        yield RawRecipe(
            recipe="air_frost_presence_domain_mean_time_series.yaml",
            variables={
                "MODEL_NAME": [model["name"] for model in models],
                "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                "SUBAREA_EXTENT": conf.SUBAREA_EXTENT if conf.SELECT_SUBAREA else None,
            },
            model_ids=[model["id"] for model in models],
            aggregation=False,
        )
 
    # Thick fog presence
    if conf.THICK_FOG_PRESENCE_DOMAIN_MEAN_TIMESERIES:
        yield RawRecipe(
            recipe="thick_fog_presence_domain_mean_time_series.yaml",
            variables={
                "MODEL_NAME": [model["name"] for model in models],
                "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                "SUBAREA_EXTENT": conf.SUBAREA_EXTENT if conf.SELECT_SUBAREA else None,
            },
            model_ids=[model["id"] for model in models],
            aggregation=False,
        )

    # Snow presence
    if conf.SNOW_PRESENCE_DOMAIN_MEAN_TIMESERIES:
        yield RawRecipe(
            recipe="snow_presence_domain_mean_time_series.yaml",
            variables={
                "MODEL_NAME": [model["name"] for model in models],
                "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                "SUBAREA_EXTENT": conf.SUBAREA_EXTENT if conf.SELECT_SUBAREA else None,
            },
            model_ids=[model["id"] for model in models],
            aggregation=False,
        )

    # Surface winds on Beaufort Scale
    if conf.SFC_WIND_BEAUFORT_SCALE_DOMAIN_MEAN_TIMESERIES:
        yield RawRecipe(
            recipe="surface_wind_speed_on_beaufort_scale_domain_mean_time_series.yaml",
            variables={
                "MODEL_NAME": [model["name"] for model in models],
                "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                "SUBAREA_EXTENT": conf.SUBAREA_EXTENT if conf.SELECT_SUBAREA else None,
            },
            model_ids=[model["id"] for model in models],
            aggregation=False,
        )

    # Create a list of case aggregation types.
    AGGREGATION_TYPES = ["lead_time", "hour_of_day", "validity_time", "all"]

    # Surface (2D) fields.
    for atype, field in itertools.product(AGGREGATION_TYPES, conf.SURFACE_FIELDS):
        if conf.TIMESERIES_SURFACE_FIELD_AGGREGATION[AGGREGATION_TYPES.index(atype)]:
            yield RawRecipe(
                recipe=f"generic_surface_domain_mean_time_series_case_aggregation_{atype}.yaml",
                variables={
                    "VARNAME": field,
                    "MODEL_NAME": [model["name"] for model in models],
                    "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                    "SUBAREA_EXTENT": conf.SUBAREA_EXTENT
                    if conf.SELECT_SUBAREA
                    else None,
                },
                model_ids=[model["id"] for model in models],
                aggregation=True,
            )

    # Pressure level fields.
    for atype, field, plevel in itertools.product(
        AGGREGATION_TYPES, conf.PRESSURE_LEVEL_FIELDS, conf.PRESSURE_LEVELS
    ):
        if conf.TIMESERIES_PLEVEL_FIELD_AGGREGATION[AGGREGATION_TYPES.index(atype)]:
            yield RawRecipe(
                recipe=f"generic_level_domain_mean_time_series_case_aggregation_{atype}.yaml",
                variables={
                    "VARNAME": field,
                    "LEVELTYPE": "pressure",
                    "LEVEL": plevel,
                    "MODEL_NAME": [model["name"] for model in models],
                    "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                    "SUBAREA_EXTENT": conf.SUBAREA_EXTENT
                    if conf.SELECT_SUBAREA
                    else None,
                },
                model_ids=[model["id"] for model in models],
                aggregation=True,
            )

    # Model level fields.
    for atype, field, mlevel in itertools.product(
        AGGREGATION_TYPES, conf.MODEL_LEVEL_FIELDS, conf.MODEL_LEVELS
    ):
        if conf.TIMESERIES_MLEVEL_FIELD_AGGREGATION[AGGREGATION_TYPES.index(atype)]:
            yield RawRecipe(
                recipe=f"generic_level_domain_mean_time_series_case_aggregation_{atype}.yaml",
                variables={
                    "VARNAME": field,
                    "LEVELTYPE": "model_level_number",
                    "LEVEL": mlevel,
                    "MODEL_NAME": [model["name"] for model in models],
                    "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                    "SUBAREA_EXTENT": conf.SUBAREA_EXTENT
                    if conf.SELECT_SUBAREA
                    else None,
                },
                model_ids=[model["id"] for model in models],
                aggregation=True,
            )
