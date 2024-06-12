# Copyright 2022 Met Office and contributors.
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
import importlib.resources
import json
import logging
import math
import sys
import warnings
from typing import Union

import iris
import iris.coords
import iris.cube
import iris.exceptions
import iris.plot as iplt
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from markdown_it import MarkdownIt

from CSET._common import get_recipe_metadata, render_file, slugify
from CSET.operators._utils import _is_transect, get_cube_yxcoordname

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
        fp.seek(0)
        fp.truncate()
        json.dump(meta, fp)
    return complete_plot_index


def _check_single_cube(
    cube: Union[iris.cube.Cube, iris.cube.CubeList],
) -> iris.cube.Cube:
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


def _make_plot_html_page(plots: list):
    """Create a HTML page to display a plot image."""
    # Debug check that plots actually contains some strings.
    assert isinstance(plots[0], str)

    # Load HTML template file.
    # Importlib behaviour changed in 3.12 to avoid circular dependencies.
    if sys.version_info.minor >= 12:
        operator_files = importlib.resources.files()
    else:
        import CSET.operators

        operator_files = importlib.resources.files(CSET.operators)
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


def _colorbar_map_levels(varname: str, **kwargs):
    """
    Specify the color map and levels.

    For the given variable name, from a colorbar dictionary file.

    Parameters
    ----------
    colorbar_file: str
        Filename of the colorbar dictionary to read.
    varname: str
        Variable name to extract from the dictionary

    """
    # Grab the colour bar file from the recipe global metadata. A non-existent
    # placeholder path is used if not found.
    colorbar_file = get_recipe_metadata().get(
        "style_file_path", "/non-existent/NO_FILE_SPECIFIED"
    )
    try:
        with open(colorbar_file, "rt", encoding="UTF-8") as fp:
            colorbar = json.load(fp)

        # Specify the colormap for this variable
        try:
            cmap = colorbar[varname]["cmap"]
            logging.debug("From color_bar dictionary: Using cmap")
        except KeyError:
            cmap = mpl.colormaps["viridis"]

        # Specify the colorbar levels for this variable
        try:
            levels = colorbar[varname]["levels"]

            actual_cmap = mpl.cm.get_cmap(cmap)

            norm = mpl.colors.BoundaryNorm(levels, ncolors=actual_cmap.N)
            logging.debug("From color_bar dictionary: Using levels")
        except KeyError:
            try:
                vmin, vmax = colorbar[varname]["min"], colorbar[varname]["max"]
                logging.debug("From color_bar dictionary: Using min and max")
                levels = np.linspace(vmin, vmax, 10)
                norm = None
            except KeyError:
                levels = None
                norm = None

    except FileNotFoundError:
        logging.debug("Colour bar file: %s", colorbar_file)
        logging.info("Colour bar file does not exist. Using default values.")
        levels = None
        norm = None
        cmap = mpl.colormaps["viridis"]

    return cmap, levels, norm


def _plot_and_save_contour_plot(
    cube: iris.cube.Cube,
    filename: str,
    title: str,
    **kwargs,
):
    """Plot and save a contour plot.

    Parameters
    ----------
    cube: Cube
        2 dimensional (lat and lon) Cube of the data to plot.
    filename: str
        Filename of the plot to write.
    title: str
        Plot title.

    """
    # Setup plot details, size, resolution, etc.
    fig = plt.figure(figsize=(15, 15), facecolor="w", edgecolor="k")

    # Specify the color bar
    cmap, levels, norm = _colorbar_map_levels(cube.name())

    # Filled contour plot of the field.
    contours = iplt.contourf(cube, cmap=cmap, levels=levels, norm=norm)

    # Using pyplot interface here as we need iris to generate a cartopy GeoAxes.
    axes = plt.gca()

    # Add coastlines if cube contains x and y map coordinates.
    try:
        get_cube_yxcoordname(cube)
        axes.coastlines(resolution="10m")
    except ValueError:
        pass

    # Check to see if transect, and if so, adjust y axis.
    if _is_transect(cube):
        if "pressure" in [coord.name() for coord in cube.coords()]:
            axes.invert_yaxis()
            axes.set_yscale("log")
            axes.set_ylim(
                np.max(cube.coord("pressure").points),
                np.min(cube.coord("pressure").points),
            )
        # If both model_level_number and level_height exists, iplt can construct
        # plot as a function of height above orography (NOT sea level).
        elif "model_level_number" in [
            coord.name() for coord in cube.coords()
        ] and "level_height" in [coord.name() for coord in cube.coords()]:
            axes.set_yscale("log")

    # Add title.
    axes.set_title(title, fontsize=16)

    # Add colour bar.
    cbar = fig.colorbar(contours)
    cbar.set_label(label=f"{cube.name()} ({cube.units})", size=20)

    # Save plot.
    fig.savefig(filename, bbox_inches="tight", dpi=150)
    logging.info("Saved contour plot to %s", filename)
    plt.close(fig)


def _plot_and_save_postage_stamp_contour_plot(
    cube: iris.cube.Cube,
    filename: str,
    stamp_coordinate: str,
    title: str,
    **kwargs,
):
    """Plot postage stamp contour plots from an ensemble.

    Parameters
    ----------
    cube: Cube
        Iris cube of data to be plotted. It must have the stamp coordinate.
    filename: str
        Filename of the plot to write.
    stamp_coordinate: str
        Coordinate that becomes different plots.

    Raises
    ------
    ValueError
        If the cube doesn't have the right dimensions.
    """
    # Use the smallest square grid that will fit the members.
    grid_size = int(math.ceil(math.sqrt(len(cube.coord(stamp_coordinate).points))))

    fig = plt.figure(figsize=(10, 10))

    # Specify the color bar
    cmap, levels, norm = _colorbar_map_levels(cube.name())

    # Make a subplot for each member.
    for member, subplot in zip(
        cube.slices_over(stamp_coordinate), range(1, grid_size**2 + 1), strict=False
    ):
        # Implicit interface is much easier here, due to needing to have the
        # cartopy GeoAxes generated.
        plt.subplot(grid_size, grid_size, subplot)
        plot = iplt.contourf(member, cmap=cmap, levels=levels, norm=norm)
        ax = plt.gca()
        ax.set_title(f"Member #{member.coord(stamp_coordinate).points[0]}")
        ax.set_axis_off()

        # Add coastlines if cube contains x and y map coordinates.
        try:
            get_cube_yxcoordname(cube)
            ax.coastlines(resolution="10m")
        except ValueError:
            pass

    # Put the shared colorbar in its own axes.
    colorbar_axes = fig.add_axes([0.15, 0.07, 0.7, 0.03])
    colorbar = fig.colorbar(plot, colorbar_axes, orientation="horizontal")
    colorbar.set_label(f"{cube.name()} / {cube.units}")

    # Overall figure title.
    fig.suptitle(title)

    fig.savefig(filename, bbox_inches="tight", dpi=150)
    logging.info("Saved contour postage stamp plot to %s", filename)
    plt.close(fig)


def _plot_and_save_line_series(
    cube: iris.cube.Cube, coord: iris.coords.Coord, filename: str, title: str, **kwargs
):
    """Plot and save a 1D line series.

    Parameters
    ----------
    cube: Cube
        1 dimensional Cube of the data to plot on y-axis.
    coord: Coord
        Coordinate to plot on x-axis.
    filename: str
        Filename of the plot to write.
    title: str
        Plot title.
    """
    fig = plt.figure(figsize=(8, 8), facecolor="w", edgecolor="k")
    iplt.plot(coord, cube, "o-")
    ax = plt.gca()

    # Add some labels and tweak the style.
    ax.set(
        xlabel=f"{coord.name()} / {coord.units}",
        ylabel=f"{cube.name()} / {cube.units}",
        title=title,
    )
    ax.ticklabel_format(axis="y", useOffset=False)
    ax.tick_params(axis="x", labelrotation=15)
    ax.autoscale()

    # Save plot.
    fig.savefig(filename, bbox_inches="tight", dpi=150)
    logging.info("Saved line plot to %s", filename)
    plt.close(fig)


def _plot_and_save_vertical_line_series(
    cube: iris.cube.Cube,
    coord: iris.coords.Coord,
    filename: str,
    title: str,
    vmin: float,
    vmax: float,
    **kwargs,
):
    """Plot and save a 1D line series in vertical.

    Parameters
    ----------
    cube: Cube
        1 dimensional Cube of the data to plot on x-axis.
    coord: Coord
        Coordinate to plot on y-axis.
    filename: str
        Filename of the plot to write.
    title: str
        Plot title.
    vmin: float
        Minimum value for the x-axis.
    vmax: float
        Maximum value for the x-axis.
    """
    # plot the vertical pressure axis using log scale
    fig = plt.figure(figsize=(8, 8), facecolor="w", edgecolor="k")
    iplt.plot(cube, coord, "o-")
    ax = plt.gca()
    ax.invert_yaxis()
    ax.set_yscale("log")

    # Define y-ticks and labels for pressure log axis
    y_tick_labels = [
        "1000",
        "850",
        "700",
        "500",
        "300",
        "200",
        "100",
        "50",
        "30",
        "20",
        "10",
    ]
    y_ticks = [1000, 850, 700, 500, 300, 200, 100, 50, 30, 20, 10]

    # Set y-axis limits and ticks
    ax.set_ylim(1100, 100)
    ax.set_yticks(y_ticks)
    ax.set_yticklabels(y_tick_labels)

    # set x-axis limits
    ax.set_xlim(vmin, vmax)

    # Add some labels and tweak the style.
    ax.set(
        ylabel=f"{coord.name()} / {coord.units}",
        xlabel=f"{cube.name()} / {cube.units}",
        title=title,
    )

    # Save plot.
    fig.savefig(filename, bbox_inches="tight", dpi=150)
    logging.info("Saved line plot to %s", filename)
    plt.close(fig)


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
    recipe_title = get_recipe_metadata().get("title", "Untitled")

    # Ensure we have a name for the plot file.
    if filename is None:
        filename = slugify(recipe_title)

    # Ensure we've got a single cube.
    cube = _check_single_cube(cube)

    # Make postage stamp plots if stamp_coordinate exists and has more than a
    # single point.
    plotting_func = _plot_and_save_contour_plot
    try:
        if cube.coord(stamp_coordinate).shape[0] > 1:
            plotting_func = _plot_and_save_postage_stamp_contour_plot
    except iris.exceptions.CoordinateNotFoundError:
        pass

    try:
        cube.coord(sequence_coordinate)
    except iris.exceptions.CoordinateNotFoundError as err:
        raise ValueError(f"Cube must have a {sequence_coordinate} coordinate.") from err

    # Create a plot for each value of the sequence coordinate.
    plot_index = []
    for cube_slice in cube.slices_over(sequence_coordinate):
        # Use sequence value so multiple sequences can merge.
        sequence_value = cube_slice.coord(sequence_coordinate).points[0]
        plot_filename = f"{filename.rsplit('.', 1)[0]}_{sequence_value}.png"
        coord = cube_slice.coord(sequence_coordinate)
        # Format the coordinate value in a unit appropriate way.
        title = f"{recipe_title} | {coord.units.title(coord.points[0])}"
        # Do the actual plotting.
        plotting_func(
            cube_slice,
            plot_filename,
            stamp_coordinate=stamp_coordinate,
            title=title,
        )
        plot_index.append(plot_filename)

    # Add list of plots to plot metadata.
    complete_plot_index = _append_to_plot_index(plot_index)

    # Make a page to display the plots.
    _make_plot_html_page(complete_plot_index)

    return cube


# Deprecated
def postage_stamp_contour_plot(
    cube: iris.cube.Cube,
    filename: str = None,
    coordinate: str = "realization",
    **kwargs,
) -> iris.cube.Cube:
    """Plot postage stamp contour plots from an ensemble.

    Depreciated. Use spatial_contour_plot with a stamp_coordinate argument
    instead.

    Parameters
    ----------
    cube: Cube
        Iris cube of data to be plotted. It must have a realization coordinate.
    filename: pathlike, optional
        The path of the plot to write. Defaults to the recipe name.
    coordinate: str
        The coordinate that becomes different plots. Defaults to "realization".

    Returns
    -------
    Cube
        The original cube (so further operations can be applied)

    Raises
    ------
    ValueError
        If the cube doesn't have the right dimensions.
    TypeError
        If cube isn't a Cube.
    """
    warnings.warn(
        "postage_stamp_contour_plot is depreciated. Use spatial_contour_plot with a stamp_coordinate argument instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    # Get suitable filename.
    if filename is None:
        filename = slugify(get_recipe_metadata().get("title", "Untitled"))
    if not filename.endswith(".png"):
        filename = filename + ".png"

    # Check cube is suitable.
    cube = _check_single_cube(cube)
    try:
        cube.coord(coordinate)
    except iris.exceptions.CoordinateNotFoundError as err:
        raise ValueError(f"Cube must have a {coordinate} coordinate.") from err

    _plot_and_save_postage_stamp_contour_plot(cube, filename, coordinate, title="")
    _make_plot_html_page([filename])
    return cube


# TODO: Expand function to handle ensemble data.
# line_coordinate: str, optional
#     Coordinate about which to plot multiple lines. Defaults to
#     ``"realization"``.
def plot_line_series(
    cube: iris.cube.Cube,
    filename: str = None,
    series_coordinate: str = "time",
    # line_coordinate: str = "realization",
    **kwargs,
) -> iris.cube.Cube:
    """Plot a line plot for the specified coordinate.

    The cube must be 1D.

    Parameters
    ----------
    cube: Cube
        Iris cube of the data to plot. It should have a single dimension.
    filename: str, optional
        Name of the plot to write, used as a prefix for plot sequences. Defaults
        to the recipe name.
    series_coordinate: str, optional
        Coordinate about which to make a series. Defaults to ``"time"``. This
        coordinate must exist in the cube.

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
    # Check cube is right shape.
    cube = _check_single_cube(cube)
    try:
        coord = cube.coord(series_coordinate)
    except iris.exceptions.CoordinateNotFoundError as err:
        raise ValueError(f"Cube must have a {series_coordinate} coordinate.") from err
    if cube.ndim > 1:
        raise ValueError("Cube must be 1D.")

    # Ensure we have a name for the plot file.
    title = get_recipe_metadata().get("title", "Untitled")
    if filename is None:
        filename = slugify(title)

    # Add file extension.
    plot_filename = f"{filename.rsplit('.', 1)[0]}.png"

    # Do the actual plotting.
    _plot_and_save_line_series(cube, coord, plot_filename, title)

    # Add list of plots to plot metadata.
    plot_index = _append_to_plot_index([plot_filename])

    # Make a page to display the plots.
    _make_plot_html_page(plot_index)

    return cube


def plot_vertical_line_series(
    cube: iris.cube.Cube,
    filename: str = None,
    series_coordinate: str = "pressure",
    sequence_coordinate: str = "time",
    # line_coordinate: str = "realization",
    **kwargs,
) -> iris.cube.Cube:
    """Plot a line plot against a type of vertical coordinate.

    A 1D line plot with y-axis as pressure coordinate can be plotted, but if the sequence_coordinate is present
    then a sequence of plots will be produced.

    The cube must be 1D.

    Parameters
    ----------
    cube: Cube
        Iris cube of the data to plot. It should have a single dimension.
    filename: str, optional
        Name of the plot to write, used as a prefix for plot sequences. Defaults
        to the recipe name.
    series_coordinate: str, optional
        Coordinate to plot on the y-axis. Defaults to ``pressure``.
        This coordinate must exist in the cube.
    sequence_coordinate: str, optional
        Coordinate about which to make a plot sequence. Defaults to ``"time"``.
        This coordinate must exist in the cube.

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
    # Ensure we've got a single cube.
    cube = _check_single_cube(cube)

    # Test if series coordinate i.e. pressure level exist for any cube with cube.ndim >=1.
    try:
        coord = cube.coord(series_coordinate)
    except iris.exceptions.CoordinateNotFoundError as err:
        raise ValueError(f"Cube must have a {series_coordinate} coordinate.") from err

    # If several individual vertical lines are plotted with time as sequence_coordinate
    # for the time slider option.
    try:
        cube.coord(sequence_coordinate)
    except iris.exceptions.CoordinateNotFoundError as err:
        raise ValueError(f"Cube must have a {sequence_coordinate} coordinate.") from err

    # Ensure we have a name for the plot file.
    recipe_title = get_recipe_metadata().get("title", "Untitled")
    if filename is None:
        filename = slugify(recipe_title)

    # Make vertical line plot
    plotting_func = _plot_and_save_vertical_line_series

    # set the lower and upper limit for the x-axis to ensure all plots
    # have same range. This needs to read the whole cube over the range of
    # the sequence and if applicable postage stamp coordinate.
    # This only works if the plotting is done in the collate section of a
    # recipe and not in the parallel section of a recipe.
    vmin = np.floor((cube.data.min()))
    vmax = np.ceil((cube.data.max()))

    # Create a plot for each value of the sequence coordinate.
    plot_index = []
    for cube_slice in cube.slices_over(sequence_coordinate):
        # Use sequence value so multiple sequences can merge.
        sequence_value = cube_slice.coord(sequence_coordinate).points[0]
        plot_filename = f"{filename.rsplit('.', 1)[0]}_{sequence_value}.png"
        coord = cube_slice.coord(series_coordinate)
        # Format the coordinate value in a unit appropriate way.
        title = f"{recipe_title} | {coord.units.title(coord.points[0])}"
        # Do the actual plotting.
        plotting_func(
            cube_slice,
            coord,
            plot_filename,
            title=title,
            vmin=vmin,
            vmax=vmax,
        )
        plot_index.append(plot_filename)

    # Add list of plots to plot metadata.
    complete_plot_index = _append_to_plot_index(plot_index)

    # Make a page to display the plots.
    _make_plot_html_page(complete_plot_index)

    return cube
