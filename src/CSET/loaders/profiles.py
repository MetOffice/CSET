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

"""Load profile recipes."""

import itertools

from CSET.recipes import Config, RawRecipe, get_models


def load(conf: Config):
    """Yield recipes from the given workflow configuration."""
    # Load a list of model detail dictionaries.
    models = get_models(conf.asdict())

    # Pressure level fields.
    if conf.PROFILE_PLEVEL:
        for field, method in itertools.product(
            conf.PRESSURE_LEVEL_FIELDS,
            conf.SPATIAL_PLEVEL_FIELD_METHOD,
        ):
            yield RawRecipe(
                recipe="generic_level_domain_mean_vertical_profile_series.yaml",
                variables={
                    "VARNAME": field,
                    "LEVELTYPE": "pressure",
                    "MODEL_NAME": [model["name"] for model in models],
                    "METHOD": method,
                    "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                    "SUBAREA_EXTENT": conf.SUBAREA_EXTENT
                    if conf.SELECT_SUBAREA
                    else None,
                },
                model_ids=[model["id"] for model in models],
                aggregation=False,
            )

    # Model level fields
    if conf.PROFILE_MLEVEL:
        for field, method in itertools.product(
            conf.MODEL_LEVEL_FIELDS,
            conf.SPATIAL_MLEVEL_FIELD_METHOD,
        ):
            yield RawRecipe(
                recipe="generic_level_domain_mean_vertical_profile_series.yaml",
                variables={
                    "VARNAME": field,
                    "LEVELTYPE": "model_level_number",
                    "MODEL_NAME": [model["name"] for model in models],
                    "METHOD": method,
                    "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                    "SUBAREA_EXTENT": conf.SUBAREA_EXTENT
                    if conf.SELECT_SUBAREA
                    else None,
                },
                model_ids=[model["id"] for model in models],
                aggregation=False,
            )

    # Create a list of case aggregation types.
    AGGREGATION_TYPES = ["lead_time", "hour_of_day", "validity_time", "all"]

    # Pressure level fields.
    for atype, field in itertools.product(
        AGGREGATION_TYPES, conf.PRESSURE_LEVEL_FIELDS
    ):
        if conf.PROFILE_PLEVEL_AGGREGATION[AGGREGATION_TYPES.index(atype)]:
            yield RawRecipe(
                recipe=f"generic_level_domain_mean_vertical_profile_series_case_aggregation_{atype}.yaml",
                variables={
                    "VARNAME": field,
                    "LEVELTYPE": "pressure",
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
    for atype, field in itertools.product(AGGREGATION_TYPES, conf.MODEL_LEVEL_FIELDS):
        if conf.PROFILE_MLEVEL_AGGREGATION[AGGREGATION_TYPES.index(atype)]:
            yield RawRecipe(
                recipe=f"generic_level_domain_mean_vertical_profile_series_case_aggregation_{atype}.yaml",
                variables={
                    "VARNAME": field,
                    "LEVELTYPE": "model_level_number",
                    "MODEL_NAME": [model["name"] for model in models],
                    "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                    "SUBAREA_EXTENT": conf.SUBAREA_EXTENT
                    if conf.SELECT_SUBAREA
                    else None,
                },
                model_ids=[model["id"] for model in models],
                aggregation=True,
            )
