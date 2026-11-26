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

"""Load Global Precipitation Measurement, GMP,  recipes."""

from CSET.recipes import Config, RawRecipe


def load(conf: Config):
    """Yield recipes from the given workflow configuration."""
    # Surface (2D) fields for GPM rainfall.
    #
    if conf.GPM_OBS:
        yield RawRecipe(
            recipe="generic_surface_spatial_plot_sequence_gpm_rainfall.yaml",
            model_ids=["GPM"],  # -> Becomes $INPUT_PATHS
            variables={
                "VARNAME": "precipition_flux",
                "GPM_NAME": "GPM",
                "METHOD": "SEQ",
                "SUBAREA_TYPE": "realworld",
                "SUBAREA_EXTENT": [48.0, 62.0, -14.0, 5.0],
                "SUBAREA_NAME": "GPM-UKV",
            },
            aggregation=False,
        )
