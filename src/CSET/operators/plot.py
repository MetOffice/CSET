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
import iris.cube
import iris.exceptions
import iris.plot as iplt
import matplotlib as mpl
import matplotlib.pyplot as plt
from markdown_it import MarkdownIt

from CSET._common import get_recipe_metadata, render_file, slugify


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


def _plot_and_save_contour_plot(
    cube: iris.cube.Cube, filename: str, title: str, **kwargs
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

    Raises
    ------
    ValueError
        If the cube doesn't have the right dimensions.
    """
    # Setup plot details, size, resolution, etc.
    fig = plt.figure(figsize=(15, 15), facecolor="w", edgecolor="k")

    cmap = mpl.colormaps["viridis"]

    # Filled contour plot of the field.
    iplt.contourf(cube, cmap=cmap)
    axes = fig.gca()

    # Add coastlines.
    axes.coastlines(resolution="10m")

    # Add title.
    plt.title(title, fontsize=16)

    # Add colour bar.
    cbar = plt.colorbar()
    cbar.set_label(label=f"{cube.name()} ({cube.units})", size=20)

    # Save plot.
    fig.savefig(filename, bbox_inches="tight", dpi=150)
    logging.info("Saved contour plot to %s", filename)


def _plot_and_save_postage_stamp_contour_plot(
    cube: iris.cube.Cube,
    filename: str,
    stamp_coordinate: str,
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

    plt.figure(figsize=(10, 10))
    # Make a subplot for each member.
    subplot = 1
    for member in cube.slices_over(stamp_coordinate):
        plt.subplot(grid_size, grid_size, subplot)
        plot = iplt.contourf(member)
        plt.title(f"Member #{member.coord(stamp_coordinate).points[0]}")
        plt.axis("off")
        plt.gca().coastlines()
        subplot += 1

    # Put the shared colorbar in its own axes.
    colorbar_axes = plt.gcf().add_axes([0.15, 0.07, 0.7, 0.03])
    colorbar = plt.colorbar(plot, colorbar_axes, orientation="horizontal")
    colorbar.set_label(f"{cube.name()} / {cube.units}")

    plt.savefig(filename, bbox_inches="tight", dpi=150)
    logging.info("Saved contour postage stamp plot to %s", filename)


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
        # TODO: Should this be an error, or should it just do the right thing?
        raise ValueError(f"Cube must have a {sequence_coordinate} coordinate.") from err

    # Create a plot for each value of the sequence coordinate.
    plot_index = []
    for cube_slice in cube.slices_over(sequence_coordinate):
        # Use sequence value so multiple sequences can merge.
        sequence_value = cube_slice.coord(sequence_coordinate).points[0]
        plot_filename = f"{filename.rsplit('.', 1)[0]}_{sequence_value}.png"
        coord = cube_slice.coord(sequence_coordinate)
        # Format the coordinate value in a unit appropriate way.
        title = coord.units.title(coord.points[0])
        # Do the actual plotting.
        plotting_func(
            cube_slice,
            plot_filename,
            stamp_coordinate=stamp_coordinate,
            title=title,
        )
        plot_index.append(plot_filename)

    # Add list of plots to plot metadata.
    # NOTE: It is not currently use for anything there. (2024-02-12)
    # TODO: Refactor this out into a common function.
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

    # Make a page to display the plots.
    _make_plot_html_page(complete_plot_index)

    return cube


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

    _plot_and_save_postage_stamp_contour_plot(cube, filename, coordinate)
    _make_plot_html_page([filename])
    return cube
