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

"""Load power spectrum recipes."""

import itertools

from CSET.recipes import Config, RawRecipe, get_models


def load(conf: Config):
    """Yield recipes from the given workflow configuration."""
    # Load a list of model detail dictionaries.
    models = get_models(conf.asdict())

    # Surface (2D) fields.
    if conf.SPECTRUM_SURFACE_FIELD:
        for field in conf.SURFACE_FIELDS:
            yield RawRecipe(
                recipe="generic_surface_power_spectrum_series.yaml",
                variables={
                    "VARNAME": field,
                    "MODEL_NAME": [model["name"] for model in models],
                    "SEQUENCE": "time"
                    if conf.SPECTRUM_SURFACE_FIELD_SEQUENCE
                    else "realization",
                    "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                    "SUBAREA_EXTENT": conf.SUBAREA_EXTENT
                    if conf.SELECT_SUBAREA
                    else None,
                    "SUBAREA_NAME": conf.SUBAREA_NAME if conf.SELECT_SUBAREA else "",
                    "SPECTRUM_SURFACE_FIELD_SEQUENCE": conf.SPECTRUM_SURFACE_FIELD_SEQUENCE,
                },
                model_ids=[model["id"] for model in models],
                aggregation=False,
            )

    # Pressure level fields.
    if conf.SPECTRUM_PLEVEL_FIELD:
        for field, plevel in itertools.product(
            conf.PRESSURE_LEVEL_FIELDS,
            conf.PRESSURE_LEVELS,
        ):
            yield RawRecipe(
                recipe="generic_plevel_power_spectrum_series.yaml",
                variables={
                    "VARNAME": field,
                    "LEVELTYPE": "pressure",
                    "LEVEL": plevel,
                    "MODEL_NAME": [model["name"] for model in models],
                    "SEQUENCE": "time"
                    if conf.SPECTRUM_PLEVEL_FIELD_SEQUENCE
                    else "realization",
                    "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                    "SUBAREA_EXTENT": conf.SUBAREA_EXTENT
                    if conf.SELECT_SUBAREA
                    else None,
                    "SUBAREA_NAME": conf.SUBAREA_NAME if conf.SELECT_SUBAREA else "",
                    "SPECTRUM_PLEVEL_FIELD_SEQUENCE": conf.SPECTRUM_PLEVEL_FIELD_SEQUENCE,
                },
                model_ids=[model["id"] for model in models],
                aggregation=False,
            )

    # Model level fields
    if conf.SPECTRUM_MLEVEL_FIELD:
        for field, mlevel in itertools.product(
            conf.MODEL_LEVEL_FIELDS,
            conf.MODEL_LEVELS,
        ):
            yield RawRecipe(
                recipe="generic_mlevel_power_spectrum_series.yaml",
                variables={
                    "VARNAME": field,
                    "LEVELTYPE": "model_level_number",
                    "LEVEL": mlevel,
                    "MODEL_NAME": [model["name"] for model in models],
                    "SEQUENCE": "time"
                    if conf.SPECTRUM_MLEVEL_FIELD_SEQUENCE
                    else "realization",
                    "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                    "SUBAREA_EXTENT": conf.SUBAREA_EXTENT
                    if conf.SELECT_SUBAREA
                    else None,
                    "SUBAREA_NAME": conf.SUBAREA_NAME if conf.SELECT_SUBAREA else "",
                    "SPECTRUM_MLEVEL_FIELD_SEQUENCE": conf.SPECTRUM_MLEVEL_FIELD_SEQUENCE,
                },
                model_ids=[model["id"] for model in models],
                aggregation=False,
            )

    # Create a list of case aggregation types.
    AGGREGATION_TYPES = ["all", "rolling"]

    # Surface (2D) fields.
    for atype, field in itertools.product(AGGREGATION_TYPES, conf.SURFACE_FIELDS):
        if conf.SPECTRUM_SURFACE_FIELD_AGGREGATION[AGGREGATION_TYPES.index(atype)]:
            yield RawRecipe(
                recipe=f"generic_surface_power_spectrum_series_mean_{atype}.yaml",
                variables={
                    "VARNAME": field,
                    "MODEL_NAME": [model["name"] for model in models],
                    "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                    "SUBAREA_EXTENT": conf.SUBAREA_EXTENT
                    if conf.SELECT_SUBAREA
                    else None,
                    "WINDOW_LEN_SURFACE": conf.WINDOW_LEN_SURFACE
                    if atype == "rolling"
                    else None,
                },
                model_ids=[model["id"] for model in models],
                aggregation=True,
            )

    # Pressure level fields.
    for atype, field, plevel in itertools.product(
        AGGREGATION_TYPES, conf.PRESSURE_LEVEL_FIELDS, conf.PRESSURE_LEVELS
    ):
        if conf.SPECTRUM_PLEVEL_FIELD_AGGREGATION[AGGREGATION_TYPES.index(atype)]:
            # Build the variables dict *without* WINDOW_LEN_PLEVEL first
            variables = {
                "VARNAME": field,
                "LEVELTYPE": "pressure",
                "LEVEL": [plevel],
                "MODEL_NAME": [model["name"] for model in models],
                "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                "SUBAREA_EXTENT": conf.SUBAREA_EXTENT if conf.SELECT_SUBAREA else None,
            }

            # Add WINDOW_LEN_PLEVEL *only if* rolling
            if atype == "rolling":
                variables["WINDOW_LEN_PLEVEL"] = conf.WINDOW_LEN_PLEVEL
            else:
                variables["WINDOW_LEN_PLEVEL"] = None

            yield RawRecipe(
                recipe=f"generic_level_power_spectrum_series_plevel_mean_{atype}.yaml",
                variables=variables,
                model_ids=[model["id"] for model in models],
                aggregation=True,
            )

    # Model level fields.
    for atype, field, mlevel in itertools.product(
        AGGREGATION_TYPES, conf.MODEL_LEVEL_FIELDS, conf.MODEL_LEVELS
    ):
        if conf.POWER_SPECTRUM_MLEVEL_FIELD_AGGREGATION[AGGREGATION_TYPES.index(atype)]:
            # Build the variables dict *without* WINDOW_LEN_MLEVEL first
            variables = {
                "VARNAME": field,
                "LEVELTYPE": "model_level_number",
                "LEVEL": [mlevel],
                "MODEL_NAME": [model["name"] for model in models],
                "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                "SUBAREA_EXTENT": conf.SUBAREA_EXTENT if conf.SELECT_SUBAREA else None,
            }

            # Add WINDOW_LEN_MLEVEL *only if* rolling
            if atype == "rolling":
                variables["WINDOW_LEN_MLEVEL"] = conf.WINDOW_LEN_MLEVEL
            else:
                variables["WINDOW_LEN_MLEVEL"] = None

            yield RawRecipe(
                recipe=f"generic_level_power_spectrum_series_mlevel_mean_{atype}.yaml",
                variables=variables,
                model_ids=[model["id"] for model in models],
                aggregation=True,
            )
