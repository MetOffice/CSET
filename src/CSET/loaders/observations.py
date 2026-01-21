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

"""Load observations recipes."""

import itertools

from CSET.recipes import Config, RawRecipe, get_models


def load(conf: Config):
    """Yield recipes from the given workflow configuration."""
    # Load a list of model detail dictionaries.
    models = get_models(conf.asdict())

    # Observation scatterplot, no model data.
    if conf.SURFACE_SYNOP_OBS:
        for obs_field in conf.SURFACE_SYNOP_FIELDS:
            yield RawRecipe(
                recipe="generic_obs_scatterplot.yaml",
                variables={
                    "OBSVARNAME": obs_field,
                    "PLOTTING_PROJECTION": conf.PLOTTING_PROJECTION
                    if conf.PLOTTING_PROJECTION
                    else None,
                },
                model_ids="OBS",
                aggregation=False,
            )

    # Scatter plot of differences between models and obs.
    if conf.SURFACE_SYNOP_OBS and conf.SURFACE_SYNOP_DIFFS:
        for model, fields in itertools.product(
            models,
            zip(
                conf.SURFACE_SYNOP_FIELDS,
                conf.SURFACE_SYNOP_MODEL_FIELDS,
                strict=True,
            ),
        ):
            obs_field, model_field = fields
            yield RawRecipe(
                recipe="generic_model_obs_difference_scatterplot.yaml",
                variables={
                    "OBSVARNAME": obs_field,
                    "VARNAME": model_field,
                    "MODEL_NAME": model["name"],
                    "PLOTTING_PROJECTION": conf.PLOTTING_PROJECTION
                    if conf.PLOTTING_PROJECTION
                    else None,
                },
                model_ids=[model["id"], "OBS"],
                aggregation=False,
            )

    # Surface spatial plot NIMROD radar observations, no model data.
    if conf.NIMROD_RADAR_OBS:
        for radar_field in conf.NIMROD_RADAR_FIELDS:
            yield RawRecipe(
                recipe="generic_surface_spatial_plot_sequence_radar.yaml",
                variables={
                    "RADARVARNAME": radar_field,
                    "PLOTTING_PROJECTION": conf.PLOTTING_PROJECTION
                    if conf.PLOTTING_PROJECTION
                    else None,
                },
                model_ids="RADAR_NIMROD",
                aggregation=False,
            )
