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
    if conf.CARDINGTON_SINGLE_POINT_TIME_SERIES:
        cardington_models = [model for model in models if "Cardington" in model["name"]]
        non_cardington_models = [
            model for model in models if "Cardington" not in model["name"]
        ]
        if len(cardington_models) != 1:
            raise ValueError(
                "Exactly one Cardington input must be configured; "
                f"found {len(cardington_models)}."
            )
        if len(non_cardington_models) != 1:
            raise ValueError(
                "Exactly one forecast model must be configured for the "
                "Cardington diagnostics; "
                f"found {len(non_cardington_models)}."
            )
        cardington_model = cardington_models[0]
        um_model = non_cardington_models[0]
        model_ids = [cardington_model["id"], um_model["id"]]

        def make_recipe(recipe, variables):
            return RawRecipe(
                recipe=recipe,
                variables={"MODEL_NAME": um_model["name"], **variables},
                model_ids=model_ids,
                aggregation=False,
            )

        model_field, card_field, plot_field, height = [
            "visibility",
            "m01s03i281",
            "visibility_belfort",
            2,
        ]

        varname = f"{card_field}_{height_token(height)}"
        yield make_recipe(
            recipe="cardington_visibility_single_point_time_series.yaml",
            variables={
                "VARNAME": varname,
                "UM_VARNAME": model_field,
                "HEIGHT": height,
                "PLOTNAME": plot_field,
            },
        )

        field = "surface_temperature"
        yield make_recipe(
            recipe="cardington_surface_temperature_time_series.yaml",
            variables={
                "VARNAME": field,
                "UM_VARNAME": "m01s00i024",
                "PLOTNAME": field,
            },
        )

        fields = [("surface_air_pressure", "air_pressure")]
        for model_field, card_field in fields:
            yield make_recipe(
                recipe="cardington_surface_pressure_time_series.yaml",
                variables={
                    "VARNAME": card_field,
                    "UM_VARNAME": model_field,
                    "PLOTNAME": card_field,
                },
            )

        fields = [
            ("wind_speed", "wind_speed_vector", [2, 10, 25, 50]),
            ("wind_direction", "wind_direction", [2, 10, 25, 50]),
        ]
        for plot_field, card_field, heights in fields:
            for ht in heights:
                yield make_recipe(
                    recipe="cardington_wind_single_point_time_series.yaml",
                    variables={
                        "VARNAME": f"{card_field}_{height_token(ht)}",
                        "UM_U_VARNAME": "x_wind",
                        "UM_V_VARNAME": "y_wind",
                        "PLOT_VARNAME": plot_field,
                        "HEIGHT": ht,
                    },
                )

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
                varname = None
                if isinstance(card_field, str):
                    varname = f"{card_field}_{height_token(ht)}"

                if "latent" in plot_field:
                    yield make_recipe(
                        recipe="cardington_latent_heat_single_point_time_series.yaml",
                        variables={
                            "VARNAME": varname,
                            "UM_VARNAME": model_field,
                            "HEIGHT": ht,
                            "PLOTNAME": plot_field,
                        },
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

                    yield make_recipe(
                        recipe="cardington_sensible_heat_single_point_time_series.yaml",
                        variables={
                            "UM_VARNAME": model_field,  # m01s03i217 (unchanged)
                            "HEIGHT": ht,
                            "PLOTNAME": plot_field,
                            "WT_VARNAMES": ",".join(card_varnames),
                        },
                    )
                elif plot_field == "relative humidity":
                    yield make_recipe(
                        recipe="cardington_relative_humidity_single_point_time_series.yaml",
                        variables={
                            "OBS_NAME": cardington_model["name"],
                            "OBS_VARNAME": varname,
                            "VARNAME": model_field,
                            "STASH": "m01s03i245",
                            "HEIGHT": ht,
                            "PLOT_VARNAME": plot_field,
                        },
                    )
                elif plot_field == "dew point":
                    yield make_recipe(
                        recipe="cardington_dewpoint_temperature_single_point_time_series.yaml",
                        variables={
                            "OBS_NAME": cardington_model["name"],
                            "OBS_VARNAME": varname,
                            "VARNAME": model_field,
                            "STASH": model_field,
                            "HEIGHT": ht,
                            "PLOT_VARNAME": plot_field,
                        },
                    )
                elif "temperature" in model_field or "temperature" in card_field:
                    yield make_recipe(
                        recipe="cardington_temperature_single_point_time_series.yaml",
                        variables={
                            "VARNAME": varname,
                            "UM_VARNAME": model_field,
                            "HEIGHT": ht,
                            "PLOTNAME": plot_field,
                        },
                    )
                elif "gust" in plot_field:
                    yield make_recipe(
                        recipe="cardington_wind_gust_single_point_time_series.yaml",
                        variables={
                            "VARNAME": varname,
                            "UM_VARNAME": model_field,
                            "HEIGHT": ht,
                            "PLOTNAME": plot_field,
                        },
                    )

        # --- Net downwelling radiative flux (shortwave or longwave only) ---
        if conf.CARDINGTON_NET_DOWNWELLING_RADIATIVE_FLUX_SINGLE_POINT_TIME_SERIES:
            flux_types = [
                (
                    "shortwave",
                    "m01s01i201",  # UM SW downwelling
                    "m01s01i202",  # UM SW upwelling
                    "downwelling_shortwave_flux",
                    "upwelling_shortwave_flux",
                ),
                (
                    "longwave",
                    "m01s02i201",  # UM LW downwelling
                    "m01s02i202",  # UM LW upwelling
                    "downwelling_longwave_flux",
                    "upwelling_longwave_flux",
                ),
            ]
            for flux_name, _um_dn, _um_up, card_dn, card_up in flux_types:
                yield make_recipe(
                    recipe="cardington_net_downwelling_radiative_flux_time_series.yaml",
                    variables={
                        "OBS_NAME": cardington_model["name"],
                        "OBS_DN": card_dn,
                        "OBS_UP": card_up,
                        "VARNAME": f"surface_net_downward_{flux_name}_flux",
                        "MODEL_NAME": um_model["name"],
                        "PLOT_VARNAME": flux_name,
                        "OBS_HEIGHT": "2",
                    },
                )

        # --- Total net radiative flux (shortwave + longwave) ---
        if conf.CARDINGTON_TOTAL_NET_RADIATIVE_FLUX_SINGLE_POINT_TIME_SERIES:
            yield make_recipe(
                recipe="cardington_total_net_radiative_flux_time_series.yaml",
                variables={
                    "OBS_NAME": cardington_model["name"],
                    "OBS_SW_DN": "downwelling_shortwave_flux",
                    "OBS_SW_UP": "upwelling_shortwave_flux",
                    "OBS_LW_DN": "downwelling_longwave_flux",
                    "OBS_LW_UP": "upwelling_longwave_flux",
                    "MODEL_SW": "m01s01i235",  # UM net shortwave
                    "MODEL_LW": "m01s02i235",  # UM net longwave
                    "PLOT_VARNAME": "net_radiative_flux",
                    "OBS_HEIGHT": "2",
                },
            )
