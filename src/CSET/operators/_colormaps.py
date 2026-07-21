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

"""Functions to support colormap settings for CSET plots."""

import functools
import importlib.resources
import itertools
import json
import logging
from typing import Literal

import iris
import matplotlib as mpl
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np

from CSET._common import (
    combine_dicts,
    get_recipe_metadata,
    iter_maybe,
)

DEFAULT_DISCRETE_COLORS = mpl.colormaps["tab10"].colors + mpl.colormaps["Accent"].colors


@functools.cache
def load_colorbar_map(user_colorbar_file: str = None) -> dict:
    """Load the colorbar definitions from a file.

    This is a separate function to make it cacheable.
    """
    colorbar_file = importlib.resources.files().joinpath("_colorbar_definition.json")
    with open(colorbar_file, "rt", encoding="UTF-8") as fp:
        colorbar = json.load(fp)

    logging.debug("User colour bar file: %s", user_colorbar_file)
    override_colorbar = {}
    if user_colorbar_file:
        try:
            with open(user_colorbar_file, "rt", encoding="UTF-8") as fp:
                override_colorbar = json.load(fp)
        except FileNotFoundError:
            logging.warning("Colorbar file does not exist. Using default values.")

    # Overwrite values with the user supplied colorbar definition.
    colorbar = combine_dicts(colorbar, override_colorbar)
    return colorbar


def get_model_colors_map(cubes: iris.cube.CubeList | iris.cube.Cube) -> dict:
    """Get an appropriate colors for model lines in line plots.

    For each model in the list of cubes colors either from user provided
    color definition file (so-called style file) or from default colors are mapped
    to model_name attribute.

    Parameters
    ----------
    cubes: CubeList or Cube
        Cubes with model_name attribute

    Returns
    -------
    model_colors_map:
        Dictionary mapping model_name attribute to colors
    """
    user_colorbar_file = get_recipe_metadata().get("style_file_path", None)
    colorbar = load_colorbar_map(user_colorbar_file)
    model_names = sorted(
        filter(
            lambda x: x is not None,
            (cube.attributes.get("model_name", None) for cube in iter_maybe(cubes)),
        )
    )
    if not model_names:
        return {}
    use_user_colors = all(mname in colorbar.keys() for mname in model_names)
    if use_user_colors:
        return {mname: colorbar[mname] for mname in model_names}

    color_list = itertools.cycle(DEFAULT_DISCRETE_COLORS)
    return {mname: color for mname, color in zip(model_names, color_list, strict=False)}


def colorbar_map_levels(cube: iris.cube.Cube, axis: Literal["x", "y"] | None = None):
    """Get an appropriate colorbar for the given cube.

    For the given variable the appropriate colorbar is looked up from a
    combination of the built-in CSET colorbar definitions, and any user supplied
    definitions. As well as varying on variables, these definitions may also
    exist for specific pressure levels to account for variables with
    significantly different ranges at different heights. The colorbars also exist
    for masks and mask differences for considering variable presence diagnostics.
    Specific variable ranges can be separately set in user-supplied definition
    for x- or y-axis limits, or indicate where automated range preferred.

    Parameters
    ----------
    cube: Cube
        Cube of variable for which the colorbar information is desired.
    axis: "x", "y", optional
        Select the levels for just this axis of a line plot. The min and max
        can be set by xmin/xmax or ymin/ymax respectively. For variables where
        setting a universal range is not desirable (e.g. temperature), users
        can set ymin/ymax values to "auto" in the colorbar definitions file.
        Where no additional xmin/xmax or ymin/ymax values are provided, the
        axis bounds default to use the vmin/vmax values provided.

    Returns
    -------
    cmap:
        Matplotlib colormap.
    levels:
        List of levels to use for plotting. For continuous plots the min and max
        should be taken as the range.
    norm:
        BoundaryNorm information.
    """
    # Grab the colorbar file from the recipe global metadata.
    user_colorbar_file = get_recipe_metadata().get("style_file_path", None)
    colorbar = load_colorbar_map(user_colorbar_file)
    cmap = None

    try:
        # We assume that pressure is a scalar coordinate here.
        pressure_level_raw = cube.coord("pressure").points[0]
        # Ensure pressure_level is a string, as it is used as a JSON key.
        pressure_level = str(int(pressure_level_raw))
    except iris.exceptions.CoordinateNotFoundError:
        pressure_level = None

    # First try long name, then standard name, then var name. This order is used
    # as long name is the one we correct between models, so it most likely to be
    # consistent.
    varnames = list(filter(None, [cube.long_name, cube.standard_name, cube.var_name]))
    # Treat observation-labelled var names consistently with model var names.
    varnames = [varname.replace("observed_", "") for varname in varnames]
    for varname in varnames:
        # Get the colormap for this variable.
        try:
            var_colorbar = colorbar[varname]
            cmap = plt.get_cmap(colorbar[varname]["cmap"], 51)
            varname_key = varname
            break
        except KeyError:
            logging.debug("Cube name %s has no colorbar definition.", varname)

    # Get colormap if it is a mask.
    if any("mask_for_" in name for name in varnames):
        cmap, levels, norm = custom_colormap_mask(cube, axis=axis)
        return cmap, levels, norm
    # If winds on Beaufort Scale use custom colorbar and levels
    if any("Beaufort_Scale" in name for name in varnames):
        cmap, levels, norm = custom_beaufort_scale(cube, axis=axis)
        return cmap, levels, norm
    # If probability is plotted use custom colorbar and levels
    if any("probability_of_" in name for name in varnames):
        cmap, levels, norm = custom_colormap_probability(cube, axis=axis)
        return cmap, levels, norm
    # If aviation colour state use custom colorbar and levels
    if any("aviation_colour_state" in name for name in varnames):
        cmap, levels, norm = custom_colormap_aviation_colour_state(cube)
        return cmap, levels, norm
    # If verification scores use custom colorbar
    if any("RMSE_" in name for name in varnames):
        cmap, levels, norm = custom_colormap_scores(cube)
        return cmap, levels, norm

    # If no valid colormap has been defined, use defaults and return.
    if not cmap:
        logging.warning("No colorbar definition exists for %s.", cube.name())
        cmap, levels, norm = mpl.colormaps["viridis"], None, None
        return cmap, levels, norm

    # Test if pressure-level specific settings are provided for cube.
    if pressure_level:
        try:
            var_colorbar = colorbar[varname_key]["pressure_levels"][pressure_level]
        except KeyError:
            logging.debug(
                "%s has no colorbar definition for pressure level %s.",
                varname,
                pressure_level,
            )

    # Check for availability of x-axis or y-axis user-specific overrides
    # for setting level bounds for line plot types and return just levels.
    # Line plots do not need a colormap, and just use the data range.
    if axis:
        if axis == "x":
            try:
                vmin, vmax = var_colorbar["xmin"], var_colorbar["xmax"]
            except KeyError:
                vmin, vmax = var_colorbar["min"], var_colorbar["max"]
        if axis == "y":
            try:
                vmin, vmax = var_colorbar["ymin"], var_colorbar["ymax"]
            except KeyError:
                vmin, vmax = var_colorbar["min"], var_colorbar["max"]
        # Check if user-specified auto-scaling for this variable
        if vmin == "auto" or vmax == "auto":
            levels = None
        else:
            levels = [vmin, vmax]
        return None, levels, None
    # Get and use the colorbar levels for this variable if spatial or histogram.
    else:
        try:
            levels = var_colorbar["levels"]
            # Use discrete bins when levels are specified, rather
            # than a smooth range.
            norm = mpl.colors.BoundaryNorm(levels, ncolors=cmap.N)
            logging.debug("Using levels for %s colorbar.", varname)
            logging.info("Using levels: %s", levels)
        except KeyError:
            # Get the range for this variable.
            vmin, vmax = var_colorbar["min"], var_colorbar["max"]
            logging.debug("Using min and max for %s colorbar.", varname)
            # Calculate levels from range.
            if vmin == "auto" or vmax == "auto":
                levels = None
            else:
                levels = np.linspace(vmin, vmax, 101)
            norm = None

        # Overwrite cmap, levels and norm for specific variables that
        # require custom colorbar_map as these can not be defined in the
        # JSON file.
        cmap, levels, norm = custom_colormap_precipitation(cube, cmap, levels, norm)
        cmap, levels, norm = custom_colourmap_nimrod_weights(cube, cmap, levels, norm)
        cmap, levels, norm = custom_colormap_visibility_in_air(cube, cmap, levels, norm)
        cmap, levels, norm = custom_colormap_celsius(cube, cmap, levels, norm)
        cmap, levels, norm = custom_colormap_feature_tracking(cube, cmap, levels, norm)
        return cmap, levels, norm


def custom_colormap_mask(cube: iris.cube.Cube, axis: Literal["x", "y"] | None = None):
    """Get colormap for mask.

    If "mask_for_" appears anywhere in the name of a cube this function will be called
    regardless of the name of the variable to ensure a consistent plot.

    Parameters
    ----------
    cube: Cube
        Cube of variable for which the colorbar information is desired.
    axis: "x", "y", optional
        Select the levels for just this axis of a line plot. The min and max
        can be set by xmin/xmax or ymin/ymax respectively. For variables where
        setting a universal range is not desirable (e.g. temperature), users
        can set ymin/ymax values to "auto" in the colorbar definitions file.
        Where no additional xmin/xmax or ymin/ymax values are provided, the
        axis bounds default to use the vmin/vmax values provided.

    Returns
    -------
    cmap:
        Matplotlib colormap.
    levels:
        List of levels to use for plotting. For continuous plots the min and max
        should be taken as the range.
    norm:
        BoundaryNorm information.
    """
    if "difference" not in cube.long_name:
        if axis:
            levels = [0, 1]
            # Complete settings based on levels.
            return None, levels, None
        else:
            # Define the levels and colors.
            levels = [0, 1, 2]
            colors = ["white", "dodgerblue"]
            # Create a custom color map.
            cmap = mcolors.ListedColormap(colors)
            # Normalize the levels.
            norm = mcolors.BoundaryNorm(levels, cmap.N)
            logging.debug("Colormap for %s.", cube.long_name)
            return cmap, levels, norm
    else:
        if axis:
            levels = [-1, 1]
            return None, levels, None
        else:
            # Search for if mask difference, set to +/- 0.5 as values plotted <
            # not <=.
            levels = [-2, -0.5, 0.5, 2]
            colors = ["goldenrod", "white", "teal"]
            cmap = mcolors.ListedColormap(colors)
            norm = mcolors.BoundaryNorm(levels, cmap.N)
            logging.debug("Colormap for %s.", cube.long_name)
            return cmap, levels, norm


def custom_beaufort_scale(cube: iris.cube.Cube, axis: Literal["x", "y"] | None = None):
    """Get a custom colorbar for a cube in the Beaufort Scale.

    Specific variable ranges can be separately set in user-supplied definition
    for x- or y-axis limits, or indicate where automated range preferred.

    Parameters
    ----------
    cube: Cube
        Cube of variable with Beaufort Scale in name.
    axis: "x", "y", optional
        Select the levels for just this axis of a line plot. The min and max
        can be set by xmin/xmax or ymin/ymax respectively. For variables where
        setting a universal range is not desirable (e.g. temperature), users
        can set ymin/ymax values to "auto" in the colorbar definitions file.
        Where no additional xmin/xmax or ymin/ymax values are provided, the
        axis bounds default to use the vmin/vmax values provided.

    Returns
    -------
    cmap:
        Matplotlib colormap.
    levels:
        List of levels to use for plotting. For continuous plots the min and max
        should be taken as the range.
    norm:
        BoundaryNorm information.
    """
    if "difference" not in cube.long_name:
        if axis:
            levels = [0, 12]
            return None, levels, None
        else:
            levels = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
            colors = [
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
            cmap = mcolors.ListedColormap(colors)
            norm = mcolors.BoundaryNorm(levels, cmap.N)
            logging.info("change colormap for Beaufort Scale colorbar.")
            return cmap, levels, norm
    else:
        if axis:
            levels = [-4, 4]
            return None, levels, None
        else:
            levels = [
                -3.5,
                -2.5,
                -1.5,
                -0.5,
                0.5,
                1.5,
                2.5,
                3.5,
            ]
            cmap = plt.get_cmap("bwr", 8)
            norm = mcolors.BoundaryNorm(levels, cmap.N)
            return cmap, levels, norm


def custom_colormap_celsius(cube: iris.cube.Cube, cmap, levels, norm):
    """Return altered colormap for temperature with change in units to Celsius.

    If "Celsius" appears anywhere in the name of a cube this function will be called.

    Parameters
    ----------
    cube: Cube
        Cube of variable for which the colorbar information is desired.
    cmap: Matplotlib colormap.
    levels: List
        List of levels to use for plotting. For continuous plots the min and max
        should be taken as the range.
    norm: BoundaryNorm.

    Returns
    -------
    cmap: Matplotlib colormap.
    levels: List
        List of levels to use for plotting. For continuous plots the min and max
        should be taken as the range.
    norm: BoundaryNorm.
    """
    varnames = filter(None, [cube.long_name, cube.standard_name, cube.var_name])
    if any("temperature" in name for name in varnames) and "Celsius" == cube.units:
        levels = np.array(levels)
        levels -= 273
        levels = levels.tolist()
    else:
        # Do nothing keep the existing colourbar attributes
        levels = levels
    cmap = cmap
    norm = norm
    return cmap, levels, norm


def custom_colormap_probability(
    cube: iris.cube.Cube, axis: Literal["x", "y"] | None = None
):
    """Get a custom colorbar for a probability cube.

    Specific variable ranges can be separately set in user-supplied definition
    for x- or y-axis limits, or indicate where automated range preferred.

    Parameters
    ----------
    cube: Cube
        Cube of variable with probability in name.
    axis: "x", "y", optional
        Select the levels for just this axis of a line plot. The min and max
        can be set by xmin/xmax or ymin/ymax respectively. For variables where
        setting a universal range is not desirable (e.g. temperature), users
        can set ymin/ymax values to "auto" in the colorbar definitions file.
        Where no additional xmin/xmax or ymin/ymax values are provided, the
        axis bounds default to use the vmin/vmax values provided.

    Returns
    -------
    cmap:
        Matplotlib colormap.
    levels:
        List of levels to use for plotting. For continuous plots the min and max
        should be taken as the range.
    norm:
        BoundaryNorm information.
    """
    if axis:
        levels = [0, 1]
        return None, levels, None
    else:
        cmap = mcolors.ListedColormap(
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
        levels = [0.0, 0.01, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        norm = mcolors.BoundaryNorm(levels, cmap.N)
        return cmap, levels, norm


def custom_colormap_precipitation(cube: iris.cube.Cube, cmap, levels, norm):
    """Return a custom colormap for the current recipe."""
    varnames_lower = [
        n.lower() for n in (cube.long_name, cube.standard_name, cube.var_name) if n
    ]

    is_rainfall_var = any(
        key in name
        for name in varnames_lower
        for key in (
            "surface_microphysical",
            "rainfall rate composite",
            "nimrod5min",
            "nimrod_5min",
            "rain_accumulation",
            "rain accumulation",
        )
    )

    if is_rainfall_var:
        logging.debug(
            "Using custom precipitation colourmap due to varnames: %s", varnames_lower
        )
        levels = [0, 0.125, 0.25, 0.5, 1, 2, 4, 8, 16, 32, 64, 128, 256]
        colors = [
            "w",
            (0, 0, 0.6),
            "b",
            "c",
            "g",
            "y",
            (1, 0.5, 0),
            "r",
            "pink",
            "m",
            "purple",
            "maroon",
            "gray",
        ]
        # Create a custom colormap
        cmap = mcolors.ListedColormap(colors)
        # Normalize the levels
        norm = mcolors.BoundaryNorm(levels, cmap.N)
        logging.info("Using custom rainfall colourmap.")
    return cmap, levels, norm


def custom_colourmap_nimrod_weights(cube: iris.cube.Cube, cmap, levels, norm):
    """Return a custom colourmap for the current recipe."""
    varnames = filter(None, [cube.long_name, cube.standard_name, cube.var_name])
    if (
        any("wts" in name for name in varnames)
        and "difference" not in cube.long_name
        and "mask" not in cube.long_name
    ):
        # Define the levels and colors. Remember the Nimrod weights vary over
        # the range [0,13] and should be integer values. Optimum value is 13.
        levels = [
            -0.5,
            0.5,
            1.5,
            2.5,
            3.5,
            4.5,
            5.5,
            6.5,
            7.5,
            8.5,
            9.5,
            10.5,
            11.5,
            12.5,
            13.5,
        ]
        norm = mcolors.BoundaryNorm(levels, cmap.N)
        colours = [
            "#d10000",
            "purple",
            "#8f00d6",
            "#ff9700",
            "pink",
            "#ffff00",
            "#00007f",
            "#6c9ccd",
            "#aae8ff",
            "#37a648",
            "#8edc64",
            "#c5ffc5",
            "#dcdcdc",
            "#ffffff",
        ]
        # Create a custom colormap.
        cmap = mcolors.ListedColormap(colours)
        # Normalize the levels.
        norm = mcolors.BoundaryNorm(levels, cmap.N)
        logging.info("Change colormap for Nimrod weights colorbar.")
    else:
        # Do nothing and keep existing colorbar attributes.
        cmap = cmap
        levels = levels
        norm = norm
    return cmap, levels, norm


def custom_colormap_aviation_colour_state(cube: iris.cube.Cube):
    """Return custom colormap for aviation colour state.

    If "aviation_colour_state" appears anywhere in the name of a cube
    this function will be called.

    Parameters
    ----------
    cube: Cube
        Cube of variable for which the colorbar information is desired.

    Returns
    -------
    cmap: Matplotlib colormap.
    levels: List
        List of levels to use for plotting. For continuous plots the min and max
        should be taken as the range.
    norm: BoundaryNorm.
    """
    levels = [-0.5, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5]
    colors = [
        "#87ceeb",
        "#ffffff",
        "#8ced69",
        "#ffff00",
        "#ffd700",
        "#ffa500",
        "#fe3620",
    ]
    # Create a custom colormap
    cmap = mcolors.ListedColormap(colors)
    # Normalise the levels
    norm = mcolors.BoundaryNorm(levels, cmap.N)
    return cmap, levels, norm


def custom_colormap_visibility_in_air(cube: iris.cube.Cube, cmap, levels, norm):
    """Return a custom colormap for the current recipe."""
    varnames = filter(None, [cube.long_name, cube.standard_name, cube.var_name])
    if (
        any("visibility_in_air" in name for name in varnames)
        and "difference" not in cube.long_name
        and "mask" not in cube.long_name
    ):
        # Define the levels and colors (in km)
        levels = [0, 0.05, 0.1, 0.2, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0, 50.0, 70.0, 100.0]
        norm = mcolors.BoundaryNorm(levels, cmap.N)
        colours = [
            "#8f00d6",
            "#d10000",
            "#ff9700",
            "#ffff00",
            "#00007f",
            "#6c9ccd",
            "#aae8ff",
            "#37a648",
            "#8edc64",
            "#c5ffc5",
            "#dcdcdc",
            "#ffffff",
        ]
        # Create a custom colormap
        cmap = mcolors.ListedColormap(colours)
        # Normalize the levels
        norm = mcolors.BoundaryNorm(levels, cmap.N)
        logging.info("change colormap for visibility_in_air variable colorbar.")
    else:
        # do nothing and keep existing colorbar attributes
        cmap = cmap
        levels = levels
        norm = norm
    return cmap, levels, norm


def custom_colormap_scores(cube: iris.cube.Cube):
    """Return altered colormap for statistical metrics.

    Parameters
    ----------
    cube: Cube
        Cube of variable for which the colorbar information is desired.

    Returns
    -------
    cmap: Matplotlib colormap.
    levels: List
        List of levels to use for plotting. For continuous plots the min and max
        should be taken as the range.
    norm: BoundaryNorm.
    """
    varnames = filter(None, [cube.long_name, cube.standard_name, cube.var_name])
    cmap, levels, norm = None, None, None
    if any("RMSE_" in name for name in varnames):
        cmap = plt.get_cmap("PuRd", 51)
    return cmap, levels, norm


def custom_colormap_feature_tracking(cube: iris.cube.Cube, cmap, levels, norm):
    """Return altered colormap for feature tracking.

    Parameters
    ----------
    cube: Cube
        Cube of variable for which the colorbar information is desired.

    Returns
    -------
    cmap: Matplotlib colormap.
    levels: List
        List of levels to use for plotting. For continuous plots the min and max
        should be taken as the range.
    norm: BoundaryNorm.
    """
    varnames = list(filter(None, [cube.long_name, cube.standard_name, cube.var_name]))
    if (
        any("feature_id" in name for name in varnames)
        and "difference" not in cube.long_name
        and "mask" not in cube.long_name
    ):
        # Define the levels and colors
        levels = np.linspace(1, np.ma.max(cube.data), 10)
        cmap = plt.get_cmap("viridis")
        # Normalize the levels
        norm = mcolors.BoundaryNorm(levels, cmap.N)
        logging.info("change colormap for feature id variable colorbar.")
    elif (
        any("feature_lifetime" in name for name in varnames)
        and "difference" not in cube.long_name
        and "mask" not in cube.long_name
    ):
        # Define the levels and colors
        levels = np.linspace(1, np.ma.max(cube.data), 10)
        cmap = plt.get_cmap("YlGnBu")
        # Normalize the levels
        norm = mcolors.BoundaryNorm(levels, cmap.N)
        logging.info("change colormap for feature lifetime variable colorbar.")
    elif (
        any("feature_init" in name for name in varnames)
        and "difference" not in cube.long_name
        and "mask" not in cube.long_name
    ):
        # Define the levels and colors
        levels = np.array([0.5, 1])
        cmap = plt.get_cmap("Blues")
        # Normalize the levels
        norm = mcolors.BoundaryNorm(levels, cmap.N)
        logging.info("change colormap for feature init variable colorbar.")

    else:
        # do nothing and keep existing colorbar attributes
        cmap = cmap
        levels = levels
        norm = norm

    # Set all non-feature data to white
    if any("feature" in name for name in varnames):
        cmap.with_extremes(under="white")

    return cmap, levels, norm
