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

"""Load transect recipes."""

import itertools

from CSET.recipes import Config, RawRecipe, get_models


def load(conf: Config):
    """Yield recipes from the given workflow configuration."""
    # Load a list of model detail dictionaries.
    models = get_models(conf.asdict())

    # Pressure level fields.
    if conf.EXTRACT_PLEVEL_TRANSECT:
        for model, field in itertools.product(
            models,
            conf.PRESSURE_LEVEL_FIELDS,
        ):
            yield RawRecipe(
                recipe="transect.yaml",
                variables={
                    "VARNAME": field,
                    "VERTICAL_COORDINATE": "pressure",
                    "MODEL_NAME": model["name"],
                    "START_COORDS": conf.PLEVEL_TRANSECT_STARTCOORDS,
                    "FINISH_COORDS": conf.PLEVEL_TRANSECT_FINISHCOORDS,
                    "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                    "SUBAREA_EXTENT": conf.SUBAREA_EXTENT
                    if conf.SELECT_SUBAREA
                    else None,
                },
                model_ids=model["id"],
                aggregation=False,
            )

    # Model level fields
    if conf.EXTRACT_MLEVEL_TRANSECT:
        for model, field in itertools.product(
            models,
            conf.MODEL_LEVEL_FIELDS,
        ):
            yield RawRecipe(
                recipe="transect.yaml",
                variables={
                    "VARNAME": field,
                    "VERTICAL_COORDINATE": "model_level_number",
                    "MODEL_NAME": model["name"],
                    "START_COORDS": conf.MLEVEL_TRANSECT_STARTCOORDS,
                    "FINISH_COORDS": conf.MLEVEL_TRANSECT_FINISHCOORDS,
                    "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                    "SUBAREA_EXTENT": conf.SUBAREA_EXTENT
                    if conf.SELECT_SUBAREA
                    else None,
                },
                model_ids=model["id"],
                aggregation=False,
            )
