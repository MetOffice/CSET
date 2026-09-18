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

from CSET.recipes import Config, RawRecipe, get_models


def select_radar_source(input_source_list):
    """Select the preferred radar source from a list of sources."""
    # Preference list for Nimrod sources, with most preferred heading the list.
    nimrod_preference = ["Nimrod2km", "Nimrodxkm", "Nimrod1km"]

    empty_string = ""
    preferred_nimrod = empty_string
    for prefer in reversed(nimrod_preference):
        if any(prefer in source for source in input_source_list):
            preferred_nimrod = prefer
    return preferred_nimrod


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
    if conf.NIMROD_COMP_1KM and conf.NIMROD_WEIGHTS:
        radar_sources.append(
            {
                "name": "Nimrod_1km_weights",
                "id": "Nimrod1km_weights",
                "varname": "Hourly wts accumulation",
            }
        )
    if conf.NIMROD_COMP_2KM and conf.NIMROD_WEIGHTS:
        radar_sources.append(
            {
                "name": "Nimrod_2km_weights",
                "id": "Nimrod2km_weights",
                "varname": "Hourly wts accumulation",
            }
        )
    if conf.NIMROD_COMP_XKM and conf.NIMROD_WEIGHTS:
        radar_sources.append(
            {
                "name": "Nimrod_xkm_weights",
                "id": "Nimrodxkm_weights",
                "varname": "Hourly wts accumulation",
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
    # Load a list of model detail dictionaries.
    models = get_models(conf.asdict())

    # Load the required radar observation sources.
    radar_sources = get_radar_sources(conf)

    # Form the list of accumulated hourly rainfall radar sources.
    accum_radars = [
        radar
        for radar in radar_sources
        if radar["varname"] == "Hourly rain accumulation"
    ]

    # Specify the boundary margin width to use when trimming model fields.
    boundary_margin = 16

    # Surface (2D) fields for Nimrod radar rainfall.
    #
    # These loaders produce 2D plots of both the Nimrod
    # surface rainfall and the Nimrod weights field.
    #
    # The different sources of Nimrod rainfall accumulation have
    # different spatial grids. So each source requires its own
    # recipe to prevent incompatible cubes being created.
    if conf.NIMROD_RADAR_OBS and conf.PROCESS_RADAR_2D and (len(radar_sources) > 0):
        for radar in radar_sources:
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
                    "SUBAREA_NAME": conf.SUBAREA_NAME if conf.SELECT_SUBAREA else "",
                },
                aggregation=False,
            )

    # Radar 2D plots using a common domain between model and radar network.
    if conf.NIMROD_RADAR_OBS and conf.PROCESS_RADAR_2D and (len(accum_radars) > 0):
        radar_source = select_radar_source([source["id"] for source in accum_radars])
        radar_obs_ids = [radar_source]
        radar_wts_ids = [radar_source + "_weights"]
        model_names_list = [model["name"] for model in models]
        model_ids_list = [model["id"] for model in models]
        yield RawRecipe(
            recipe="model_radar_common_domain_2d_radar.yaml",
            variables={
                "MODEL_VARNAME": "surface_microphysical_rainfall_rate",
                "RADAR_VARNAME": "Hourly rain accumulation",
                "MODEL_LABEL": model_names_list[0],
                "RADAR_LABEL": radar_obs_ids[0],
                "MASK_LABEL": radar_wts_ids[0],
                "METHOD": "SEQ",
                "BOUNDARY_MARGIN": boundary_margin,
                "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                "SUBAREA_EXTENT": conf.SUBAREA_EXTENT if conf.SELECT_SUBAREA else None,
                "SUBAREA_NAME": conf.SUBAREA_NAME if conf.SELECT_SUBAREA else "",
            },
            # model_ids=[model_ids_list[0], "Nimrod2km", "Nimrod2km_weights"],
            model_ids=[model_ids_list[0], radar_obs_ids[0], radar_wts_ids[0]],
            aggregation=False,
        )

    # Model rainfall 2D plots using a common domain between model and radar network.
    if conf.NIMROD_RADAR_OBS and conf.PROCESS_RADAR_2D and (len(accum_radars) > 0):
        radar_source = select_radar_source([source["id"] for source in accum_radars])
        radar_obs_ids = [radar_source]
        radar_wts_ids = [radar_source + "_weights"]
        model_names_list = [model["name"] for model in models]
        model_ids_list = [model["id"] for model in models]
        # Loop over the model names.
        for idx, model_use in enumerate(model_names_list):
            yield RawRecipe(
                recipe="model_radar_common_domain_2d_model.yaml",
                variables={
                    "MODEL_VARNAME": "surface_microphysical_rainfall_rate",
                    "RADAR_VARNAME": "Hourly rain accumulation",
                    "MODEL_LABEL": model_use,
                    "RADAR_LABEL": radar_obs_ids[0],
                    "MASK_LABEL": radar_wts_ids[0],
                    "METHOD": "SEQ",
                    "BOUNDARY_MARGIN": boundary_margin,
                    "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                    "SUBAREA_EXTENT": conf.SUBAREA_EXTENT
                    if conf.SELECT_SUBAREA
                    else None,
                    "SUBAREA_NAME": conf.SUBAREA_NAME if conf.SELECT_SUBAREA else "",
                },
                # model_ids=[model_ids_list[0], "Nimrod2km", "Nimrod2km_weights"],
                model_ids=[model_ids_list[idx], radar_obs_ids[0], radar_wts_ids[0]],
                aggregation=False,
            )

    # Histogram sequence rainfall using common domain between
    # model and Nimrod radar observations.
    if (
        conf.NIMROD_RADAR_OBS
        and conf.PROCESS_RADAR_HISTOGRAMS
        and (len(accum_radars) > 0)
    ):
        # Select the radar source to use.
        radar_source = select_radar_source([source["id"] for source in accum_radars])
        radar_obs_ids = [radar_source]
        radar_wts_ids = [radar_source + "_weights"]
        model_names_list = [model["name"] for model in models]
        model_ids_list = [model["id"] for model in models]
        combined_names = model_names_list + radar_obs_ids + radar_wts_ids
        combined_ids = model_ids_list + radar_obs_ids + radar_wts_ids
        yield RawRecipe(
            recipe="radar_common_domain_histogram.yaml",
            variables={
                "MODEL_VARNAME": "surface_microphysical_rainfall_rate",
                "RADAR_VARNAME": "Hourly rain accumulation",
                "RADAR_WTS_VARNAME": "Hourly wts accumulation",
                "ALL_LABEL": combined_names,
                "SEQUENCE": "time",
                "OUTPUTS": "all",
                "BOUNDARY_MARGIN": boundary_margin,
                "TITLE_STRING": "sequence plots",
                "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                "SUBAREA_EXTENT": conf.SUBAREA_EXTENT if conf.SELECT_SUBAREA else None,
                "SUBAREA_NAME": conf.SUBAREA_NAME if conf.SELECT_SUBAREA else "",
            },
            model_ids=combined_ids,
            aggregation=False,
        )

    # Histogram case study rainfall using common domain between
    # model and Nimrod radar observations.
    if (
        conf.NIMROD_RADAR_OBS
        and conf.PROCESS_RADAR_HISTOGRAMS
        and (len(accum_radars) > 0)
    ):
        # Select the radar source to use.
        radar_source = select_radar_source([source["id"] for source in accum_radars])
        radar_obs_ids = [radar_source]
        radar_wts_ids = [radar_source + "_weights"]
        model_names_list = [model["name"] for model in models]
        model_ids_list = [model["id"] for model in models]
        combined_names = model_names_list + radar_obs_ids + radar_wts_ids
        combined_ids = model_ids_list + radar_obs_ids + radar_wts_ids
        yield RawRecipe(
            recipe="radar_common_domain_histogram.yaml",
            variables={
                "MODEL_VARNAME": "surface_microphysical_rainfall_rate",
                "RADAR_VARNAME": "Hourly rain accumulation",
                "RADAR_WTS_VARNAME": "Hourly wts accumulation",
                "ALL_LABEL": combined_names,
                "SEQUENCE": "realization",
                "OUTPUTS": "all",
                "BOUNDARY_MARGIN": boundary_margin,
                "TITLE_STRING": "case study",
                "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                "SUBAREA_EXTENT": conf.SUBAREA_EXTENT if conf.SELECT_SUBAREA else None,
                "SUBAREA_NAME": conf.SUBAREA_NAME if conf.SELECT_SUBAREA else "",
            },
            model_ids=combined_ids,
            aggregation=False,
        )
