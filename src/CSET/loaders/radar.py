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

from CSET.recipes import Config, RawRecipe


def get_radar_sources(conf) -> list[dict]:
    """Load radar observation sources into a single object."""
    # Set initial values for outputs from this function.
    radar_sources = []

    # Append details of required radar observations.
    if conf.NIMROD_COMP_1KM:
        radar_sources.append(
            {
                "name": "Nimrod_1km",
                "id": "Nimrod1km",
                "varname": "Hourly rain accumulation",
            }
        )
    if conf.NIMROD_COMP_2KM:
        radar_sources.append(
            {
                "name": "Nimrod_2km",
                "id": "Nimrod2km",
                "varname": "Hourly rain accumulation",
            }
        )
    if conf.NIMROD_COMP_XKM:
        radar_sources.append(
            {
                "name": "Nimrod_xkm",
                "id": "Nimrodxkm",
                "varname": "Hourly rain accumulation",
            }
        )
    if conf.NIMROD_COMP_5MIN:
        radar_sources.append(
            {
                "name": "Nimrod_5min",
                "id": "Nimrod5min",
                "varname": "Rainfall rate Composite",
            }
        )

    return radar_sources


def load(conf: Config):
    """Yield recipes from the given workflow configuration."""
    # Load the required radar observation sources.
    radar_sources = get_radar_sources(conf)

    for radar in radar_sources:
        # Surface (2D) fields for Nimrod radar rainfall.
        #
        # The different sources of Nimrod rainfall accumulation have
        # different spatial grids. So each source requires its own
        # recipe to prevent incompatible cubes being created.
        if conf.SPATIAL_SURFACE_FIELD:
            yield RawRecipe(
                recipe="generic_surface_spatial_plot_sequence_radar_rainfall.yaml",
                model_ids=radar["id"],  # -> Becomes $INPUT_PATHS
                variables={
                    "VARNAME": radar["varname"],
                    "RADAR_NAME": radar["name"],
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
    # To get multiple radar sources plotted on the histogram the
    # recipe must be done by passing lists of the radar_ids and
    # the radar_names. As this is a multiline plot, all radar sources
    # share the same radar variable name.
    if conf.HISTOGRAM_SURFACE_FIELD:
        accum_radars = [
            radar
            for radar in radar_sources
            if radar["varname"] == "Hourly rain accumulation"
        ]
        yield RawRecipe(
            recipe="generic_surface_histogram_series.yaml",
            # model_ids -> Becomes $INPUT_PATHS
            model_ids=[radar["id"] for radar in accum_radars],
            variables={
                "VARNAME": next(radar["varname"] for radar in accum_radars),
                "MODEL_NAME": [radar["name"] for radar in accum_radars],
                "SEQUENCE": "time"
                if conf.HISTOGRAM_SURFACE_FIELD_SEQUENCE
                else "realization",
                "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                "SUBAREA_EXTENT": conf.SUBAREA_EXTENT if conf.SELECT_SUBAREA else None,
            },
            aggregation=False,
        )
