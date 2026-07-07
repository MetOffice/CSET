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

from CSET.recipes import Config, RawRecipe, get_models


def load(conf: Config):
    """Yield recipes from the given workflow configuration."""
    # Load a list of model detail dictionaries.
    models = get_models(conf.asdict())

    # dfss
    if conf.DFSS:
        for field in conf.SURFACE_FIELDS:
            yield RawRecipe(
                recipe="dfss.yaml",
                variables={
                    "VARNAME": field,
                    "CENTILE_OR_THRESHOLD": conf.CENTILE_OR_THRESHOLD,
                    "CENTILE": conf.CENTILE,
                    "THRESHOLD": conf.THRESHOLD,
                    "$NEIGHBOURHOOD_LENGTHS": conf.NEIGHBOURHOOD_LENGTHS,
                },
                model_ids=[model["id"] for model in models],
                aggregation=False,
            )
