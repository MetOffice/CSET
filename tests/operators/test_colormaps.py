# © Crown copyright, Met Office (2022-2026) and CSET contributors.
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

"""Test colormap functions used by plot operators."""

import json
import logging

import iris.coords
import iris.cube
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

from CSET.operators import _colormaps, misc


def test_load_colorbar_map():
    """Colorbar is loaded correctly."""
    colorbar = _colormaps.load_colorbar_map()
    assert isinstance(colorbar, dict)
    # Check we can find an example definition.
    assert colorbar["temperature_at_screen_level"] == {
        "cmap": "RdYlBu_r",
        "max": 323,
        "min": 263,
        "ymax": "auto",
        "ymin": "auto",
    }


def test_load_colorbar_map_override(tmp_path):
    """Colorbar is loaded correctly and overridden by the user definition."""
    # Setup a user provided colorbar override.
    user_definition = {"temperature_at_screen_level": {"max": 1000, "min": 0}}
    user_colorbar_file = tmp_path / "colorbar.json"
    with open(user_colorbar_file, "wt") as fp:
        json.dump(user_definition, fp)

    colorbar = _colormaps.load_colorbar_map(user_colorbar_file)

    assert isinstance(colorbar, dict)
    # Check definition is updated.
    assert colorbar["temperature_at_screen_level"] == {
        "cmap": "RdYlBu_r",
        "max": 1000,
        "min": 0,
        "ymax": "auto",
        "ymin": "auto",
    }
    # Check we can still see unchanged definitions.
    assert colorbar["temperature_at_screen_level_difference"] == {
        "cmap": "bwr",
        "max": 10,
        "min": -10,
    }


def test_load_colorbar_map_override_file_not_found(tmp_path):
    """Colorbar overridden by the user definition in non-existent file."""
    user_colorbar_file = tmp_path / "colorbar.json"
    colorbar = _colormaps.load_colorbar_map(user_colorbar_file)
    # Check it still returns the built-in one.
    assert isinstance(colorbar, dict)


def test_get_model_colors_map(cube):
    """Generate model_colors_map if model name provided."""
    cube.attributes["model_name"] = "model_1"
    model_colors_map = _colormaps.get_model_colors_map(cube)
    assert model_colors_map == {
        "model_1": (0.12156862745098039, 0.4666666666666667, 0.7058823529411765)
    }


def test_get_model_colors_map_noname(cube):
    """Empty model_colors_map if no model name provided."""
    model_colors_map = _colormaps.get_model_colors_map(cube)
    assert model_colors_map == {}


def test_colorbar_map_levels(cube, tmp_working_dir):
    """Colorbar definition is found for cube."""
    cmap, levels, norm = _colormaps.colorbar_map_levels(cube)
    assert cmap == mpl.pyplot.get_cmap("RdYlBu_r", 51)
    assert (levels == np.linspace(263, 323, 101)).all()
    assert norm is None


def test_colorbar_map_levels_xaxis(cube, tmp_working_dir):
    """Set levels for based on xmin, xmax."""
    cube = iris.cube.Cube(np.arange(10), long_name="zonal_wind_at_pressure_levels")
    cmap, levels, norm = _colormaps.colorbar_map_levels(cube, axis="x")
    assert cmap is None
    assert levels == [-25, 25]
    assert norm is None


def test_colorbar_map_levels_xaxis_default(cube, tmp_working_dir):
    """Test for variable without xmin, xmax."""
    cube = iris.cube.Cube(
        np.arange(10), long_name="zonal_wind_at_pressure_levels_difference"
    )
    cmap, levels, norm = _colormaps.colorbar_map_levels(cube, axis="x")
    assert cmap is None
    assert levels == [-20, 20]
    assert norm is None


def test_colorbar_map_levels_yaxis(cube, tmp_working_dir):
    """Set levels for based on ymin, ymax."""
    cube = iris.cube.Cube(np.arange(10), long_name="toa_upward_shortwave_flux")
    cmap, levels, norm = _colormaps.colorbar_map_levels(cube, axis="y")
    assert cmap is None
    assert levels == [0, 500]
    assert norm is None


def test_colorbar_map_levels_yaxis_default(cube, tmp_working_dir):
    """Test for variable without ymin, ymax."""
    cube = iris.cube.Cube(
        np.arange(10), long_name="toa_upward_shortwave_flux_difference"
    )
    cmap, levels, norm = _colormaps.colorbar_map_levels(cube, axis="y")
    assert cmap is None
    assert levels == [-100, 100]
    assert norm is None


def test_colorbar_map_levels_yaxis_auto(cube, tmp_working_dir):
    """Set levels for based on ymin, ymax set to auto."""
    cmap, levels, norm = _colormaps.colorbar_map_levels(cube, axis="y")
    assert cmap is None
    assert levels is None
    assert norm is None


def test_colorbar_map_levels_def_on_levels(cube, tmp_working_dir):
    """Colorbar definition that uses levels is found for cube."""
    cube = iris.cube.Cube(
        np.arange(10), long_name="surface_microphysical_rainfall_rate"
    )
    cmap, levels, norm = _colormaps.colorbar_map_levels(cube)
    assert levels == [0, 0.125, 0.25, 0.5, 1, 2, 4, 8, 16, 32, 64, 128, 256]


def test_colorbar_map_levels_def_on_levels_test_visibility_in_air(
    cube, tmp_working_dir
):
    """Colorbar definition that uses levels is found for cube."""
    cube = iris.cube.Cube(np.arange(10), long_name="visibility_in_air")
    cmap, levels, norm = _colormaps.colorbar_map_levels(cube)
    assert levels == [
        0,
        0.05,
        0.1,
        0.2,
        1.0,
        2.0,
        5.0,
        10.0,
        20.0,
        30.0,
        50.0,
        70.0,
        100.0,
    ]


def test_colorbar_map_levels_name_fallback(cube, tmp_working_dir):
    """Colorbar definition is found for cube after checking its other names."""
    cube.standard_name = None
    cmap, levels, norm = _colormaps.colorbar_map_levels(cube)
    assert cmap == mpl.pyplot.get_cmap("RdYlBu_r", 51)
    assert (levels == np.linspace(263, 323, 101)).all()
    assert norm is None


def test_colorbar_map_levels_unknown_variable_fallback(cube, tmp_working_dir):
    """Colorbar definition doesn't exist for cube."""
    cube.standard_name = None
    cube.long_name = None
    cube.var_name = "unknown"
    cmap, levels, norm = _colormaps.colorbar_map_levels(cube)
    assert cmap == mpl.pyplot.get_cmap("viridis")
    assert levels is None
    assert norm is None


def test_colorbar_map_levels_name_observed(cube, tmp_working_dir):
    """Colorbar definition is found for cube with 'observed_' preceding known names."""
    cube.var_name = "observed_temperature_at_screen_level"
    cmap, levels, norm = _colormaps.colorbar_map_levels(cube)
    assert cmap == mpl.pyplot.get_cmap("RdYlBu_r", 51)
    assert (levels == np.linspace(263, 323, 101)).all()
    assert norm is None


def test_colorbar_map_levels_pressure_level(transect_source_cube, tmp_working_dir):
    """Pressure level specific colorbar definition is picked up."""
    cube_250hPa = transect_source_cube.extract(iris.Constraint(pressure=250))
    cmap, levels, norm = _colormaps.colorbar_map_levels(cube_250hPa)
    assert cmap == mpl.pyplot.get_cmap("RdYlBu_r", 51)
    assert (levels == np.linspace(200, 240, 101)).all()
    assert norm is None


def test_colorbar_map_levels_pressure_level_yaxis(
    transect_source_cube, tmp_working_dir
):
    """Pressure level specific colorbar definition is picked up."""
    cube_250hPa = transect_source_cube.extract(iris.Constraint(pressure=250))
    cube_250hPa.rename("zonal_wind_at_pressure_levels")
    cmap, levels, norm = _colormaps.colorbar_map_levels(cube_250hPa, axis="y")
    assert cmap is None
    assert levels == [-20, 20]
    assert norm is None


def test_colorbar_map_levels_missing_pressure_level(
    transect_source_cube, tmp_working_dir, caplog
):
    """Pressure level specific colorbar definition is not defined."""
    cube_288hPa = transect_source_cube.extract(iris.Constraint(pressure=250))
    cube_288hPa.coord("pressure").points = 288.0
    cmap, levels, norm = _colormaps.colorbar_map_levels(cube_288hPa)
    with caplog.at_level(logging.DEBUG):
        cmap, levels, norm = _colormaps.colorbar_map_levels(cube_288hPa)
        assert caplog.record_tuples == [
            (
                "root",
                logging.DEBUG,
                "temperature_at_pressure_levels has no colorbar definition for pressure level 288.",
            ),
            (
                "root",
                logging.DEBUG,
                "Using min and max for temperature_at_pressure_levels colorbar.",
            ),
        ]


def test_colorbar_map_mask(cube, tmp_working_dir):
    """Test to ensure axis picks up correct colormap for a mask."""
    cube.rename(f"mask_for_{cube.name()}")
    cmap, levels, norm = _colormaps.colorbar_map_levels(cube)
    assert cmap == mpl.colors.ListedColormap(["w", "dodgerblue"])
    assert levels == [0, 1, 2]
    assert isinstance(norm, mpl.colors.BoundaryNorm)
    assert (norm.boundaries == levels).all()


def test_colorbar_map_beaufort_scale(cube, tmp_working_dir):
    """Test to ensure picks up correct colormap for a cube in Beaufort Scale."""
    cube.rename("wind_speed_at_10m_on_Beaufort_Scale")
    cmap, levels, norm = _colormaps.colorbar_map_levels(cube)
    assert cmap == mpl.colors.ListedColormap(
        [
            "black",
            (0, 0, 0.6),
            "blue",
            "cyan",
            "green",
            "yellow",
            (1, 0.5, 0),
            "red",
            "pink",
            "magenta",
            "purple",
            "maroon",
            "white",
        ]
    )
    assert levels == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
    assert isinstance(norm, mpl.colors.BoundaryNorm)
    assert (norm.boundaries == levels).all()


def test_colorbar_map_mask_difference(cube, tmp_working_dir):
    """Test to ensure axis picks up correct colormap for a mask difference."""
    cube.rename(f"mask_for_{cube.name()}_difference")
    cmap, levels, norm = _colormaps.colorbar_map_levels(cube)
    assert cmap == mpl.colors.ListedColormap(["goldenrod", "w", "teal"])
    assert levels == [-2, -0.5, 0.5, 2]
    assert isinstance(norm, mpl.colors.BoundaryNorm)
    assert (norm.boundaries == levels).all()


def test_colorbar_map_beaufort_scale_difference(cube, tmp_working_dir):
    """Test to ensure picks up correct colormap for Beaufort Scale difference."""
    cube.rename("wind_speed_at_10m_on_Beaufort_Scale_difference")
    cmap, levels, norm = _colormaps.colorbar_map_levels(cube)
    assert cmap == plt.get_cmap("bwr", 8)
    assert levels == [
        -3.5,
        -2.5,
        -1.5,
        -0.5,
        0.5,
        1.5,
        2.5,
        3.5,
    ]
    assert isinstance(norm, mpl.colors.BoundaryNorm)
    assert (norm.boundaries == levels).all()


def test_colorbar_map_axis_mask(cube, tmp_working_dir):
    """Test to ensure axis picks up correct levels when mask defined."""
    cube.rename(f"mask_for_{cube.name()}")
    cmap, levels, norm = _colormaps.colorbar_map_levels(cube, axis="y")
    assert cmap is None
    assert levels == [0, 1]
    assert norm is None


def test_colorbar_map_axis_mask_difference(cube, tmp_working_dir):
    """Test to ensure axis picks up correct levels when mask difference defined."""
    cube.rename(f"mask_for_{cube.name()}_difference")
    cmap, levels, norm = _colormaps.colorbar_map_levels(cube, axis="x")
    assert cmap is None
    assert levels == [-1, 1]
    assert norm is None


def test_colorbar_map_beaufort_scale_axis(cube, tmp_working_dir):
    """Test to ensure axis picks up correct levels for a cube in Beaufort Scale."""
    cube.rename("wind_speed_at_10m_on_Beaufort_Scale")
    cmap, levels, norm = _colormaps.colorbar_map_levels(cube, axis="y")
    assert cmap is None
    assert levels == [0, 12]
    assert norm is None


def test_colorbar_map_beaufort_scale_axis_difference(cube, tmp_working_dir):
    """Test to ensure axis picks up correct levels for a cube in Beaufort Scale difference."""
    cube.rename("wind_speed_at_10m_on_Beaufort_Scale_difference")
    cmap, levels, norm = _colormaps.colorbar_map_levels(cube, axis="x")
    assert cmap is None
    assert levels == [-4, 4]
    assert norm is None


def test_colorbar_map_celsius(cube, tmp_working_dir):
    """Test to ensure color bar is changed for temperature in Celsius."""
    cube = misc.convert_units(cube, "Celsius")
    cmap = mpl.cm.RdYlBu
    norm = None
    levels = [273, 373]
    cmap, levels, norm = _colormaps.custom_colormap_celsius(
        cube, cmap=cmap, levels=levels, norm=norm
    )
    assert cmap == mpl.cm.RdYlBu
    assert norm is None
    assert levels == [0, 100]


def test_colorbar_map_probabilities_axis(cube, tmp_working_dir):
    """Test to ensure axis picks up correct levels for a cube of probabilities."""
    cube.rename("probability_of_temperature_>_276")
    cmap, levels, norm = _colormaps.colorbar_map_levels(cube, axis="x")
    assert cmap is None
    assert levels == [0, 1]
    assert norm is None


def test_colorbar_map_probabilities(cube, tmp_working_dir):
    """Test to ensure colorbar picks up correct maap for cube of probabilities."""
    cube.rename("probability_of_temperature_>_276")
    cmap, levels, norm = _colormaps.colorbar_map_levels(cube)
    assert cmap == mpl.colors.ListedColormap(
        [
            "#FFFFFF",
            "#636363",
            "#e1dada",
            "#B5CAFF",
            "#8FB3FF",
            "#7F97FF",
            "#ABCF63",
            "#E8F59E",
            "#FFFA14",
            "#FFD121",
            "#FFA30A",
        ]
    )
    assert levels == [0.0, 0.01, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    assert isinstance(norm, mpl.colors.BoundaryNorm)
    assert (norm.boundaries == levels).all()


def test_colorbar_map_aviation_colour_state(cube, tmp_working_dir):
    """Test to ensure color bar is change for aviation colour states."""
    cube.rename("aviation_colour_state")
    expected_levels = [-0.5, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5]
    expected_colors = [
        "#87ceeb",
        "#ffffff",
        "#8ced69",
        "#ffff00",
        "#ffd700",
        "#ffa500",
        "#fe3620",
    ]
    expected_cmap = mpl.colors.ListedColormap(expected_colors)
    cmap, levels, norm = _colormaps.colorbar_map_levels(cube)
    assert cmap == expected_cmap
    assert levels == expected_levels
    assert isinstance(norm, mpl.colors.BoundaryNorm)
    assert (norm.boundaries == levels).all()


def test_colorbar_map_scores_rmse(cube, tmp_working_dir):
    """Colorbar definition is found for a rmse cube calculated via scores."""
    cube.rename(f"RMSE_{cube.name()}")
    cmap, levels, norm = _colormaps.colorbar_map_levels(cube)
    assert cmap == plt.get_cmap("PuRd", 51)
    assert levels is None
    assert norm is None


def test_colorbar_map_auto(cube):
    """Set colorbar for variables with auto scaling set."""
    cube.rename("surface_altitude")
    cmap, levels, norm = _colormaps.colorbar_map_levels(cube)
    assert cmap == plt.get_cmap("terrain", 51)
    assert levels is None
    assert norm is None


def test_colorbar_feature_tracking_id_cube(cube):
    """Colorbar definition is found for a feature id cube."""
    cube.rename("feature_id")
    cmap, levels, norm = _colormaps.custom_colormap_feature_tracking(
        cube, None, None, None
    )
    expected_levels = np.linspace(1, np.ma.max(cube.data), 10)
    assert cmap == plt.get_cmap("viridis")
    assert cmap.get_under() is not None
    assert (levels == expected_levels).all()
    assert (norm.boundaries == levels).all()


def test_colorbar_feature_tracking_lifetime_cube(cube):
    """Colorbar definition is found for a feature lifetime cube."""
    cube.rename("feature_lifetime")
    cmap, levels, norm = _colormaps.custom_colormap_feature_tracking(
        cube, None, None, None
    )
    expected_levels = np.linspace(1, np.ma.max(cube.data), 10)
    assert cmap == plt.get_cmap("YlGnBu")
    assert cmap.get_under() is not None
    assert (levels == expected_levels).all()
    assert (norm.boundaries == levels).all()


def test_colorbar_feature_tracking_init_cube(cube):
    """Colorbar definition is found for a feature init cube."""
    cube.rename("feature_init")
    cmap, levels, norm = _colormaps.custom_colormap_feature_tracking(
        cube, None, None, None
    )
    expected_levels = np.array([0.5, 1])
    assert cmap == plt.get_cmap("Blues")
    assert cmap.get_under() is not None
    assert (levels == expected_levels).all()
    assert (norm.boundaries == levels).all()
