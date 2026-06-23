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

    # Surface timeseries
    if conf.HOURLY_PRECIPITATION_DFSS:
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
                    "SUBAREA_NAME": conf.SUBAREA_NAME if conf.SELECT_SUBAREA else "",
                },
                model_ids=[model["id"] for model in models],
                aggregation=False,
            )
