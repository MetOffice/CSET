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

"""Load cellstats recipes."""

import itertools

from CSET.recipes import Config, RawRecipe, get_models


def load(conf: Config):
    """Yield recipes from the given workflow configuration."""
    # Load a list of model detail dictionaries.
    models = get_models(conf.asdict())

    FEATURE_TYPES = ["mean", "max", "size", "effective_diameter"]

    if conf.RUN_CELL_TRACKING:
        field = conf.CELLTRACK_SURFACE_FIELD
        for (ftype,) in itertools.product(FEATURE_TYPES):
            index = FEATURE_TYPES.index(ftype)
            features = conf.CALCULATE_CELLSTATS_OPTIONS
            if len(features) > index and features[index]:
                yield RawRecipe(
                    recipe=f"generic_surface_cell_stats_{ftype}_all.yaml",
                    variables={
                        "VARNAME": field,
                        "MODEL_NAME": [model["name"] for model in models],
                        "CELLTRACK_THRESHOLD": conf.CELLTRACK_THRESHOLD,
                    },
                    model_ids=[model["id"] for model in models],
                    aggregation=False,
                )
