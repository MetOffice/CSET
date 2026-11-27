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
        if conf.PRESET_SUBAREA_DOMAIN:
            subarea_name = conf.PRESET_SUBAREA_DOMAIN_NAME
        else:
            subarea_name = conf.SUBAREA_NAME or ""

        yield RawRecipe(
            recipe="generic_surface_spatial_plot_sequence_gpm_rainfall.yaml",
            model_ids=["GPM"],
            variables={
                "VARNAME": "precipitation_flux",
                "METHOD": "SEQ",
                "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                "SUBAREA_EXTENT": conf.SUBAREA_EXTENT if conf.SELECT_SUBAREA else None,
                "SUBAREA_NAME": subarea_name,
            },
            aggregation=False,
        )
