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

"""Load power spectra recipes."""

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
                recipe="generic_level_power_spectrum_series.yaml",
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
                recipe="generic_level_power_spectrum_series.yaml",
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
                },
                model_ids=[model["id"] for model in models],
                aggregation=False,
            )
