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

    # Basic Quantile-Quantile plots
    if conf.SURFACE_BASIC_QQ_PLOT:
        base_model = models[0]
        for (
            model,
            field,
        ) in itertools.product(models[1:], conf.QQ_SURFACE_FIELDS):
            yield RawRecipe(
                recipe="surface_basic_qq_plot.yaml",
                variables={
                    "VARNAME": field,
                    "BASE_MODEL": base_model["name"],
                    "OTHER_MODEL": model["name"],
                    "COORD_LIST": conf.SURFACE_QQ_COORDINATE_LIST,
                    "PERCENTILES": conf.SURFACE_QQ_PERCENTILES,
                    "ONE_TO_ONE": conf.SURFACE_QQ_ONE_TO_ONE,
                    "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                    "SUBAREA_EXTENT": conf.SUBAREA_EXTENT
                    if conf.SELECT_SUBAREA
                    else None,
                },
                model_ids=[base_model["id"], model["id"]],
                aggregation=False,
            )

    # Level Quantile-Quantile plots
    if conf.LEVEL_BASIC_QQ_PLOT:
        base_model = models[0]
        for model, field, vert_coord, levels in itertools.product(
            models[1:],
            conf.QQ_LEVEL_FIELDS,
            conf.QQ_VERTICAL_COORDINATE,
            conf.QQ_LEVELS,
        ):
            yield RawRecipe(
                recipe="level_basic_qq_plot.yaml",
                variables={
                    "VARNAME": field,
                    "BASE_MODEL": base_model["name"],
                    "OTHER_MODEL": model["name"],
                    "VERTICAL_COORDINATE": vert_coord,
                    "LEVELS": levels,
                    "COORD_LIST": conf.LEVEL_QQ_COORDINATE_LIST,
                    "PERCENTILES": conf.LEVEL_QQ_PERCENTILES,
                    "ONE_TO_ONE": conf.LEVEL_QQ_ONE_TO_ONE,
                    "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                    "SUBAREA_EXTENT": conf.SUBAREA_EXTENT
                    if conf.SELECT_SUBAREA
                    else None,
                },
                model_ids=[base_model["id"], model["id"]],
                aggregation=False,
            )
