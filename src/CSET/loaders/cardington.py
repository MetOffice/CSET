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

"""Load Cardington recipes."""

from CSET.recipes import Config, RawRecipe, get_models


def height_token(ht: float) -> str:
    """Convert height to the token used in Cardington variable names."""
    # Cardington uses "1p2m" for 1.2 m.
    if abs(ht - 1.2) < 1e-9:
        return "1p2m"

    # Integers become "2m", "10m", etc.
    if float(ht).is_integer():
        return f"{int(ht)}m"

    # Fallback for other non-integer heights, e.g. 0.5 -> "0p5m".
    return f"{str(ht).replace('.', 'p')}m"


def load(conf: Config):
    """Yield recipes from the given workflow configuration."""
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
        model = non_cardington_models[0]
        model_ids = [cardington_model["id"], model["id"]]

        def make_recipe(recipe, variables):
            return RawRecipe(
                recipe=recipe,
                variables={
                    "MODEL_NAME": model["name"],
                    "OBS_NAME": cardington_model["name"],
                    **variables,
                },
                model_ids=model_ids,
                aggregation=False,
            )

        # Visibility, always at 2m
        model_field = "visibility_in_air"
        card_field = "visibility_belfort"
        plot_field = "visible range"
        height = 2

        obs_varname = f"{card_field}_{height_token(height)}"
        yield make_recipe(
            recipe="cardington_visibility_single_point_time_series.yaml",
            variables={
                "OBS_VARNAME": obs_varname,
                "VARNAME": model_field,
                "HEIGHT": height,
                "PLOTNAME": plot_field,
            },
        )

        # Surface (skin) temperature.
        field = "surface_temperature"
        yield make_recipe(
            recipe="cardington_surface_temperature_time_series.yaml",
            variables={
                "OBS_VARNAME": field,
                "VARNAME": "grid_surface_temperature",
                "PLOTNAME": field,
            },
        )

        # Surface pressure.
        fields = [
            ("surface_air_pressure", "air_pressure"),
        ]
        for model_field, card_field in fields:
            yield make_recipe(
                recipe="cardington_surface_pressure_time_series.yaml",
                variables={
                    "OBS_VARNAME": card_field,
                    "VARNAME": model_field,
                    "PLOTNAME": card_field,
                },
            )

        # Wind speed and direction.
        fields = [
            ("wind_speed", "wind_speed_vector", [2, 10, 25, 50]),
            ("wind_direction", "wind_direction", [2, 10, 25, 50]),
        ]
        for plot_field, card_field, heights in fields:
            for ht in heights:
                yield make_recipe(
                    recipe="cardington_wind_single_point_time_series.yaml",
                    variables={
                        "OBS_VARNAME": (f"{card_field}_{height_token(ht)}"),
                        "U_VARNAME": "x_wind",
                        "V_VARNAME": "y_wind",
                        "PLOT_VARNAME": plot_field,
                        "HEIGHT": ht,
                    },
                )
        # other atmospheric measurements on various levels
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
            (
                "dew point",
                "dew_point_temperature_at_screen_level",
                "dewpoint_temperature",
                [1.2, 10, 25, 50],
            ),
            (
                "wind gust",
                "gust_wind_speed_at_10m",
                "wind_speed_max",
                [2, 10, 25, 50],
            ),
            (
                "latent heat flux",
                "grid_surface_upward_latent_heat_flux",
                "wq_covariance",
                [10],
            ),
            (
                "sensible heat flux",
                "grid_surface_upward_sensible_heat_flux",
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
                obs_varname = None
                if isinstance(card_field, str):
                    obs_varname = f"{card_field}_{height_token(ht)}"
                if "latent" in plot_field:
                    yield make_recipe(
                        recipe=("cardington_latent_heat_single_point_time_series.yaml"),
                        variables={
                            "OBS_VARNAME": obs_varname,
                            "VARNAME": model_field,
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
                        recipe=(
                            "cardington_sensible_heat_single_point_time_series.yaml"
                        ),
                        variables={
                            "VARNAME": model_field,
                            "HEIGHT": ht,
                            "PLOTNAME": plot_field,
                            "WT_VARNAMES": ",".join(card_varnames),
                        },
                    )
                elif plot_field == "relative humidity":
                    yield make_recipe(
                        recipe=(
                            "cardington_relative_humidity_single_point_time_series.yaml"
                        ),
                        variables={
                            "OBS_VARNAME": obs_varname,
                            "VARNAME": model_field,
                            "HEIGHT": ht,
                            "PLOT_VARNAME": plot_field,
                        },
                    )
                elif plot_field == "dew point":
                    yield make_recipe(
                        recipe=(
                            "cardington_dewpoint_temperature_"
                            "single_point_time_series.yaml"
                        ),
                        variables={
                            "OBS_VARNAME": obs_varname,
                            "VARNAME": model_field,
                            "HEIGHT": ht,
                            "PLOT_VARNAME": plot_field,
                        },
                    )
                elif "temperature" in model_field or "temperature" in card_field:
                    yield make_recipe(
                        recipe=("cardington_temperature_single_point_time_series.yaml"),
                        variables={
                            "OBS_VARNAME": obs_varname,
                            "VARNAME": model_field,
                            "HEIGHT": ht,
                            "PLOTNAME": plot_field,
                        },
                    )
                elif "gust" in plot_field:
                    yield make_recipe(
                        recipe=("cardington_wind_gust_single_point_time_series.yaml"),
                        variables={
                            "OBS_VARNAME": obs_varname,
                            "VARNAME": model_field,
                            "HEIGHT": ht,
                            "PLOTNAME": plot_field,
                        },
                    )

        # Net downwelling radiative flux.
        if conf.CARDINGTON_NET_DOWNWELLING_RADIATIVE_FLUX_SINGLE_POINT_TIME_SERIES:
            flux_types = [
                (
                    "shortwave",
                    "downwelling_shortwave_flux",
                    "upwelling_shortwave_flux",
                ),
                (
                    "longwave",
                    "downwelling_longwave_flux",
                    "upwelling_longwave_flux",
                ),
            ]
            for flux_name, card_dn, card_up in flux_types:
                yield make_recipe(
                    recipe=(
                        "cardington_net_downwelling_radiative_flux_time_series.yaml"
                    ),
                    variables={
                        "OBS_DN": card_dn,
                        "OBS_UP": card_up,
                        "VARNAME": (f"surface_net_downward_{flux_name}_flux"),
                        "PLOT_VARNAME": flux_name,
                        "OBS_HEIGHT": "2",
                    },
                )

        # Total net radiative flux.
        if conf.CARDINGTON_TOTAL_NET_RADIATIVE_FLUX_SINGLE_POINT_TIME_SERIES:
            yield make_recipe(
                recipe=("cardington_total_net_radiative_flux_time_series.yaml"),
                variables={
                    "OBS_SW_DN": "downwelling_shortwave_flux",
                    "OBS_SW_UP": "upwelling_shortwave_flux",
                    "OBS_LW_DN": "downwelling_longwave_flux",
                    "OBS_LW_UP": "upwelling_longwave_flux",
                    "MODEL_SW": "surface_downward_shortwave_flux",
                    "MODEL_LW": "surface_downward_longwave_flux",
                    "PLOT_VARNAME": "net_radiative_flux",
                    "OBS_HEIGHT": "2",
                },
            )
