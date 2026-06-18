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
    # models = get_models(conf.asdict())

    # Load the required radar observation sources.
    radar_sources = get_radar_sources(conf)

    # Form the list of accumulated hourly rainfall radar sources.
    accum_radars = [
        radar
        for radar in radar_sources
        if radar["varname"] == "Hourly rain accumulation"
    ]

    # Form the list of accumulated hourly weights for Nimrod radar sources.
    wts_radars = [
        radar
        for radar in radar_sources
        if radar["varname"] == "Hourly wts accumulation"
    ]

    #    # Radar masking based on sea mask.
    #    if conf.SPATIAL_SURFACE_FIELD:
    #        for field in conf.SURFACE_FIELDS:
    #            yield RawRecipe(
    #                recipe="sea_mask_for_surface_domain_mean_time_series.yaml",
    #                variables={
    #                    "VARNAME": field,
    #                    "MODEL_NAME": [model["name"] for model in models],
    #                    "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
    #                    "SUBAREA_EXTENT": conf.SUBAREA_EXTENT
    #                    if conf.SELECT_SUBAREA
    #                    else None,
    #                    "SUBAREA_NAME": conf.SUBAREA_NAME if conf.SELECT_SUBAREA else "",
    #                },
    #                model_ids=[model["id"] for model in models],
    #                aggregation=False,
    #            )

    # Radar masking of radar obs based on sea mask.
    if conf.SPATIAL_SURFACE_FIELD:
        field = "Hourly rain accumulation"
        yield RawRecipe(
            recipe="radar_mask_model.yaml",
            variables={
                "VARNAME": field,
                "MODEL_LABEL": "Nimrod2km",
                "MASK_LABEL": "Nimrod2km",
                "METHOD": "SEQ",
                "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                "SUBAREA_EXTENT": conf.SUBAREA_EXTENT if conf.SELECT_SUBAREA else None,
                "SUBAREA_NAME": conf.SUBAREA_NAME if conf.SELECT_SUBAREA else "",
            },
            model_ids=["Nimrod2km", "Nimrod2km_weights"],
            aggregation=False,
        )

    # Radar masking of model rainfall based on sea mask.
    if conf.SPATIAL_SURFACE_FIELD:
        field = "surface_microphysical_rainfall_rate"
        yield RawRecipe(
            recipe="radar_mask_model.yaml",
            variables={
                "VARNAME": field,
                "MODEL_LABEL": "ModelA",
                "MASK_LABEL": "Nimrod2km",
                "METHOD": "SEQ",
                "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                "SUBAREA_EXTENT": conf.SUBAREA_EXTENT if conf.SELECT_SUBAREA else None,
                "SUBAREA_NAME": conf.SUBAREA_NAME if conf.SELECT_SUBAREA else "",
            },
            model_ids=["1", "Nimrod2km_weights"],
            aggregation=False,
        )

    # Surface (2D) fields for model rainfall masked by Nimrod radar.
    #
    # The different sources of Nimrod rainfall accumulation have
    # different spatial grids. So each source requires its own
    # recipe to prevent incompatible cubes being created.
    #    if conf.SPATIAL_SURFACE_FIELD:
    #        radar_source = ["Nimrod_2km"]
    #        for radar in radar_source:
    #            model_labels = [model["id"] for model in models]
    #            radar_label = ["Nimrod2km_weights"]
    #            combined_ids = [model_labels[0]] + radar_label
    #            print("Combined ids is: ", combined_ids)
    #            yield RawRecipe(
    #                recipe="radar_plot_sequence_rainfall.yaml",
    ##                model_ids=radar["id"],  # -> Becomes $INPUT_PATHS
    #                model_ids=combined_ids,
    #                variables={
    ##                    "VARNAME": radar["varname"],
    ##                    "RADAR_NAME": radar["name"],
    #                    "RADAR_NAME": "Nimrod_2km_weights",
    ##                    "MODEL_NAME": [model["name"] for model in models],
    #                    "MODEL_NAME": "ModelA",
    #                    "METHOD": "SEQ",
    #                    "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
    #                    "SUBAREA_EXTENT": conf.SUBAREA_EXTENT
    #                    if conf.SELECT_SUBAREA
    #                    else None,
    #                },
    #                aggregation=False,
    #            )

    # Surface (2D) fields for Nimrod radar rainfall.
    #
    # The different sources of Nimrod rainfall accumulation have
    # different spatial grids. So each source requires its own
    # recipe to prevent incompatible cubes being created.
    if conf.SPATIAL_SURFACE_FIELD:
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
                },
                aggregation=False,
            )

    # Histograms for surface (2D) Nimrod radar hourly accumulated rainfall.
    #
    # To get multiple radar sources plotted on the histogram the
    # recipe must be done by passing lists of the radar_ids and
    # the radar_names. As this is a multiline plot, all radar sources
    # share the same radar variable name.
    if conf.HISTOGRAM_SURFACE_FIELD:
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
                "SUBAREA_NAME": "",
                "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                "SUBAREA_EXTENT": conf.SUBAREA_EXTENT if conf.SELECT_SUBAREA else None,
            },
            aggregation=False,
        )

    # Histograms for surface (2D) Nimrod radar hourly accumulated rainfall.
    #
    # The histograms are produced after the rainfall obs have been masked using
    # the associated Nimrod weights file.
    #
    # To get multiple radar sources plotted on the histogram the
    # recipe must be done by passing lists of the radar_ids and
    # the radar_names. As this is a multiline plot, all radar sources
    # share the same radar variable name.
    if conf.HISTOGRAM_SURFACE_FIELD:
        radar_obs_ids = [radar["id"] for radar in accum_radars]
        radar_wts_ids = [radar["id"] for radar in wts_radars]
        combined_ids = radar_obs_ids + radar_wts_ids
        print(" combined_ids: ", combined_ids)
        yield RawRecipe(
            recipe="radar_dev3.yaml",
            # model_ids -> Becomes $INPUT_PATHS
            # model_ids=[ radar_obs_ids, radar_wts_ids],
            model_ids=combined_ids,
            variables={
                "VARNAME": next(radar["varname"] for radar in accum_radars),
                "ALL_NAME": combined_ids,
                "RADAR_NAME": [radar["id"] for radar in accum_radars],
                "WEIGHTS_NAME": [radar["id"] for radar in wts_radars],
                "SEQUENCE": "time"
                if conf.HISTOGRAM_SURFACE_FIELD_SEQUENCE
                else "realization",
                "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                "SUBAREA_EXTENT": conf.SUBAREA_EXTENT if conf.SELECT_SUBAREA else None,
            },
            aggregation=False,
        )

    # Histograms for surface (2D) Nimrod radar 5 minute rainfall rate.
    if conf.HISTOGRAM_SURFACE_FIELD and conf.NIMROD_COMP_5MIN:
        yield RawRecipe(
            recipe="generic_surface_histogram_series.yaml",
            # model_ids -> Becomes $INPUT_PATHS
            model_ids="Nimrod5min",
            variables={
                "VARNAME": "Rainfall rate Composite",
                "MODEL_NAME": "Nimrod_5min",
                "SEQUENCE": "time"
                if conf.HISTOGRAM_SURFACE_FIELD_SEQUENCE
                else "realization",
                "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                "SUBAREA_EXTENT": conf.SUBAREA_EXTENT if conf.SELECT_SUBAREA else None,
            },
            aggregation=False,
        )

    # Timeseries for surface (2D) Nimrod radar hourly accumulated rainfall.
    #
    # The timeseries are produced after the rainfall obs have been masked using
    # the associated Nimrod weights file.
    #
    # To get multiple radar sources plotted on the histogram the
    # recipe must be done by passing lists of the radar_ids and
    # the radar_names. As this is a multiline plot, all radar sources
    # share the same radar variable name.
    if conf.TIMESERIES_SURFACE_FIELD:
        radar_obs_ids = [radar["id"] for radar in accum_radars]
        radar_wts_ids = [radar["id"] for radar in wts_radars]
        combined_ids = radar_obs_ids + radar_wts_ids
        print(" combined_ids: ", combined_ids)
        yield RawRecipe(
            recipe="radar_masked_mean_time_series.yaml",
            # model_ids -> Becomes $INPUT_PATHS
            # model_ids=[ radar_obs_ids, radar_wts_ids],
            model_ids=combined_ids,
            variables={
                "VARNAME": next(radar["varname"] for radar in accum_radars),
                "ALL_NAME": combined_ids,
                "RADAR_NAME": [radar["id"] for radar in accum_radars],
                "WEIGHTS_NAME": [radar["id"] for radar in wts_radars],
                "SEQUENCE": "realisation",
                #                "SEQUENCE": "time"
                #                if conf.HISTOGRAM_SURFACE_FIELD_SEQUENCE
                #                else "realization",
                "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                "SUBAREA_EXTENT": conf.SUBAREA_EXTENT if conf.SELECT_SUBAREA else None,
            },
            aggregation=False,
        )

    # Timeseries plot of Nimrod hourly surface rainfall accumulation.
    if conf.TIMESERIES_SURFACE_FIELD:
        yield RawRecipe(
            recipe="radar_mean_time_series.yaml",
            # model_ids -> Becomes $INPUT_PATHS
            model_ids=[radar["id"] for radar in accum_radars],
            variables={
                "VARNAME": next(radar["varname"] for radar in accum_radars),
                "MODEL_NAME": [radar["name"] for radar in accum_radars],
                "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                "SUBAREA_EXTENT": conf.SUBAREA_EXTENT if conf.SELECT_SUBAREA else None,
            },
            aggregation=False,
        )

    # Timeseries plot of Nimrod 5 minute rainfall rate.
    if conf.TIMESERIES_SURFACE_FIELD and conf.NIMROD_COMP_5MIN:
        yield RawRecipe(
            recipe="radar_mean_time_series.yaml",
            # model_ids -> Becomes $INPUT_PATHS
            model_ids="Nimrod5min",
            variables={
                "VARNAME": "Rainfall rate Composite",
                "MODEL_NAME": "Nimrod_5min",
                "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                "SUBAREA_EXTENT": conf.SUBAREA_EXTENT if conf.SELECT_SUBAREA else None,
            },
            aggregation=False,
        )
