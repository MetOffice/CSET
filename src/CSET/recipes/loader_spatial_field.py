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
from collections.abc import Generator
from typing import Any

from CSET.recipes import RawRecipe, get_models


def load(v: dict[str, Any]) -> Generator[RawRecipe]:
    """Yield recipes from the given suite configuration."""
    # Load a list of model detail dictionaries.
    models = get_models(v)

    # Surface (2D) fields.
    if v["SPATIAL_SURFACE_FIELD"]:
        for model, field, method in itertools.product(
            models, v["SURFACE_FIELDS"], v["SPATIAL_SURFACE_FIELD_METHOD"]
        ):
            yield RawRecipe(
                recipe="generic_surface_spatial_plot_sequence.yaml",
                model_ids=model["id"],
                variables={
                    "VARNAME": field,
                    "MODEL_NAME": model["name"],
                    "METHOD": method,
                    "SUBAREA_TYPE": v["SUBAREA_TYPE"] if v["SELECT_SUBAREA"] else None,
                    "SUBAREA_EXTENT": v["SUBAREA_EXTENT"]
                    if v["SELECT_SUBAREA"]
                    else None,
                },
                aggregation=False,
            )

    # Pressure level fields.
    if v["SPATIAL_PLEVEL_FIELD"]:
        for model, field, plevel, method in itertools.product(
            models,
            v["PRESSURE_LEVEL_FIELDS"],
            v["PRESSURE_LEVELS"],
            v["SPATIAL_PLEVEL_FIELD_METHOD"],
        ):
            yield RawRecipe(
                recipe="generic_level_spatial_plot_sequence.yaml",
                variables={
                    "VARNAME": field,
                    "LEVELTYPE": "pressure",
                    "LEVEL": plevel,
                    "MODEL_NAME": model["name"],
                    "METHOD": method,
                    "SUBAREA_TYPE": v["SUBAREA_TYPE"] if v["SELECT_SUBAREA"] else None,
                    "SUBAREA_EXTENT": v["SUBAREA_EXTENT"]
                    if v["SELECT_SUBAREA"]
                    else None,
                },
                model_ids=model["id"],
                aggregation=False,
            )

    # Model level fields
    if v["SPATIAL_MLEVEL_FIELD"]:
        for model, field, mlevel, method in itertools.product(
            models,
            v["MODEL_LEVEL_FIELDS"],
            v["MODEL_LEVELS"],
            v["SPATIAL_MLEVEL_FIELD_METHOD"],
        ):
            yield RawRecipe(
                recipe="generic_level_spatial_plot_sequence.yaml",
                variables={
                    "VARNAME": field,
                    "LEVELTYPE": "model_level_number",
                    "LEVEL": mlevel,
                    "MODEL_NAME": model["name"],
                    "METHOD": method,
                    "SUBAREA_TYPE": v["SUBAREA_TYPE"] if v["SELECT_SUBAREA"] else None,
                    "SUBAREA_EXTENT": v["SUBAREA_EXTENT"]
                    if v["SELECT_SUBAREA"]
                    else None,
                },
                model_ids=model["id"],
                aggregation=False,
            )

    # Create a list of case aggregation types.
    AGGREGATION_TYPES = ["lead_time", "hour_of_day", "validity_time", "all"]

    # Surface (2D) fields.
    for model, atype, field in itertools.product(
        models, AGGREGATION_TYPES, v["SURFACE_FIELDS"]
    ):
        if v["SPATIAL_SURFACE_FIELD_AGGREGATION"][AGGREGATION_TYPES.index(atype)]:
            yield RawRecipe(
                recipe=f"generic_surface_spatial_plot_sequence_case_aggregation_mean_{atype}.yaml",
                variables={
                    "VARNAME": field,
                    "MODEL_NAME": model["name"],
                    "SUBAREA_TYPE": v["SUBAREA_TYPE"] if v["SELECT_SUBAREA"] else None,
                    "SUBAREA_EXTENT": v["SUBAREA_EXTENT"]
                    if v["SELECT_SUBAREA"]
                    else None,
                },
                model_ids=model["id"],
                aggregation=True,
            )

    # Pressure level fields.
    for model, atype, field, plevel in itertools.product(
        models, AGGREGATION_TYPES, v["PRESSURE_LEVEL_FIELDS"], v["PRESSURE_LEVELS"]
    ):
        if v["SPATIAL_PLEVEL_FIELD_AGGREGATION"][AGGREGATION_TYPES.index(atype)]:
            yield RawRecipe(
                recipe=f"generic_level_spatial_plot_sequence_case_aggregation_mean_{atype}.yaml",
                variables={
                    "VARNAME": field,
                    "LEVELTYPE": "pressure",
                    "LEVEL": plevel,
                    "MODEL_NAME": model["name"],
                    "SUBAREA_TYPE": v["SUBAREA_TYPE"] if v["SELECT_SUBAREA"] else None,
                    "SUBAREA_EXTENT": v["SUBAREA_EXTENT"]
                    if v["SELECT_SUBAREA"]
                    else None,
                },
                model_ids=model["id"],
                aggregation=True,
            )

    # Model level fields.
    for model, atype, field, mlevel in itertools.product(
        models, AGGREGATION_TYPES, v["MODEL_LEVEL_FIELDS"], v["MODEL_LEVELS"]
    ):
        if v["SPATIAL_MLEVEL_FIELD_AGGREGATION"][AGGREGATION_TYPES.index(atype)]:
            yield RawRecipe(
                recipe=f"generic_level_spatial_plot_sequence_case_aggregation_mean_{atype}.yaml",
                variables={
                    "VARNAME": field,
                    "LEVELTYPE": "model_level_number",
                    "LEVEL": mlevel,
                    "MODEL_NAME": model["name"],
                    "SUBAREA_TYPE": v["SUBAREA_TYPE"] if v["SELECT_SUBAREA"] else None,
                    "SUBAREA_EXTENT": v["SUBAREA_EXTENT"]
                    if v["SELECT_SUBAREA"]
                    else None,
                },
                model_ids=model["id"],
                aggregation=True,
            )
