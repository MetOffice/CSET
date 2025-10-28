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

"""Operators to produce various kinds of plots."""

import fcntl
import functools
import importlib.resources
import itertools
import json
import logging
import math
import os
import sys
from typing import Literal

import cartopy.crs as ccrs
import iris
import iris.coords
import iris.cube
import iris.exceptions
import iris.plot as iplt
import matplotlib as mpl
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
from markdown_it import MarkdownIt

from CSET._common import (
    combine_dicts,
    get_recipe_metadata,
    iter_maybe,
    render_file,
    slugify,
)
from CSET.operators._utils import get_cube_yxcoordname, is_transect

# Use a non-interactive plotting backend.
mpl.use("agg")

DEFAULT_DISCRETE_COLORS = mpl.colormaps["tab10"].colors + mpl.colormaps["Accent"].colors

############################
# Private helper functions #
############################


def _append_to_plot_index(plot_index: list) -> list:
    """Add plots into the plot index, returning the complete plot index."""
    with open("meta.json", "r+t", encoding="UTF-8") as fp:
        fcntl.flock(fp, fcntl.LOCK_EX)
        fp.seek(0)
        meta = json.load(fp)
        complete_plot_index = meta.get("plots", [])
        complete_plot_index = complete_plot_index + plot_index
        meta["plots"] = complete_plot_index
        if os.getenv("CYLC_TASK_CYCLE_POINT") and not bool(
            os.getenv("DO_CASE_AGGREGATION")
        ):
            meta["case_date"] = os.getenv("CYLC_TASK_CYCLE_POINT", "")
        fp.seek(0)
        fp.truncate()
        json.dump(meta, fp, indent=2)
    return complete_plot_index


def _check_single_cube(cube: iris.cube.Cube | iris.cube.CubeList) -> iris.cube.Cube:
    """Ensure a single cube is given.

    If a CubeList of length one is given that the contained cube is returned,
    otherwise an error is raised.

    Parameters
    ----------
    cube: Cube | CubeList
        The cube to check.

    Returns
    -------
    cube: Cube
        The checked cube.

    Raises
    ------
    TypeError
        If the input cube is not a Cube or CubeList of a single Cube.
    """
    if isinstance(cube, iris.cube.Cube):
        return cube
    if isinstance(cube, iris.cube.CubeList):
        if len(cube) == 1:
            return cube[0]
    raise TypeError("Must have a single cube", cube)


def _py312_importlib_resources_files_shim():
    """Importlib behaviour changed in 3.12 to avoid circular dependencies.

    This shim is needed until python 3.12 is our oldest supported version, after
    which it can just be replaced by directly using importlib.resources.files.
    """
    if sys.version_info.minor >= 12:
        files = importlib.resources.files()
    else:
        import CSET.operators

        files = importlib.resources.files(CSET.operators)
    return files


def _make_plot_html_page(plots: list):
    """Create a HTML page to display a plot image."""
    # Debug check that plots actually contains some strings.
    assert isinstance(plots[0], str)

    # Load HTML template file.
    operator_files = _py312_importlib_resources_files_shim()
    template_file = operator_files.joinpath("_plot_page_template.html")

    # Get some metadata.
    meta = get_recipe_metadata()
    title = meta.get("title", "Untitled")
    description = MarkdownIt().render(meta.get("description", "*No description.*"))

    # Prepare template variables.
    variables = {
        "title": title,
        "description": description,
        "initial_plot": plots[0],
        "plots": plots,
        "title_slug": slugify(title),
    }

    # Render template.
    html = render_file(template_file, **variables)

    # Save completed HTML.
    with open("index.html", "wt", encoding="UTF-8") as fp:
        fp.write(html)


@functools.cache
def _load_colorbar_map(user_colorbar_file: str = None) -> dict:
    """Load the colorbar definitions from a file.

    This is a separate function to make it cacheable.
    """
    colorbar_file = _py312_importlib_resources_files_shim().joinpath(
        "_colorbar_definition.json"
    )
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


def _get_model_colors_map(cubes: iris.cube.CubeList | iris.cube.Cube) -> dict:
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
    colorbar = _load_colorbar_map(user_colorbar_file)
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


def _colorbar_map_levels(cube: iris.cube.Cube, axis: Literal["x", "y"] | None = None):
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
    colorbar = _load_colorbar_map(user_colorbar_file)
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
        cmap, levels, norm = _custom_colormap_mask(cube, axis=axis)
        return cmap, levels, norm
    # If winds on Beaufort Scale use custom colorbar and levels
    if any("Beaufort_Scale" in name for name in varnames):
        cmap, levels, norm = _custom_beaufort_scale(cube, axis=axis)
        return cmap, levels, norm
    # If probability is plotted use custom colorbar and levels
    if any("probability_of_" in name for name in varnames):
        cmap, levels, norm = _custom_colormap_probability(cube, axis=axis)
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
            levels = np.linspace(vmin, vmax, 101)
            norm = None

        # Overwrite cmap, levels and norm for specific variables that
        # require custom colorbar_map as these can not be defined in the
        # JSON file.
        cmap, levels, norm = _custom_colourmap_precipitation(cube, cmap, levels, norm)
        cmap, levels, norm = _custom_colourmap_visibility_in_air(
            cube, cmap, levels, norm
        )
        cmap, levels, norm = _custom_colormap_celsius(cube, cmap, levels, norm)
        return cmap, levels, norm


def _setup_spatial_map(
    cube: iris.cube.Cube,
    figure,
    cmap,
    grid_size: int | None = None,
    subplot: int | None = None,
):
    """Define map projections, extent and add coastlines for spatial plots.

    For spatial map plots, a relevant map projection for rotated or non-rotated inputs
    is specified, and map extent defined based on the input data.

    Parameters
    ----------
    cube: Cube
        2 dimensional (lat and lon) Cube of the data to plot.
    figure:
        Matplotlib Figure object holding all plot elements.
    cmap:
        Matplotlib colormap.
    grid_size: int, optional
        Size of grid for subplots if multiple spatial subplots in figure.
    subplot: int, optional
        Subplot index if multiple spatial subplots in figure.

    Returns
    -------
    axes:
        Matplotlib GeoAxes definition.
    """
    # Identify min/max plot bounds.
    try:
        lat_axis, lon_axis = get_cube_yxcoordname(cube)
        x1 = np.min(cube.coord(lon_axis).points)
        x2 = np.max(cube.coord(lon_axis).points)
        y1 = np.min(cube.coord(lat_axis).points)
        y2 = np.max(cube.coord(lat_axis).points)

        # Adjust bounds within +/- 180.0 if x dimension extends beyond half-globe.
        if np.abs(x2 - x1) > 180.0:
            x1 = x1 - 180.0
            x2 = x2 - 180.0
            logging.debug("Adjusting plot bounds to fit global extent.")

        # Consider map projection orientation.
        # Adapting orientation enables plotting across international dateline.
        # Users can adapt the default central_longitude if alternative projections views.
        if x2 > 180.0:
            central_longitude = 180.0
        else:
            central_longitude = 0.0

        # Define spatial map projection.
        coord_system = cube.coord(lat_axis).coord_system
        if isinstance(coord_system, iris.coord_systems.RotatedGeogCS):
            # Define rotated pole map projection for rotated pole inputs.
            projection = ccrs.RotatedPole(
                pole_longitude=coord_system.grid_north_pole_longitude,
                pole_latitude=coord_system.grid_north_pole_latitude,
                central_rotated_longitude=0.0,
            )
            crs = projection
        else:
            # Define regular map projection for non-rotated pole inputs.
            # Alternatives might include e.g. for global model outputs:
            #    projection=ccrs.Robinson(central_longitude=X.y, globe=None)
            # See also https://scitools.org.uk/cartopy/docs/v0.15/crs/projections.html.
            projection = ccrs.PlateCarree(central_longitude=central_longitude)
            crs = ccrs.PlateCarree()

        # Define axes for plot (or subplot) with required map projection.
        if subplot is not None:
            axes = figure.add_subplot(
                grid_size, grid_size, subplot, projection=projection
            )
        else:
            axes = figure.add_subplot(projection=projection)

        # Add coastlines if cube contains x and y map coordinates.
        if cmap.name in ["viridis", "Greys"]:
            coastcol = "magenta"
        else:
            coastcol = "black"
        logging.debug("Plotting coastlines in colour %s.", coastcol)
        axes.coastlines(resolution="10m", color=coastcol)

        # If is lat/lon spatial map, fix extent to keep plot tight.
        # Specifying crs within set_extent helps ensure only data region is shown.
        if isinstance(coord_system, iris.coord_systems.GeogCS):
            axes.set_extent([x1, x2, y1, y2], crs=crs)

    except ValueError:
        # Skip if not both x and y map coordinates.
        axes = figure.gca()
        pass

    return axes


def _get_plot_resolution() -> int:
    """Get resolution of rasterised plots in pixels per inch."""
    return get_recipe_metadata().get("plot_resolution", 100)


def _plot_and_save_spatial_plot(
    cube: iris.cube.Cube,
    filename: str,
    title: str,
    method: Literal["contourf", "pcolormesh"],
    **kwargs,
):
    """Plot and save a spatial plot.

    Parameters
    ----------
    cube: Cube
        2 dimensional (lat and lon) Cube of the data to plot.
    filename: str
        Filename of the plot to write.
    title: str
        Plot title.
    method: "contourf" | "pcolormesh"
        The plotting method to use.
    """
    # Setup plot details, size, resolution, etc.
    fig = plt.figure(figsize=(10, 10), facecolor="w", edgecolor="k")

    # Specify the color bar
    cmap, levels, norm = _colorbar_map_levels(cube)

    # Setup plot map projection, extent and coastlines.
    axes = _setup_spatial_map(cube, fig, cmap)

    # Plot the field.
    if method == "contourf":
        # Filled contour plot of the field.
        plot = iplt.contourf(cube, cmap=cmap, levels=levels, norm=norm)
    elif method == "pcolormesh":
        try:
            vmin = min(levels)
            vmax = max(levels)
        except TypeError:
            vmin, vmax = None, None
        # pcolormesh plot of the field and ensure to use norm and not vmin/vmax
        # if levels are defined.
        if norm is not None:
            vmin = None
            vmax = None
            logging.debug("Plotting using defined levels.")
        plot = iplt.pcolormesh(cube, cmap=cmap, norm=norm, vmin=vmin, vmax=vmax)
    else:
        raise ValueError(f"Unknown plotting method: {method}")

    # Check to see if transect, and if so, adjust y axis.
    if is_transect(cube):
        if "pressure" in [coord.name() for coord in cube.coords()]:
            axes.invert_yaxis()
            axes.set_yscale("log")
            axes.set_ylim(1100, 100)
        # If both model_level_number and level_height exists, iplt can construct
        # plot as a function of height above orography (NOT sea level).
        elif {"model_level_number", "level_height"}.issubset(
            {coord.name() for coord in cube.coords()}
        ):
            axes.set_yscale("log")

        axes.set_title(
            f"{title}\n"
            f"Start Lat: {cube.attributes['transect_coords'].split('_')[0]}"
            f" Start Lon: {cube.attributes['transect_coords'].split('_')[1]}"
            f" End Lat: {cube.attributes['transect_coords'].split('_')[2]}"
            f" End Lon: {cube.attributes['transect_coords'].split('_')[3]}",
            fontsize=16,
        )

    else:
        # Add title.
        axes.set_title(title, fontsize=16)

    # Add watermark with min/max/mean. Currently not user togglable.
    # In the bbox dictionary, fc and ec are hex colour codes for grey shade.
    axes.annotate(
        f"Min: {np.min(cube.data):.3g} Max: {np.max(cube.data):.3g} Mean: {np.mean(cube.data):.3g}",
        xy=(1, -0.05),
        xycoords="axes fraction",
        xytext=(-5, 5),
        textcoords="offset points",
        ha="right",
        va="bottom",
        size=11,
        bbox=dict(boxstyle="round", fc="#cccccc", ec="#808080", alpha=0.9),
    )

    # Add colour bar.
    cbar = fig.colorbar(plot, orientation="horizontal", pad=0.042, shrink=0.7)
    cbar.set_label(label=f"{cube.name()} ({cube.units})", size=14)
    # add ticks and tick_labels for every levels if less than 20 levels exist
    if levels is not None and len(levels) < 20:
        cbar.set_ticks(levels)
        cbar.set_ticklabels([f"{level:.2f}" for level in levels])
        if "visibility" in cube.name():
            cbar.set_ticklabels([f"{level:.3g}" for level in levels])
        logging.debug("Set colorbar ticks and labels.")

    # Save plot.
    fig.savefig(filename, bbox_inches="tight", dpi=_get_plot_resolution())
    logging.info("Saved spatial plot to %s", filename)
    plt.close(fig)


def _plot_and_save_postage_stamp_spatial_plot(
    cube: iris.cube.Cube,
    filename: str,
    stamp_coordinate: str,
    title: str,
    method: Literal["contourf", "pcolormesh"],
    **kwargs,
):
    """Plot postage stamp spatial plots from an ensemble.

    Parameters
    ----------
    cube: Cube
        Iris cube of data to be plotted. It must have the stamp coordinate.
    filename: str
        Filename of the plot to write.
    stamp_coordinate: str
        Coordinate that becomes different plots.
    method: "contourf" | "pcolormesh"
        The plotting method to use.

    Raises
    ------
    ValueError
        If the cube doesn't have the right dimensions.
    """
    # Use the smallest square grid that will fit the members.
    grid_size = int(math.ceil(math.sqrt(len(cube.coord(stamp_coordinate).points))))

    fig = plt.figure(figsize=(10, 10))

    # Specify the color bar
    cmap, levels, norm = _colorbar_map_levels(cube)

    # Make a subplot for each member.
    for member, subplot in zip(
        cube.slices_over(stamp_coordinate), range(1, grid_size**2 + 1), strict=False
    ):
        # Setup subplot map projection, extent and coastlines.
        axes = _setup_spatial_map(
            member, fig, cmap, grid_size=grid_size, subplot=subplot
        )
        if method == "contourf":
            # Filled contour plot of the field.
            plot = iplt.contourf(member, cmap=cmap, levels=levels, norm=norm)
        elif method == "pcolormesh":
            if levels is not None:
                vmin = min(levels)
                vmax = max(levels)
            else:
                raise TypeError("Unknown vmin and vmax range.")
                vmin, vmax = None, None
            # pcolormesh plot of the field and ensure to use norm and not vmin/vmax
            # if levels are defined.
            if norm is not None:
                vmin = None
                vmax = None
            # pcolormesh plot of the field.
            plot = iplt.pcolormesh(member, cmap=cmap, norm=norm, vmin=vmin, vmax=vmax)
        else:
            raise ValueError(f"Unknown plotting method: {method}")
        axes.set_title(f"Member #{member.coord(stamp_coordinate).points[0]}")
        axes.set_axis_off()

    # Put the shared colorbar in its own axes.
    colorbar_axes = fig.add_axes([0.15, 0.07, 0.7, 0.03])
    colorbar = fig.colorbar(
        plot, colorbar_axes, orientation="horizontal", pad=0.042, shrink=0.7
    )
    colorbar.set_label(f"{cube.name()} ({cube.units})", size=14)

    # Overall figure title.
    fig.suptitle(title, fontsize=16)

    fig.savefig(filename, bbox_inches="tight", dpi=_get_plot_resolution())
    logging.info("Saved contour postage stamp plot to %s", filename)
    plt.close(fig)


def _plot_and_save_line_series(
    cubes: iris.cube.CubeList,
    coords: list[iris.coords.Coord],
    ensemble_coord: str,
    filename: str,
    title: str,
    **kwargs,
):
    """Plot and save a 1D line series.

    Parameters
    ----------
    cubes: Cube or CubeList
        Cube or CubeList containing the cubes to plot on the y-axis.
    coords: list[Coord]
        Coordinates to plot on the x-axis, one per cube.
    ensemble_coord: str
        Ensemble coordinate in the cube.
    filename: str
        Filename of the plot to write.
    title: str
        Plot title.
    """
    fig = plt.figure(figsize=(10, 10), facecolor="w", edgecolor="k")

    model_colors_map = _get_model_colors_map(cubes)

    # Store min/max ranges.
    y_levels = []

    # Check match-up across sequence coords gives consistent sizes
    _validate_cubes_coords(cubes, coords)

    for cube, coord in zip(cubes, coords, strict=True):
        label = None
        color = "black"
        if model_colors_map:
            label = cube.attributes.get("model_name")
            color = model_colors_map.get(label)
        for cube_slice in cube.slices_over(ensemble_coord):
            # Label with (control) if part of an ensemble or not otherwise.
            if cube_slice.coord(ensemble_coord).points == [0]:
                iplt.plot(
                    coord,
                    cube_slice,
                    color=color,
                    marker="o",
                    ls="-",
                    lw=3,
                    label=f"{label} (control)"
                    if len(cube.coord(ensemble_coord).points) > 1
                    else label,
                )
                # Label with (perturbed) if part of an ensemble and not the control.
            else:
                iplt.plot(
                    coord,
                    cube_slice,
                    color=color,
                    ls="-",
                    lw=1.5,
                    alpha=0.75,
                    label=f"{label} (member)",
                )

        # Calculate the global min/max if multiple cubes are given.
        _, levels, _ = _colorbar_map_levels(cube, axis="y")
        if levels is not None:
            y_levels.append(min(levels))
            y_levels.append(max(levels))

    # Get the current axes.
    ax = plt.gca()

    # Add some labels and tweak the style.
    # check if cubes[0] works for single cube if not CubeList
    ax.set_xlabel(f"{coords[0].name()} / {coords[0].units}", fontsize=14)
    ax.set_ylabel(f"{cubes[0].name()} / {cubes[0].units}", fontsize=14)
    ax.set_title(title, fontsize=16)

    ax.ticklabel_format(axis="y", useOffset=False)
    ax.tick_params(axis="x", labelrotation=15)
    ax.tick_params(axis="both", labelsize=12)

    # Set y limits to global min and max, autoscale if colorbar doesn't exist.
    if y_levels:
        ax.set_ylim(min(y_levels), max(y_levels))
        # Add zero line.
        if min(y_levels) < 0.0 and max(y_levels) > 0.0:
            ax.axhline(y=0, xmin=0, xmax=1, ls="-", color="grey", lw=2)
        logging.debug(
            "Line plot with y-axis limits %s-%s", min(y_levels), max(y_levels)
        )
    else:
        ax.autoscale()

    # Add gridlines
    ax.grid(linestyle="--", color="grey", linewidth=1)
    # Ientify unique labels for legend
    handles = list(
        {
            label: handle
            for (handle, label) in zip(*ax.get_legend_handles_labels(), strict=True)
        }.values()
    )
    ax.legend(handles=handles, loc="best", ncol=1, frameon=False, fontsize=16)

    # Save plot.
    fig.savefig(filename, bbox_inches="tight", dpi=_get_plot_resolution())
    logging.info("Saved line plot to %s", filename)
    plt.close(fig)


def _plot_and_save_vertical_line_series(
    cubes: iris.cube.CubeList,
    coords: list[iris.coords.Coord],
    ensemble_coord: str,
    filename: str,
    series_coordinate: str,
    title: str,
    vmin: float,
    vmax: float,
    **kwargs,
):
    """Plot and save a 1D line series in vertical.

    Parameters
    ----------
    cubes: CubeList
        1 dimensional Cube or CubeList of the data to plot on x-axis.
    coord: list[Coord]
        Coordinates to plot on the y-axis, one per cube.
    ensemble_coord: str
        Ensemble coordinate in the cube.
    filename: str
        Filename of the plot to write.
    series_coordinate: str
        Coordinate to use as vertical axis.
    title: str
        Plot title.
    vmin: float
        Minimum value for the x-axis.
    vmax: float
        Maximum value for the x-axis.
    """
    # plot the vertical pressure axis using log scale
    fig = plt.figure(figsize=(10, 10), facecolor="w", edgecolor="k")

    model_colors_map = _get_model_colors_map(cubes)

    # Check match-up across sequence coords gives consistent sizes
    _validate_cubes_coords(cubes, coords)

    for cube, coord in zip(cubes, coords, strict=True):
        label = None
        color = "black"
        if model_colors_map:
            label = cube.attributes.get("model_name")
            color = model_colors_map.get(label)

        for cube_slice in cube.slices_over(ensemble_coord):
            # If ensemble data given plot control member with (control)
            # unless single forecast.
            if cube_slice.coord(ensemble_coord).points == [0]:
                iplt.plot(
                    cube_slice,
                    coord,
                    color=color,
                    marker="o",
                    ls="-",
                    lw=3,
                    label=f"{label} (control)"
                    if len(cube.coord(ensemble_coord).points) > 1
                    else label,
                )
            # If ensemble data given plot perturbed members with (perturbed).
            else:
                iplt.plot(
                    cube_slice,
                    coord,
                    color=color,
                    ls="-",
                    lw=1.5,
                    alpha=0.75,
                    label=f"{label} (member)",
                )

    # Get the current axis
    ax = plt.gca()

    # Special handling for pressure level data.
    if series_coordinate == "pressure":
        # Invert y-axis and set to log scale.
        ax.invert_yaxis()
        ax.set_yscale("log")

        # Define y-ticks and labels for pressure log axis.
        y_tick_labels = [
            "1000",
            "850",
            "700",
            "500",
            "300",
            "200",
            "100",
        ]
        y_ticks = [1000, 850, 700, 500, 300, 200, 100]

        # Set y-axis limits and ticks.
        ax.set_ylim(1100, 100)

    # Test if series_coordinate is model level data. The UM data uses
    # model_level_number and lfric uses full_levels as coordinate.
    elif series_coordinate in ("model_level_number", "full_levels", "half_levels"):
        # Define y-ticks and labels for vertical axis.
        y_ticks = iter_maybe(cubes)[0].coord(series_coordinate).points
        y_tick_labels = [str(int(i)) for i in y_ticks]
        ax.set_ylim(min(y_ticks), max(y_ticks))

    ax.set_yticks(y_ticks)
    ax.set_yticklabels(y_tick_labels)

    # Set x-axis limits.
    ax.set_xlim(vmin, vmax)
    # Mark y=0 if present in plot.
    if vmin < 0.0 and vmax > 0.0:
        ax.axvline(x=0, ymin=0, ymax=1, ls="-", color="grey", lw=2)

    # Add some labels and tweak the style.
    ax.set_ylabel(f"{coord.name()} / {coord.units}", fontsize=14)
    ax.set_xlabel(
        f"{iter_maybe(cubes)[0].name()} / {iter_maybe(cubes)[0].units}", fontsize=14
    )
    ax.set_title(title, fontsize=16)
    ax.ticklabel_format(axis="x")
    ax.tick_params(axis="y")
    ax.tick_params(axis="both", labelsize=12)

    # Add gridlines
    ax.grid(linestyle="--", color="grey", linewidth=1)
    # Ientify unique labels for legend
    handles = list(
        {
            label: handle
            for (handle, label) in zip(*ax.get_legend_handles_labels(), strict=True)
        }.values()
    )
    ax.legend(handles=handles, loc="best", ncol=1, frameon=False, fontsize=16)

    # Save plot.
    fig.savefig(filename, bbox_inches="tight", dpi=_get_plot_resolution())
    logging.info("Saved line plot to %s", filename)
    plt.close(fig)


def _plot_and_save_scatter_plot(
    cube_x: iris.cube.Cube | iris.cube.CubeList,
    cube_y: iris.cube.Cube | iris.cube.CubeList,
    filename: str,
    title: str,
    one_to_one: bool,
    **kwargs,
):
    """Plot and save a 2D scatter plot.

    Parameters
    ----------
    cube_x: Cube | CubeList
        1 dimensional Cube or CubeList of the data to plot on x-axis.
    cube_y: Cube | CubeList
        1 dimensional Cube or CubeList of the data to plot on y-axis.
    filename: str
        Filename of the plot to write.
    title: str
        Plot title.
    one_to_one: bool
        Whether a 1:1 line is plotted.
    """
    fig = plt.figure(figsize=(10, 10), facecolor="w", edgecolor="k")
    # plot the cube_x and cube_y 1D fields as a scatter plot. If they are CubeLists this ensures
    # to pair each cube from cube_x with the corresponding cube from cube_y, allowing to iterate
    # over the pairs simultaneously.

    # Ensure cube_x and cube_y are iterable
    cube_x_iterable = iter_maybe(cube_x)
    cube_y_iterable = iter_maybe(cube_y)

    for cube_x_iter, cube_y_iter in zip(cube_x_iterable, cube_y_iterable, strict=True):
        iplt.scatter(cube_x_iter, cube_y_iter)
    if one_to_one is True:
        plt.plot(
            [
                np.nanmin([np.nanmin(cube_y.data), np.nanmin(cube_x.data)]),
                np.nanmax([np.nanmax(cube_y.data), np.nanmax(cube_x.data)]),
            ],
            [
                np.nanmin([np.nanmin(cube_y.data), np.nanmin(cube_x.data)]),
                np.nanmax([np.nanmax(cube_y.data), np.nanmax(cube_x.data)]),
            ],
            "k",
            linestyle="--",
        )
    ax = plt.gca()

    # Add some labels and tweak the style.
    ax.set_xlabel(f"{cube_x[0].name()} / {cube_x[0].units}", fontsize=14)
    ax.set_ylabel(f"{cube_y[0].name()} / {cube_y[0].units}", fontsize=14)
    ax.set_title(title, fontsize=16)
    ax.ticklabel_format(axis="y", useOffset=False)
    ax.tick_params(axis="x", labelrotation=15)
    ax.tick_params(axis="both", labelsize=12)
    ax.autoscale()

    # Save plot.
    fig.savefig(filename, bbox_inches="tight", dpi=_get_plot_resolution())
    logging.info("Saved scatter plot to %s", filename)
    plt.close(fig)


def _plot_and_save_vector_plot(
    cube_u: iris.cube.Cube,
    cube_v: iris.cube.Cube,
    filename: str,
    title: str,
    method: Literal["contourf", "pcolormesh"],
    **kwargs,
):
    """Plot and save a 2D vector plot.

    Parameters
    ----------
    cube_u: Cube
        2 dimensional Cube of u component of the data.
    cube_v: Cube
        2 dimensional Cube of v component of the data.
    filename: str
        Filename of the plot to write.
    title: str
        Plot title.
    """
    fig = plt.figure(figsize=(10, 10), facecolor="w", edgecolor="k")

    # Create a cube containing the magnitude of the vector field.
    cube_vec_mag = (cube_u**2 + cube_v**2) ** 0.5
    cube_vec_mag.rename(f"{cube_u.name()}_{cube_v.name()}_magnitude")

    # Specify the color bar
    cmap, levels, norm = _colorbar_map_levels(cube_vec_mag)

    # Setup plot map projection, extent and coastlines.
    axes = _setup_spatial_map(cube_vec_mag, fig, cmap)

    if method == "contourf":
        # Filled contour plot of the field.
        plot = iplt.contourf(cube_vec_mag, cmap=cmap, levels=levels, norm=norm)
    elif method == "pcolormesh":
        try:
            vmin = min(levels)
            vmax = max(levels)
        except TypeError:
            vmin, vmax = None, None
        # pcolormesh plot of the field and ensure to use norm and not vmin/vmax
        # if levels are defined.
        if norm is not None:
            vmin = None
            vmax = None
        plot = iplt.pcolormesh(cube_vec_mag, cmap=cmap, norm=norm, vmin=vmin, vmax=vmax)
    else:
        raise ValueError(f"Unknown plotting method: {method}")

    # Check to see if transect, and if so, adjust y axis.
    if is_transect(cube_vec_mag):
        if "pressure" in [coord.name() for coord in cube_vec_mag.coords()]:
            axes.invert_yaxis()
            axes.set_yscale("log")
            axes.set_ylim(1100, 100)
        # If both model_level_number and level_height exists, iplt can construct
        # plot as a function of height above orography (NOT sea level).
        elif {"model_level_number", "level_height"}.issubset(
            {coord.name() for coord in cube_vec_mag.coords()}
        ):
            axes.set_yscale("log")

        axes.set_title(
            f"{title}\n"
            f"Start Lat: {cube_vec_mag.attributes['transect_coords'].split('_')[0]}"
            f" Start Lon: {cube_vec_mag.attributes['transect_coords'].split('_')[1]}"
            f" End Lat: {cube_vec_mag.attributes['transect_coords'].split('_')[2]}"
            f" End Lon: {cube_vec_mag.attributes['transect_coords'].split('_')[3]}",
            fontsize=16,
        )

    else:
        # Add title.
        axes.set_title(title, fontsize=16)

    # Add watermark with min/max/mean. Currently not user togglable.
    # In the bbox dictionary, fc and ec are hex colour codes for grey shade.
    axes.annotate(
        f"Min: {np.min(cube_vec_mag.data):.3g} Max: {np.max(cube_vec_mag.data):.3g} Mean: {np.mean(cube_vec_mag.data):.3g}",
        xy=(1, -0.05),
        xycoords="axes fraction",
        xytext=(-5, 5),
        textcoords="offset points",
        ha="right",
        va="bottom",
        size=11,
        bbox=dict(boxstyle="round", fc="#cccccc", ec="#808080", alpha=0.9),
    )

    # Add colour bar.
    cbar = fig.colorbar(plot, orientation="horizontal", pad=0.042, shrink=0.7)
    cbar.set_label(label=f"{cube_vec_mag.name()} ({cube_vec_mag.units})", size=14)
    # add ticks and tick_labels for every levels if less than 20 levels exist
    if levels is not None and len(levels) < 20:
        cbar.set_ticks(levels)
        cbar.set_ticklabels([f"{level:.1f}" for level in levels])

    # 30 barbs along the longest axis of the plot, or a barb per point for data
    # with less than 30 points.
    step = max(max(cube_u.shape) // 30, 1)
    iplt.quiver(cube_u[::step, ::step], cube_v[::step, ::step], pivot="middle")

    # Save plot.
    fig.savefig(filename, bbox_inches="tight", dpi=_get_plot_resolution())
    logging.info("Saved vector plot to %s", filename)
    plt.close(fig)


def _plot_and_save_histogram_series(
    cubes: iris.cube.Cube | iris.cube.CubeList,
    filename: str,
    title: str,
    vmin: float,
    vmax: float,
    **kwargs,
):
    """Plot and save a histogram series.

    Parameters
    ----------
    cubes: Cube or CubeList
        2 dimensional Cube or CubeList of the data to plot as histogram.
    filename: str
        Filename of the plot to write.
    title: str
        Plot title.
    vmin: float
        minimum for colorbar
    vmax: float
        maximum for colorbar
    """
    fig = plt.figure(figsize=(10, 10), facecolor="w", edgecolor="k")
    ax = plt.gca()

    model_colors_map = _get_model_colors_map(cubes)

    # Set default that histograms will produce probability density function
    # at each bin (integral over range sums to 1).
    density = True

    for cube in iter_maybe(cubes):
        # Easier to check title (where var name originates)
        # than seeing if long names exist etc.
        # Exception case, where distribution better fits log scales/bins.
        if "surface_microphysical" in title:
            if "amount" in title:
                # Compute histogram following Klingaman et al. (2017): ASoP
                bin2 = np.exp(np.log(0.02) + 0.1 * np.linspace(0, 99, 100))
                bins = np.pad(bin2, (1, 0), "constant", constant_values=0)
                density = False
            else:
                bins = 10.0 ** (
                    np.arange(-10, 27, 1) / 10.0
                )  # Suggestion from RMED toolbox.
                bins = np.insert(bins, 0, 0)
                ax.set_yscale("log")
            vmin = bins[1]
            vmax = bins[-1]  # Manually set vmin/vmax to override json derived value.
            ax.set_xscale("log")
        elif "lightning" in title:
            bins = [0, 1, 2, 3, 4, 5]
        else:
            bins = np.linspace(vmin, vmax, 51)
        logging.debug(
            "Plotting histogram with %s bins %s - %s.",
            np.size(bins),
            np.min(bins),
            np.max(bins),
        )

        # Reshape cube data into a single array to allow for a single histogram.
        # Otherwise we plot xdim histograms stacked.
        cube_data_1d = (cube.data).flatten()

        label = None
        color = "black"
        if model_colors_map:
            label = cube.attributes.get("model_name")
            color = model_colors_map[label]
        x, y = np.histogram(cube_data_1d, bins=bins, density=density)

        # Compute area under curve.
        if "surface_microphysical" in title and "amount" in title:
            bin_mean = (bins[:-1] + bins[1:]) / 2.0
            x = x * bin_mean / x.sum()
            x = x[1:]
            y = y[1:]

        ax.plot(
            y[:-1], x, color=color, linewidth=3, marker="o", markersize=6, label=label
        )

    # Add some labels and tweak the style.
    ax.set_title(title, fontsize=16)
    ax.set_xlabel(
        f"{iter_maybe(cubes)[0].name()} / {iter_maybe(cubes)[0].units}", fontsize=14
    )
    ax.set_ylabel("Normalised probability density", fontsize=14)
    if "surface_microphysical" in title and "amount" in title:
        ax.set_ylabel(
            f"Contribution to mean ({iter_maybe(cubes)[0].units})", fontsize=14
        )
    ax.set_xlim(vmin, vmax)
    ax.tick_params(axis="both", labelsize=12)

    # Overlay grid-lines onto histogram plot.
    ax.grid(linestyle="--", color="grey", linewidth=1)
    if model_colors_map:
        ax.legend(loc="best", ncol=1, frameon=False, fontsize=16)

    # Save plot.
    fig.savefig(filename, bbox_inches="tight", dpi=_get_plot_resolution())
    logging.info("Saved line plot to %s", filename)
    plt.close(fig)


def _plot_and_save_postage_stamp_histogram_series(
    cube: iris.cube.Cube,
    filename: str,
    title: str,
    stamp_coordinate: str,
    vmin: float,
    vmax: float,
    **kwargs,
):
    """Plot and save postage (ensemble members) stamps for a histogram series.

    Parameters
    ----------
    cube: Cube
        2 dimensional Cube of the data to plot as histogram.
    filename: str
        Filename of the plot to write.
    title: str
        Plot title.
    stamp_coordinate: str
        Coordinate that becomes different plots.
    vmin: float
        minimum for pdf x-axis
    vmax: float
        maximum for pdf x-axis
    """
    # Use the smallest square grid that will fit the members.
    grid_size = int(math.ceil(math.sqrt(len(cube.coord(stamp_coordinate).points))))

    fig = plt.figure(figsize=(10, 10), facecolor="w", edgecolor="k")
    # Make a subplot for each member.
    for member, subplot in zip(
        cube.slices_over(stamp_coordinate), range(1, grid_size**2 + 1), strict=False
    ):
        # Implicit interface is much easier here, due to needing to have the
        # cartopy GeoAxes generated.
        plt.subplot(grid_size, grid_size, subplot)
        # Reshape cube data into a single array to allow for a single histogram.
        # Otherwise we plot xdim histograms stacked.
        member_data_1d = (member.data).flatten()
        plt.hist(member_data_1d, density=True, stacked=True)
        ax = plt.gca()
        ax.set_title(f"Member #{member.coord(stamp_coordinate).points[0]}")
        ax.set_xlim(vmin, vmax)

    # Overall figure title.
    fig.suptitle(title, fontsize=16)

    fig.savefig(filename, bbox_inches="tight", dpi=_get_plot_resolution())
    logging.info("Saved histogram postage stamp plot to %s", filename)
    plt.close(fig)


def _plot_and_save_postage_stamps_in_single_plot_histogram_series(
    cube: iris.cube.Cube,
    filename: str,
    title: str,
    stamp_coordinate: str,
    vmin: float,
    vmax: float,
    **kwargs,
):
    fig, ax = plt.subplots(figsize=(10, 10), facecolor="w", edgecolor="k")
    ax.set_title(title, fontsize=16)
    ax.set_xlim(vmin, vmax)
    ax.set_xlabel(f"{cube.name()} / {cube.units}", fontsize=14)
    ax.set_ylabel("normalised probability density", fontsize=14)
    # Loop over all slices along the stamp_coordinate
    for member in cube.slices_over(stamp_coordinate):
        # Flatten the member data to 1D
        member_data_1d = member.data.flatten()
        # Plot the histogram using plt.hist
        plt.hist(
            member_data_1d,
            density=True,
            stacked=True,
            label=f"Member #{member.coord(stamp_coordinate).points[0]}",
        )

    # Add a legend
    ax.legend(fontsize=16)

    # Save the figure to a file
    plt.savefig(filename, bbox_inches="tight", dpi=_get_plot_resolution())

    # Close the figure
    plt.close(fig)


def _spatial_plot(
    method: Literal["contourf", "pcolormesh"],
    cube: iris.cube.Cube,
    filename: str | None,
    sequence_coordinate: str,
    stamp_coordinate: str,
):
    """Plot a spatial variable onto a map from a 2D, 3D, or 4D cube.

    A 2D spatial field can be plotted, but if the sequence_coordinate is present
    then a sequence of plots will be produced. Similarly if the stamp_coordinate
    is present then postage stamp plots will be produced.

    Parameters
    ----------
    method: "contourf" | "pcolormesh"
        The plotting method to use.
    cube: Cube
        Iris cube of the data to plot. It should have two spatial dimensions,
        such as lat and lon, and may also have a another two dimension to be
        plotted sequentially and/or as postage stamp plots.
    filename: str | None
        Name of the plot to write, used as a prefix for plot sequences. If None
        uses the recipe name.
    sequence_coordinate: str
        Coordinate about which to make a plot sequence. Defaults to ``"time"``.
        This coordinate must exist in the cube.
    stamp_coordinate: str
        Coordinate about which to plot postage stamp plots. Defaults to
        ``"realization"``.

    Raises
    ------
    ValueError
        If the cube doesn't have the right dimensions.
    TypeError
        If the cube isn't a single cube.
    """
    recipe_title = get_recipe_metadata().get("title", "Untitled")

    # Ensure we have a name for the plot file.
    if filename is None:
        filename = slugify(recipe_title)

    # Ensure we've got a single cube.
    cube = _check_single_cube(cube)

    # Make postage stamp plots if stamp_coordinate exists and has more than a
    # single point.
    plotting_func = _plot_and_save_spatial_plot
    try:
        if cube.coord(stamp_coordinate).shape[0] > 1:
            plotting_func = _plot_and_save_postage_stamp_spatial_plot
    except iris.exceptions.CoordinateNotFoundError:
        pass

    # Must have a sequence coordinate.
    try:
        cube.coord(sequence_coordinate)
    except iris.exceptions.CoordinateNotFoundError as err:
        raise ValueError(f"Cube must have a {sequence_coordinate} coordinate.") from err

    # Create a plot for each value of the sequence coordinate.
    plot_index = []
    nplot = np.size(cube.coord(sequence_coordinate).points)
    for cube_slice in cube.slices_over(sequence_coordinate):
        # Use sequence value so multiple sequences can merge.
        sequence_value = cube_slice.coord(sequence_coordinate).points[0]
        plot_filename = f"{filename.rsplit('.', 1)[0]}_{sequence_value}.png"
        coord = cube_slice.coord(sequence_coordinate)
        # Format the coordinate value in a unit appropriate way.
        title = f"{recipe_title}\n [{coord.units.title(coord.points[0])}]"
        # Use sequence (e.g. time) bounds if plotting single non-sequence outputs
        if nplot == 1 and coord.has_bounds:
            if np.size(coord.bounds) > 1:
                title = f"{recipe_title}\n [{coord.units.title(coord.bounds[0][0])} to {coord.units.title(coord.bounds[0][1])}]"
        # Do the actual plotting.
        plotting_func(
            cube_slice,
            filename=plot_filename,
            stamp_coordinate=stamp_coordinate,
            title=title,
            method=method,
        )
        plot_index.append(plot_filename)

    # Add list of plots to plot metadata.
    complete_plot_index = _append_to_plot_index(plot_index)

    # Make a page to display the plots.
    _make_plot_html_page(complete_plot_index)


def _custom_colormap_mask(cube: iris.cube.Cube, axis: Literal["x", "y"] | None = None):
    """Get colourmap for mask.

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
            logging.debug("Colourmap for %s.", cube.long_name)
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
            logging.debug("Colourmap for %s.", cube.long_name)
            return cmap, levels, norm


def _custom_beaufort_scale(cube: iris.cube.Cube, axis: Literal["x", "y"] | None = None):
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


def _custom_colormap_celsius(cube: iris.cube.Cube, cmap, levels, norm):
    """Return altered colourmap for temperature with change in units to Celsius.

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


def _custom_colormap_probability(
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


def _custom_colourmap_precipitation(cube: iris.cube.Cube, cmap, levels, norm):
    """Return a custom colourmap for the current recipe."""
    varnames = filter(None, [cube.long_name, cube.standard_name, cube.var_name])
    if (
        any("surface_microphysical" in name for name in varnames)
        and "difference" not in cube.long_name
        and "mask" not in cube.long_name
    ):
        # Define the levels and colors
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
        logging.info("change colormap for surface_microphysical variable colorbar.")
    else:
        # do nothing and keep existing colorbar attributes
        cmap = cmap
        levels = levels
        norm = norm
    return cmap, levels, norm


def _custom_colourmap_visibility_in_air(cube: iris.cube.Cube, cmap, levels, norm):
    """Return a custom colourmap for the current recipe."""
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


def _get_num_models(cube: iris.cube.Cube | iris.cube.CubeList) -> int:
    """Return number of models based on cube attributes."""
    model_names = list(
        filter(
            lambda x: x is not None,
            {cb.attributes.get("model_name", None) for cb in iter_maybe(cube)},
        )
    )
    if not model_names:
        logging.debug("Missing model names. Will assume single model.")
        return 1
    else:
        return len(model_names)


def _validate_cube_shape(
    cube: iris.cube.Cube | iris.cube.CubeList, num_models: int
) -> None:
    """Check all cubes have a model name."""
    if isinstance(cube, iris.cube.CubeList) and len(cube) != num_models:
        raise ValueError(
            f"The number of model names ({num_models}) should equal the number "
            f"of cubes ({len(cube)})."
        )


def _validate_cubes_coords(
    cubes: iris.cube.CubeList, coords: list[iris.coords.Coord]
) -> None:
    """Check same number of cubes as sequence coordinate for zip functions."""
    if len(cubes) != len(coords):
        raise ValueError(
            f"The number of CubeList entries ({len(cubes)}) should equal the number "
            f"of sequence coordinates ({len(coords)})."
            f"Check that number of time entries in input data are consistent if "
            f"performing time-averaging steps prior to plotting outputs."
        )


####################
# Public functions #
####################


def spatial_contour_plot(
    cube: iris.cube.Cube,
    filename: str = None,
    sequence_coordinate: str = "time",
    stamp_coordinate: str = "realization",
    **kwargs,
) -> iris.cube.Cube:
    """Plot a spatial variable onto a map from a 2D, 3D, or 4D cube.

    A 2D spatial field can be plotted, but if the sequence_coordinate is present
    then a sequence of plots will be produced. Similarly if the stamp_coordinate
    is present then postage stamp plots will be produced.

    Parameters
    ----------
    cube: Cube
        Iris cube of the data to plot. It should have two spatial dimensions,
        such as lat and lon, and may also have a another two dimension to be
        plotted sequentially and/or as postage stamp plots.
    filename: str, optional
        Name of the plot to write, used as a prefix for plot sequences. Defaults
        to the recipe name.
    sequence_coordinate: str, optional
        Coordinate about which to make a plot sequence. Defaults to ``"time"``.
        This coordinate must exist in the cube.
    stamp_coordinate: str, optional
        Coordinate about which to plot postage stamp plots. Defaults to
        ``"realization"``.

    Returns
    -------
    Cube
        The original cube (so further operations can be applied).

    Raises
    ------
    ValueError
        If the cube doesn't have the right dimensions.
    TypeError
        If the cube isn't a single cube.
    """
    _spatial_plot("contourf", cube, filename, sequence_coordinate, stamp_coordinate)
    return cube


def spatial_pcolormesh_plot(
    cube: iris.cube.Cube,
    filename: str = None,
    sequence_coordinate: str = "time",
    stamp_coordinate: str = "realization",
    **kwargs,
) -> iris.cube.Cube:
    """Plot a spatial variable onto a map from a 2D, 3D, or 4D cube.

    A 2D spatial field can be plotted, but if the sequence_coordinate is present
    then a sequence of plots will be produced. Similarly if the stamp_coordinate
    is present then postage stamp plots will be produced.

    This function is significantly faster than ``spatial_contour_plot``,
    especially at high resolutions, and should be preferred unless contiguous
    contour areas are important.

    Parameters
    ----------
    cube: Cube
        Iris cube of the data to plot. It should have two spatial dimensions,
        such as lat and lon, and may also have a another two dimension to be
        plotted sequentially and/or as postage stamp plots.
    filename: str, optional
        Name of the plot to write, used as a prefix for plot sequences. Defaults
        to the recipe name.
    sequence_coordinate: str, optional
        Coordinate about which to make a plot sequence. Defaults to ``"time"``.
        This coordinate must exist in the cube.
    stamp_coordinate: str, optional
        Coordinate about which to plot postage stamp plots. Defaults to
        ``"realization"``.

    Returns
    -------
    Cube
        The original cube (so further operations can be applied).

    Raises
    ------
    ValueError
        If the cube doesn't have the right dimensions.
    TypeError
        If the cube isn't a single cube.
    """
    _spatial_plot("pcolormesh", cube, filename, sequence_coordinate, stamp_coordinate)
    return cube


# TODO: Expand function to handle ensemble data.
# line_coordinate: str, optional
#     Coordinate about which to plot multiple lines. Defaults to
#     ``"realization"``.
def plot_line_series(
    cube: iris.cube.Cube | iris.cube.CubeList,
    filename: str = None,
    series_coordinate: str = "time",
    # line_coordinate: str = "realization",
    **kwargs,
) -> iris.cube.Cube | iris.cube.CubeList:
    """Plot a line plot for the specified coordinate.

    The Cube or CubeList must be 1D.

    Parameters
    ----------
    iris.cube | iris.cube.CubeList
        Cube or CubeList of the data to plot. The individual cubes should have a single dimension.
        The cubes should cover the same phenomenon i.e. all cubes contain temperature data.
        We do not support different data such as temperature and humidity in the same CubeList for plotting.
    filename: str, optional
        Name of the plot to write, used as a prefix for plot sequences. Defaults
        to the recipe name.
    series_coordinate: str, optional
        Coordinate about which to make a series. Defaults to ``"time"``. This
        coordinate must exist in the cube.

    Returns
    -------
    iris.cube.Cube | iris.cube.CubeList
        The original Cube or CubeList (so further operations can be applied).
        plotted data.

    Raises
    ------
    ValueError
        If the cubes don't have the right dimensions.
    TypeError
        If the cube isn't a Cube or CubeList.
    """
    # Ensure we have a name for the plot file.
    title = get_recipe_metadata().get("title", "Untitled")

    if filename is None:
        filename = slugify(title)

    # Add file extension.
    plot_filename = f"{filename.rsplit('.', 1)[0]}.png"

    num_models = _get_num_models(cube)

    _validate_cube_shape(cube, num_models)

    # Iterate over all cubes and extract coordinate to plot.
    cubes = iter_maybe(cube)
    coords = []
    for cube in cubes:
        try:
            coords.append(cube.coord(series_coordinate))
        except iris.exceptions.CoordinateNotFoundError as err:
            raise ValueError(
                f"Cube must have a {series_coordinate} coordinate."
            ) from err
        if cube.ndim > 2 or not cube.coords("realization"):
            raise ValueError("Cube must be 1D or 2D with a realization coordinate.")

    # Do the actual plotting.
    _plot_and_save_line_series(cubes, coords, "realization", plot_filename, title)

    # Add list of plots to plot metadata.
    plot_index = _append_to_plot_index([plot_filename])

    # Make a page to display the plots.
    _make_plot_html_page(plot_index)

    return cube


def plot_vertical_line_series(
    cubes: iris.cube.Cube | iris.cube.CubeList,
    filename: str = None,
    series_coordinate: str = "model_level_number",
    sequence_coordinate: str = "time",
    # line_coordinate: str = "realization",
    **kwargs,
) -> iris.cube.Cube | iris.cube.CubeList:
    """Plot a line plot against a type of vertical coordinate.

    The Cube or CubeList must be 1D.

    A 1D line plot with y-axis as pressure coordinate can be plotted, but if the sequence_coordinate is present
    then a sequence of plots will be produced.

    Parameters
    ----------
    iris.cube | iris.cube.CubeList
        Cube or CubeList of the data to plot. The individual cubes should have a single dimension.
        The cubes should cover the same phenomenon i.e. all cubes contain temperature data.
        We do not support different data such as temperature and humidity in the same CubeList for plotting.
    filename: str, optional
        Name of the plot to write, used as a prefix for plot sequences. Defaults
        to the recipe name.
    series_coordinate: str, optional
        Coordinate to plot on the y-axis. Can be ``pressure`` or
        ``model_level_number`` for UM, or ``full_levels`` or ``half_levels``
        for LFRic. Defaults to ``model_level_number``.
        This coordinate must exist in the cube.
    sequence_coordinate: str, optional
        Coordinate about which to make a plot sequence. Defaults to ``"time"``.
        This coordinate must exist in the cube.

    Returns
    -------
    iris.cube.Cube | iris.cube.CubeList
        The original Cube or CubeList (so further operations can be applied).
        Plotted data.

    Raises
    ------
    ValueError
        If the cubes doesn't have the right dimensions.
    TypeError
        If the cube isn't a Cube or CubeList.
    """
    # Ensure we have a name for the plot file.
    recipe_title = get_recipe_metadata().get("title", "Untitled")

    if filename is None:
        filename = slugify(recipe_title)

    cubes = iter_maybe(cubes)
    # Initialise empty list to hold all data from all cubes in a CubeList
    all_data = []

    # Store min/max ranges for x range.
    x_levels = []

    num_models = _get_num_models(cubes)

    _validate_cube_shape(cubes, num_models)

    # Iterate over all cubes in cube or CubeList and plot.
    coords = []
    for cube in cubes:
        # Test if series coordinate i.e. pressure level exist for any cube with cube.ndim >=1.
        try:
            coords.append(cube.coord(series_coordinate))
        except iris.exceptions.CoordinateNotFoundError as err:
            raise ValueError(
                f"Cube must have a {series_coordinate} coordinate."
            ) from err

        try:
            if cube.ndim > 1 or not cube.coords("realization"):
                cube.coord(sequence_coordinate)
        except iris.exceptions.CoordinateNotFoundError as err:
            raise ValueError(
                f"Cube must have a {sequence_coordinate} coordinate or be 1D, or 2D with a realization coordinate."
            ) from err

        # Get minimum and maximum from levels information.
        _, levels, _ = _colorbar_map_levels(cube, axis="x")
        if levels is not None:
            x_levels.append(min(levels))
            x_levels.append(max(levels))
        else:
            all_data.append(cube.data)

    if len(x_levels) == 0:
        # Combine all data into a single NumPy array
        combined_data = np.concatenate(all_data)

        # Set the lower and upper limit for the x-axis to ensure all plots have
        # same range. This needs to read the whole cube over the range of the
        # sequence and if applicable postage stamp coordinate.
        vmin = np.floor(combined_data.min())
        vmax = np.ceil(combined_data.max())
    else:
        vmin = min(x_levels)
        vmax = max(x_levels)

    # Matching the slices (matching by seq coord point; it may happen that
    # evaluated models do not cover the same seq coord range, hence matching
    # necessary)
    def filter_cube_iterables(cube_iterables) -> bool:
        return len(cube_iterables) == len(coords)

    cube_iterables = filter(
        filter_cube_iterables,
        (
            iris.cube.CubeList(
                s
                for s in itertools.chain.from_iterable(
                    cb.slices_over(sequence_coordinate) for cb in cubes
                )
                if s.coord(sequence_coordinate).points[0] == point
            )
            for point in sorted(
                set(
                    itertools.chain.from_iterable(
                        cb.coord(sequence_coordinate).points for cb in cubes
                    )
                )
            )
        ),
    )

    # Create a plot for each value of the sequence coordinate.
    # Allowing for multiple cubes in a CubeList to be plotted in the same plot for
    # similar sequence values. Passing a CubeList into the internal plotting function
    # for similar values of the sequence coordinate. cube_slice can be an iris.cube.Cube
    # or an iris.cube.CubeList.
    plot_index = []
    nplot = np.size(cubes[0].coord(sequence_coordinate).points)
    for cubes_slice in cube_iterables:
        # Use sequence value so multiple sequences can merge.
        seq_coord = cubes_slice[0].coord(sequence_coordinate)
        sequence_value = seq_coord.points[0]
        plot_filename = f"{filename.rsplit('.', 1)[0]}_{sequence_value}.png"
        # Format the coordinate value in a unit appropriate way.
        title = f"{recipe_title}\n [{seq_coord.units.title(sequence_value)}]"
        # Use sequence (e.g. time) bounds if plotting single non-sequence outputs
        if nplot == 1 and seq_coord.has_bounds:
            if np.size(seq_coord.bounds) > 1:
                title = f"{recipe_title}\n [{seq_coord.units.title(seq_coord.bounds[0][0])} to {seq_coord.units.title(seq_coord.bounds[0][1])}]"
        # Do the actual plotting.
        _plot_and_save_vertical_line_series(
            cubes_slice,
            coords,
            "realization",
            plot_filename,
            series_coordinate,
            title=title,
            vmin=vmin,
            vmax=vmax,
        )
        plot_index.append(plot_filename)

    # Add list of plots to plot metadata.
    complete_plot_index = _append_to_plot_index(plot_index)

    # Make a page to display the plots.
    _make_plot_html_page(complete_plot_index)

    return cubes


def scatter_plot(
    cube_x: iris.cube.Cube | iris.cube.CubeList,
    cube_y: iris.cube.Cube | iris.cube.CubeList,
    filename: str = None,
    one_to_one: bool = True,
    **kwargs,
) -> iris.cube.CubeList:
    """Plot a scatter plot between two variables.

    Both cubes must be 1D.

    Parameters
    ----------
    cube_x: Cube | CubeList
        1 dimensional Cube of the data to plot on y-axis.
    cube_y: Cube | CubeList
        1 dimensional Cube of the data to plot on x-axis.
    filename: str, optional
        Filename of the plot to write.
    one_to_one: bool, optional
        If True a 1:1 line is plotted; if False it is not. Default is True.

    Returns
    -------
    cubes: CubeList
        CubeList of the original x and y cubes for further processing.

    Raises
    ------
    ValueError
        If the cube doesn't have the right dimensions and cubes not the same
        size.
    TypeError
        If the cube isn't a single cube.

    Notes
    -----
    Scatter plots are used for determining if there is a relationship between
    two variables. Positive relations have a slope going from bottom left to top
    right; Negative relations have a slope going from top left to bottom right.

    A variant of the scatter plot is the quantile-quantile plot. This plot does
    not use all data points, but the selected quantiles of each variable
    instead. Quantile-quantile plots are valuable for comparing against
    observations and other models. Identical percentiles between the variables
    will lie on the one-to-one line implying the values correspond well to each
    other. Where there is a deviation from the one-to-one line a range of
    possibilities exist depending on how and where the data is shifted (e.g.,
    Wilks 2011 [Wilks2011]_).

    For distributions above the one-to-one line the distribution is left-skewed;
    below is right-skewed. A distinct break implies a bimodal distribution, and
    closer values/values further apart at the tails imply poor representation of
    the extremes.

    References
    ----------
    .. [Wilks2011] Wilks, D.S., (2011) "Statistical Methods in the Atmospheric
       Sciences" Third Edition, vol. 100, Academic Press, Oxford, UK, 676 pp.
    """
    # Iterate over all cubes in cube or CubeList and plot.
    for cube_iter in iter_maybe(cube_x):
        # Check cubes are correct shape.
        cube_iter = _check_single_cube(cube_iter)
        if cube_iter.ndim > 1:
            raise ValueError("cube_x must be 1D.")

    # Iterate over all cubes in cube or CubeList and plot.
    for cube_iter in iter_maybe(cube_y):
        # Check cubes are correct shape.
        cube_iter = _check_single_cube(cube_iter)
        if cube_iter.ndim > 1:
            raise ValueError("cube_y must be 1D.")

    # Ensure we have a name for the plot file.
    title = get_recipe_metadata().get("title", "Untitled")

    if filename is None:
        filename = slugify(title)

    # Add file extension.
    plot_filename = f"{filename.rsplit('.', 1)[0]}.png"

    # Do the actual plotting.
    _plot_and_save_scatter_plot(cube_x, cube_y, plot_filename, title, one_to_one)

    # Add list of plots to plot metadata.
    plot_index = _append_to_plot_index([plot_filename])

    # Make a page to display the plots.
    _make_plot_html_page(plot_index)

    return iris.cube.CubeList([cube_x, cube_y])


def vector_plot(
    cube_u: iris.cube.Cube,
    cube_v: iris.cube.Cube,
    filename: str = None,
    sequence_coordinate: str = "time",
    **kwargs,
) -> iris.cube.CubeList:
    """Plot a vector plot based on the input u and v components."""
    recipe_title = get_recipe_metadata().get("title", "Untitled")

    # Ensure we have a name for the plot file.
    if filename is None:
        filename = slugify(recipe_title)

    # Cubes must have a matching sequence coordinate.
    try:
        # Check that the u and v cubes have the same sequence coordinate.
        if cube_u.coord(sequence_coordinate) != cube_v.coord(sequence_coordinate):
            raise ValueError("Coordinates do not match.")
    except (iris.exceptions.CoordinateNotFoundError, ValueError) as err:
        raise ValueError(
            f"Cubes should have matching {sequence_coordinate} coordinate:\n{cube_u}\n{cube_v}"
        ) from err

    # Create a plot for each value of the sequence coordinate.
    plot_index = []
    for cube_u_slice, cube_v_slice in zip(
        cube_u.slices_over(sequence_coordinate),
        cube_v.slices_over(sequence_coordinate),
        strict=True,
    ):
        # Use sequence value so multiple sequences can merge.
        sequence_value = cube_u_slice.coord(sequence_coordinate).points[0]
        plot_filename = f"{filename.rsplit('.', 1)[0]}_{sequence_value}.png"
        coord = cube_u_slice.coord(sequence_coordinate)
        # Format the coordinate value in a unit appropriate way.
        title = f"{recipe_title}\n{coord.units.title(coord.points[0])}"
        # Do the actual plotting.
        _plot_and_save_vector_plot(
            cube_u_slice,
            cube_v_slice,
            filename=plot_filename,
            title=title,
            method="contourf",
        )
        plot_index.append(plot_filename)

    # Add list of plots to plot metadata.
    complete_plot_index = _append_to_plot_index(plot_index)

    # Make a page to display the plots.
    _make_plot_html_page(complete_plot_index)

    return iris.cube.CubeList([cube_u, cube_v])


def plot_histogram_series(
    cubes: iris.cube.Cube | iris.cube.CubeList,
    filename: str = None,
    sequence_coordinate: str = "time",
    stamp_coordinate: str = "realization",
    single_plot: bool = False,
    **kwargs,
) -> iris.cube.Cube | iris.cube.CubeList:
    """Plot a histogram plot for each vertical level provided.

    A histogram plot can be plotted, but if the sequence_coordinate (i.e. time)
    is present then a sequence of plots will be produced using the time slider
    functionality to scroll through histograms against time. If a
    stamp_coordinate is present then postage stamp plots will be produced. If
    stamp_coordinate and single_plot is True, all postage stamp plots will be
    plotted in a single plot instead of separate postage stamp plots.

    Parameters
    ----------
    cubes: Cube | iris.cube.CubeList
        Iris cube or CubeList of the data to plot. It should have a single dimension other
        than the stamp coordinate.
        The cubes should cover the same phenomenon i.e. all cubes contain temperature data.
        We do not support different data such as temperature and humidity in the same CubeList for plotting.
    filename: str, optional
        Name of the plot to write, used as a prefix for plot sequences. Defaults
        to the recipe name.
    sequence_coordinate: str, optional
        Coordinate about which to make a plot sequence. Defaults to ``"time"``.
        This coordinate must exist in the cube and will be used for the time
        slider.
    stamp_coordinate: str, optional
        Coordinate about which to plot postage stamp plots. Defaults to
        ``"realization"``.
    single_plot: bool, optional
        If True, all postage stamp plots will be plotted in a single plot. If
        False, each postage stamp plot will be plotted separately. Is only valid
        if stamp_coordinate exists and has more than a single point.

    Returns
    -------
    iris.cube.Cube | iris.cube.CubeList
        The original Cube or CubeList (so further operations can be applied).
        Plotted data.

    Raises
    ------
    ValueError
        If the cube doesn't have the right dimensions.
    TypeError
        If the cube isn't a Cube or CubeList.
    """
    recipe_title = get_recipe_metadata().get("title", "Untitled")

    cubes = iter_maybe(cubes)

    # Ensure we have a name for the plot file.
    if filename is None:
        filename = slugify(recipe_title)

    # Internal plotting function.
    plotting_func = _plot_and_save_histogram_series

    num_models = _get_num_models(cubes)

    _validate_cube_shape(cubes, num_models)

    # If several histograms are plotted with time as sequence_coordinate for the
    # time slider option.
    for cube in cubes:
        try:
            cube.coord(sequence_coordinate)
        except iris.exceptions.CoordinateNotFoundError as err:
            raise ValueError(
                f"Cube must have a {sequence_coordinate} coordinate."
            ) from err

    # Get minimum and maximum from levels information.
    levels = None
    for cube in cubes:
        # First check if user-specified "auto" range variable.
        # This maintains the value of levels as None, so proceed.
        _, levels, _ = _colorbar_map_levels(cube, axis="y")
        if levels is None:
            break
        # If levels is changed, recheck to use the vmin,vmax or
        # levels-based ranges for histogram plots.
        _, levels, _ = _colorbar_map_levels(cube)
        logging.debug("levels: %s", levels)
        if levels is not None:
            vmin = min(levels)
            vmax = max(levels)
            logging.debug("Updated vmin, vmax: %s, %s", vmin, vmax)
            break

    if levels is None:
        vmin = min(cb.data.min() for cb in cubes)
        vmax = max(cb.data.max() for cb in cubes)

    # Make postage stamp plots if stamp_coordinate exists and has more than a
    # single point. If single_plot is True:
    # -- all postage stamp plots will be plotted in a single plot instead of
    # separate postage stamp plots.
    # -- model names (hidden in cube attrs) are ignored, that is stamp plots are
    # produced per single model only
    if num_models == 1:
        if (
            stamp_coordinate in [c.name() for c in cubes[0].coords()]
            and cubes[0].coord(stamp_coordinate).shape[0] > 1
        ):
            if single_plot:
                plotting_func = (
                    _plot_and_save_postage_stamps_in_single_plot_histogram_series
                )
            else:
                plotting_func = _plot_and_save_postage_stamp_histogram_series
        cube_iterables = cubes[0].slices_over(sequence_coordinate)
    else:
        all_points = sorted(
            set(
                itertools.chain.from_iterable(
                    cb.coord(sequence_coordinate).points for cb in cubes
                )
            )
        )
        all_slices = list(
            itertools.chain.from_iterable(
                cb.slices_over(sequence_coordinate) for cb in cubes
            )
        )
        # Matched slices (matched by seq coord point; it may happen that
        # evaluated models do not cover the same seq coord range, hence matching
        # necessary)
        cube_iterables = [
            iris.cube.CubeList(
                s for s in all_slices if s.coord(sequence_coordinate).points[0] == point
            )
            for point in all_points
        ]

    plot_index = []
    nplot = np.size(cube.coord(sequence_coordinate).points)
    # Create a plot for each value of the sequence coordinate. Allowing for
    # multiple cubes in a CubeList to be plotted in the same plot for similar
    # sequence values. Passing a CubeList into the internal plotting function
    # for similar values of the sequence coordinate. cube_slice can be an
    # iris.cube.Cube or an iris.cube.CubeList.
    for cube_slice in cube_iterables:
        single_cube = cube_slice
        if isinstance(cube_slice, iris.cube.CubeList):
            single_cube = cube_slice[0]

        # Use sequence value so multiple sequences can merge.
        sequence_value = single_cube.coord(sequence_coordinate).points[0]
        plot_filename = f"{filename.rsplit('.', 1)[0]}_{sequence_value}.png"
        coord = single_cube.coord(sequence_coordinate)
        # Format the coordinate value in a unit appropriate way.
        title = f"{recipe_title}\n [{coord.units.title(coord.points[0])}]"
        # Use sequence (e.g. time) bounds if plotting single non-sequence outputs
        if nplot == 1 and coord.has_bounds:
            if np.size(coord.bounds) > 1:
                title = f"{recipe_title}\n [{coord.units.title(coord.bounds[0][0])} to {coord.units.title(coord.bounds[0][1])}]"
        # Do the actual plotting.
        plotting_func(
            cube_slice,
            filename=plot_filename,
            stamp_coordinate=stamp_coordinate,
            title=title,
            vmin=vmin,
            vmax=vmax,
        )
        plot_index.append(plot_filename)

    # Add list of plots to plot metadata.
    complete_plot_index = _append_to_plot_index(plot_index)

    # Make a page to display the plots.
    _make_plot_html_page(complete_plot_index)

    return cubes
