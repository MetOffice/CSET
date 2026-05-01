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

"""Load cardington recipes."""
# long_name='VIS AT 1.5M  (incl precip)         M'
#'SURFACE SENSIBLE  HEAT FLUX     W/M2'
#'SURFACE LATENT HEAT FLUX        W/M2'
#'DEWPOINT AT 1.5M (K)'

from CSET.recipes import Config, RawRecipe, get_models


def height_token(ht: float) -> str:
    """Convert height to the token used in Cardington variable names."""
    # Cardington uses "1p2m" for 1.2 m
    if abs(ht - 1.2) < 1e-9:
        return "1p2m"
    # Integers become "2m", "10m", etc.
    if float(ht).is_integer():
        return f"{int(ht)}m"
    # Fallback for any other non-integer heights (e.g. 0.5 -> "0p5m")
    s = str(ht).replace(".", "p")
    return f"{s}m"


def load(conf: Config):
    """Yield recipes from the given workflow configuration."""
    # Load a list of model detail dictionaries.
    models = get_models(conf.asdict())
    #  base_model = models[0]
    if conf.CARDINGTON_SURFACE_TEMPERATURE_TIME_SERIES:
        base_model = models[0]
        field = "surface_temperature"
        card_label = "Cardington"
        for model in models[1:]:
            yield RawRecipe(
                recipe="cardington_surface_temperature_time_series.yaml",
                variables={
                    "MODEL_NAME": model["name"],
                    "VARNAME": field,
                    "CARDINGTON_LABEL": card_label,
                    "UM_VARNAME": field,
                },
                model_ids=[base_model["id"], model["id"]],
                aggregation=False,
            )
        fields = [("surface_air_pressure", "air_pressure")]
        for model_field, card_field in fields:
            for model in models[1:]:
                yield RawRecipe(
                    recipe="cardington_surface_pressure_time_series.yaml",
                    variables={
                        "MODEL_NAME": model["name"],
                        "VARNAME": card_field,
                        "CARDINGTON_LABEL": card_label,
                        "UM_VARNAME": model_field,
                        "PLOTNAME": model_field,
                    },
                    model_ids=[base_model["id"], model["id"]],
                    aggregation=False,
                )

    if conf.CARDINGTON_WIND_SINGLE_POINT_TIME_SERIES:
        base_model = models[0]
        fields = [
            ("wind_speed", "wind_speed_vector", [2, 10, 25, 50]),
            ("wind_direction", "wind_direction", [2, 10, 25, 50]),
        ]
        for plot_field, card_field, heights in fields:
            for ht in heights:
                card_label = f"Cardington ({ht} m)"
                for model in models[1:]:
                    yield RawRecipe(
                        recipe="cardington_wind_single_point_time_series.yaml",
                        variables={
                            "MODEL_NAME": model["name"],
                            "VARNAME": f"{card_field}_{height_token(ht)}",
                            "CARDINGTON_LABEL": card_label,
                            "UM_U_VARNAME": "x_wind",
                            "UM_V_VARNAME": "y_wind",
                            "PLOT_VARNAME": plot_field,
                            "HEIGHT": ht,
                        },
                        model_ids=[base_model["id"], model["id"]],
                        aggregation=False,
                    )

    if conf.CARDINGTON_SINGLE_POINT_TIME_SERIES:
        base_model = models[0]
        fields = [
            (
                "air temperature",
                "air_temperature",
                "air_temperature_rtd",
                [1.2, 10, 25, 50],
            ),
            (
                "relative humidity",
                "relative_humidity",
                "relative_humidity",
                [1.2, 10, 25, 50],
            ),
            ("dew point", "m01s03i250", "dewpoint_temperature", [1.2, 10, 25, 50]),
            (
                "visibility",
                "m01s03i281",
                {"visibility_belfort", "visibility_vpf730"},
                [2],
            ),
            ("wind gust", "m01s03i463", "wind_speed_max", [2, 10, 25, 50]),
            ("latent heat flux", "m01s03i234", "wq_covariance", [10]),
            (
                "sensible heat flux",
                "m01s03i217",
                {
                    "wt_covariance": "HEIGHT",
                    "air_temperature_rtd": "HEIGHT_EXCEPT_2M",
                    "pressure_barometric": "FIXED",
                },
                [2, 10, 25, 50],
            ),
        ]
        for plot_field, model_field, card_field, heights in fields:
            for ht in heights:
                card_label = f"Cardington ({ht} m)"
                varname = f"{card_field}_{height_token(ht)}"
                for model in models[1:]:
                    if "latent" in plot_field:
                        yield RawRecipe(
                            recipe="cardington_latent_heat_single_point_time_series.yaml",
                            variables={
                                "MODEL_NAME": model["name"],
                                "VARNAME": varname,
                                "CARDINGTON_LABEL": card_label,
                                "UM_VARNAME": model_field,
                                "HEIGHT": ht,
                                "PLOTNAME": plot_field,
                            },
                            model_ids=[base_model["id"], model["id"]],
                            aggregation=False,
                        )
                    elif "sensible" in plot_field and isinstance(card_field, dict):
                        card_varnames = []
                        for var, rule in card_field.items():
                            if rule == "HEIGHT":
                                card_varnames.append(f"{var}_{height_token(ht)}")
                            elif rule == "HEIGHT_EXCEPT_2M":
                                if ht == 2:
                                    card_varnames.append(f"{var}_1p2m")
                                else:
                                    card_varnames.append(f"{var}_{height_token(ht)}")
                            elif rule == "FIXED":
                                card_varnames.append(var)
                            else:
                                card_varnames.append(f"{var}_{rule}")
                        yield RawRecipe(
                            recipe="cardington_sensible_heat_single_point_time_series.yaml",
                            variables={
                                "MODEL_NAME": model["name"],
                                "CARDINGTON_LABEL": f"Cardington ({ht} m)",
                                "UM_VARNAME": model_field,  # m01s03i217 (unchanged)
                                "HEIGHT": ht,
                                "PLOTNAME": plot_field,
                                "CARDINGTON_VARNAMES": ",".join(card_varnames),
                            },
                            model_ids=[base_model["id"], model["id"]],
                            aggregation=False,
                        )
                    elif "visibility" in card_field:
                        for vis_var in card_field:
                            yield RawRecipe(
                                recipe="cardington_visibility_single_point_time_series.yaml",
                                variables={
                                    "MODEL_NAME": model["name"],
                                    "VARNAME": f"{vis_var}_{height_token(ht)}",
                                    "CARDINGTON_LABEL": card_label,
                                    "UM_VARNAME": model_field,
                                    "HEIGHT": ht,
                                    "PLOTNAME": plot_field,
                                },
                                model_ids=[base_model["id"], model["id"]],
                                aggregation=False,
                            )
                    elif "temperature" in model_field or "temperature" in card_field:
                        yield RawRecipe(
                            recipe="cardington_temperature_single_point_time_series.yaml",
                            variables={
                                "MODEL_NAME": model["name"],
                                "VARNAME": varname,
                                "CARDINGTON_LABEL": card_label,
                                "UM_VARNAME": model_field,
                                "HEIGHT": ht,
                                "PLOTNAME": plot_field,
                            },
                            model_ids=[base_model["id"], model["id"]],
                            aggregation=False,
                        )
                    elif "gust" in plot_field:
                        yield RawRecipe(
                            recipe="cardington_wind_gust_single_point_time_series.yaml",
                            variables={
                                "MODEL_NAME": model["name"],
                                "VARNAME": varname,
                                "CARDINGTON_LABEL": card_label,
                                "UM_VARNAME": model_field,
                                "HEIGHT": ht,
                                "PLOTNAME": plot_field,
                            },
                            model_ids=[base_model["id"], model["id"]],
                            aggregation=False,
                        )
                    else:
                        yield RawRecipe(
                            recipe="cardington_single_point_time_series.yaml",
                            variables={
                                "MODEL_NAME": model["name"],
                                "VARNAME": varname,
                                "CARDINGTON_LABEL": card_label,
                                "UM_VARNAME": model_field,
                                "HEIGHT": ht,
                                "PLOTNAME": plot_field,
                            },
                            model_ids=[base_model["id"], model["id"]],
                            aggregation=False,
                        )
