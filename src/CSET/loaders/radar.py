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

"""Load radar observation recipes."""

from types import SimpleNamespace

from CSET.recipes import Config, RawRecipe


def get_radar_sources(conf) -> dict:
    """Load radar observation sources into a single object."""
    # Set initial values for outputs from this function.
    radar_flag = False
    radar_names = []
    radar_ids = []
    radar_varnames = []

    # Append details of required radar observations.
    if conf.NIMROD_COMP_1KM:
        radar_names.append("Nimrod_1km")
        radar_ids.append("Nimrod1km")
        radar_varnames.append("Hourly rain accumulation")
        radar_flag = True
    if conf.NIMROD_COMP_2KM:
        radar_names.append("Nimrod_2km")
        radar_ids.append("Nimrod2km")
        radar_varnames.append("Hourly rain accumulation")
        radar_flag = True
    if conf.NIMROD_COMP_XKM:
        radar_names.append("Nimrod_xkm")
        radar_ids.append("Nimrodxkm")
        radar_varnames.append("Hourly rain accumulation")
        radar_flag = True

    radar_sources = {
        "radar_flag": radar_flag,
        "radar_varnames": radar_varnames,
        "radar_names": radar_names,
        "radar_ids": radar_ids,
    }

    return radar_sources


def load(conf: Config):
    """Yield recipes from the given workflow configuration."""
    # Load the required radar observation sources.
    radar_sources = SimpleNamespace(get_radar_sources(conf))

    # Surface (2D) fields for Nimrod radar rainfall.
    #
    # The different sources of Nimrod rainfall acculumulation have
    # different spatial grids. So each source requires its own yaml
    # realisation to prevent incompatible cubes being created.
    if radar_sources.radar_flag and conf.SPATIAL_SURFACE_FIELD:
        for next in range(len(radar_sources.radar_ids)):
            yield RawRecipe(
                recipe="generic_surface_spatial_plot_sequence_radar_rainfall.yaml",
                model_ids=radar_sources.radar_ids[next],  # -> Becomes $INPUT_PATHS
                variables={
                    "VARNAME": radar_sources.radar_varnames[next],
                    "RADAR_NAME": radar_sources.radar_names[next],
                    "METHOD": "SEQ",
                    "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                    "SUBAREA_EXTENT": conf.SUBAREA_EXTENT
                    if conf.SELECT_SUBAREA
                    else None,
                },
                aggregation=False,
            )

    # Histograms for surface (2D) Nimrod radar rainfall.
    #
    # To get multiple radar sources plotted on the histogram the yaml
    # realisation must be done by passing lists of the radar_ids and
    # the radar_names. As this is a multiline plot, all radar sources
    # share the same radar variable name.
    if radar_sources.radar_flag and conf.HISTOGRAM_SURFACE_FIELD:
        yield RawRecipe(
            recipe="generic_surface_histogram_series.yaml",
            model_ids=radar_sources.radar_ids,  # -> Becomes $INPUT_PATHS
            variables={
                "VARNAME": radar_sources.radar_varnames[0],
                "MODEL_NAME": radar_sources.radar_names,
                "SEQUENCE": "time"
                if conf.HISTOGRAM_SURFACE_FIELD_SEQUENCE
                else "realization",
                "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                "SUBAREA_EXTENT": conf.SUBAREA_EXTENT if conf.SELECT_SUBAREA else None,
            },
            aggregation=False,
        )
