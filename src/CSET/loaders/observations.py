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
    if conf.POINT_OBS_SPATIAL:
        for obs_field, method in itertools.product(
            conf.SURFACE_FIELDS, conf.SPATIAL_SURFACE_FIELD_METHOD
        ):
            yield RawRecipe(
                recipe="generic_obs_spatial_plot.yaml",
                variables={
                    "VARNAME": obs_field,
                    "METHOD": method,
                    "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                    "SUBAREA_EXTENT": conf.SUBAREA_EXTENT
                    if conf.SELECT_SUBAREA
                    else None,
                    "SUBAREA_NAME": conf.SUBAREA_NAME if conf.SELECT_SUBAREA else None,
                },
                model_ids="OBS",
                aggregation=False,
            )

        # Spatial plot of model output and scatter point obs.
    if conf.POINT_OBS_MODEL_SPATIAL:
        for model, field, method in itertools.product(
            models, conf.SURFACE_FIELDS, conf.SPATIAL_SURFACE_FIELD_METHOD
        ):
            yield RawRecipe(
                recipe="generic_model_obs_spatial_sequence.yaml",
                variables={
                    "VARNAME": field,
                    "MODEL_NAME": model["name"],
                    "METHOD": method,
                    "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                    "SUBAREA_EXTENT": conf.SUBAREA_EXTENT
                    if conf.SELECT_SUBAREA
                    else None,
                    "SUBAREA_NAME": conf.SUBAREA_NAME if conf.SELECT_SUBAREA else None,
                },
                model_ids=["OBS", model["id"]],
                aggregation=False,
            )

    # Spatial scatter plot of differences between models and obs.
    if conf.POINT_OBS_MODEL_DIFFERENCE:
        for model, field, method in itertools.product(
            models, conf.SURFACE_FIELDS, conf.SPATIAL_SURFACE_FIELD_METHOD
        ):
            yield RawRecipe(
                recipe="generic_model_obs_spatial_difference.yaml",
                variables={
                    "VARNAME": field,
                    "MODEL_NAME": model["name"],
                    "METHOD": method,
                    "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                    "SUBAREA_EXTENT": conf.SUBAREA_EXTENT
                    if conf.SELECT_SUBAREA
                    else None,
                    "SUBAREA_NAME": conf.SUBAREA_NAME if conf.SELECT_SUBAREA else None,
                },
                model_ids=["OBS", model["id"]],
                aggregation=False,
            )

    # Spatial scatter plot of differences between models and obs.
    if conf.POINT_OBS_MODEL_DIFFERENCE:
        for model, field, method in itertools.product(
            models, conf.SURFACE_FIELDS, conf.SPATIAL_SURFACE_FIELD_METHOD
        ):
            yield RawRecipe(
                recipe="generic_model_obs_spatial_difference.yaml",
                variables={
                    "VARNAME": field,
                    "MODEL_NAME": model["name"],
                    "METHOD": method,
                    "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                    "SUBAREA_EXTENT": conf.SUBAREA_EXTENT
                    if conf.SELECT_SUBAREA
                    else None,
                    "SUBAREA_NAME": conf.SUBAREA_NAME if conf.SELECT_SUBAREA else None,
                },
                model_ids=["OBS", model["id"]],
                aggregation=False,
            )

    # Create a list of plot sequence types.
    TSERIES_TYPES = ["", "_bias", "_points"]

    # Timeseries plot comparing models and obs.
    for ttype, field in itertools.product(TSERIES_TYPES, conf.SURFACE_FIELDS):
        index = TSERIES_TYPES.index(ttype)
        tseries = conf.POINT_OBS_MODEL_TIMESERIES
        if len(tseries) > index and tseries[index]:
            yield RawRecipe(
                recipe=f"generic_model_obs_timeseries{ttype}.yaml",
                variables={
                    "VARNAME": field,
                    "MODEL_NAME": ["OBS"] + [model["name"] for model in models],
                    "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                    "SUBAREA_EXTENT": conf.SUBAREA_EXTENT
                    if conf.SELECT_SUBAREA
                    else None,
                    "SUBAREA_NAME": conf.SUBAREA_NAME if conf.SELECT_SUBAREA else None,
                },
                model_ids=["OBS"] + [model["id"] for model in models],
                aggregation=False,
            )

    # Create a list of plot sequence types.
    SEQ_TYPES = ["realization", "station"]

    # Histogram plot comparing models and obs.
    for stype, field in itertools.product(SEQ_TYPES, conf.SURFACE_FIELDS):
        index = SEQ_TYPES.index(stype)
        sequences = conf.POINT_OBS_MODEL_HISTOGRAM
        if len(sequences) > index and sequences[index]:
            yield RawRecipe(
                recipe="generic_model_obs_histogram.yaml",
                variables={
                    "VARNAME": field,
                    "MODEL_NAME": ["OBS"] + [model["name"] for model in models],
                    "SEQUENCE": stype,
                    "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                    "SUBAREA_EXTENT": conf.SUBAREA_EXTENT
                    if conf.SELECT_SUBAREA
                    else None,
                    "SUBAREA_NAME": conf.SUBAREA_NAME if conf.SELECT_SUBAREA else None,
                },
                model_ids=["OBS"] + [model["id"] for model in models],
                aggregation=False,
            )

    # Scatter plot comparing models and obs, comparing all models on same plot
    for stype, field in itertools.product(SEQ_TYPES, conf.SURFACE_FIELDS):
        index = SEQ_TYPES.index(stype)
        sequences = conf.POINT_OBS_MODEL_SCATTER
        if len(sequences) > index and sequences[index]:
            yield RawRecipe(
                recipe="generic_model_obs_scatter.yaml",
                variables={
                    "VARNAME": field,
                    "MODEL_NAME": ["OBS"] + [model["name"] for model in models],
                    "SEQUENCE": stype,
                    "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                    "SUBAREA_EXTENT": conf.SUBAREA_EXTENT
                    if conf.SELECT_SUBAREA
                    else None,
                    "SUBAREA_NAME": conf.SUBAREA_NAME if conf.SELECT_SUBAREA else None,
                    "HEXBIN": False,
                },
                model_ids=["OBS"] + [model["id"] for model in models],
                aggregation=False,
            )

    # Hexbin plot comparing models and obs, looping over all models to generate separate outputs
    for model, stype, field in itertools.product(
        models, SEQ_TYPES, conf.SURFACE_FIELDS
    ):
        index = SEQ_TYPES.index(stype)
        sequences = conf.POINT_OBS_MODEL_HEXBIN
        if len(sequences) > index and sequences[index]:
            yield RawRecipe(
                recipe="generic_model_obs_scatter.yaml",
                variables={
                    "VARNAME": field,
                    "MODEL_NAME": ["OBS", model["name"]],
                    "SEQUENCE": stype,
                    "SUBAREA_TYPE": conf.SUBAREA_TYPE if conf.SELECT_SUBAREA else None,
                    "SUBAREA_EXTENT": conf.SUBAREA_EXTENT
                    if conf.SELECT_SUBAREA
                    else None,
                    "SUBAREA_NAME": conf.SUBAREA_NAME if conf.SELECT_SUBAREA else None,
                    "HEXBIN": True,
                },
                model_ids=["OBS", model["id"]],
                aggregation=False,
            )
