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
from pathlib import Path
from typing import Iterable, Union

import iris
import iris.cube
import iris.exceptions
import iris.plot as iplt
import matplotlib as mpl
import matplotlib.pyplot as plt
import simple_template
from markdown_it import MarkdownIt

from CSET._common import get_recipe_metadata, slugify


def _make_plot_html_page(plots: Union[str, Iterable]):
    """Create a HTML page to display a plot image."""
    meta = get_recipe_metadata()
    title = meta.get("title", "Untitled")
    description = MarkdownIt().render(meta.get("description", "*No description.*"))
    # Wrap in a list if a single plot has been given for consistent usage.
    if not isinstance(plots, Iterable):
        plots = [plots]

    # Importlib behaviour changed in 3.12 to avoid circular dependencies.
    if sys.version_info.minor >= 12:
        operator_files = importlib.resources.files()
    else:
        import CSET.operators

        operator_files = importlib.resources.files(CSET.operators)
    template_file = operator_files.joinpath("_plot_page_template.html")
    variables = {
        "title": title,
        "description": description,
        "initial_plot": plots[0],
        "plots": plots,
        "title_slug": slugify(title),
    }
    html = simple_template.render_file(template_file, **variables)
    with open("index.html", "wt", encoding="UTF-8") as fp:
        fp.write(html)


def _check_single_cube(
    cube: Union[iris.cube.Cube, iris.cube.CubeList]
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


def _plot_and_save_contour_plot(cube: iris.cube.Cube, filename: str, title: str):
    """Plot and save a contour plot.

    Parameters
    ----------
    cube: Cube
        2 dimensional (lat and lon) Cube of the data to plot.
    filename: str
        Path of the plot to write.
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


def spatial_contour_plot(
    cube: iris.cube.Cube,
    filename: str = None,
    sequence_coordinate: str = None,
    **kwargs,
) -> iris.cube.Cube:
    """Plot a spatial variable onto a map. Optionally plot a sequence.

    Parameters
    ----------
    cube: Cube
        Iris cube of the data to plot. It should either be 2 dimensional (lat
        and lon), or also have a third dimension and specify a sequence
        coordinate.
    filename: str, optional
        Name of the plot to write, used as a prefix for plot sequences. Defaults
        to the recipe name.
    sequence_coordinate: str, optional
        Coordinate about which to make a plot sequence. This coordinate must
        exist in the cube.

    Returns
    -------
    Cube
        The original cube (so further operations can be applied).

    Raises
    ------
    ValueError
        If the cube doesn't have the right dimensions.
    TypeError
        If cube isn't a Cube.
    """
    title = get_recipe_metadata().get("title", "Untitled")
    cube = _check_single_cube(cube)
    if filename is None:
        filename = slugify(title)

    # Single plot.
    if sequence_coordinate is None:
        # Cube should be 2 dimensional.
        plot_filename = Path(filename).with_suffix(".png")
        _plot_and_save_contour_plot(cube, plot_filename, title)
        _make_plot_html_page(plot_filename)
    # Plot sequence.
    else:
        # Cube should be 3 dimensional.
        padding_zeros = len(str(cube.coord(sequence_coordinate).shape[0]))
        plot_number = 1
        plot_index = []
        for cube_slice in cube.slices_over(sequence_coordinate):
            plot_filename = (
                f"{filename.rsplit('.', 1)[0]}_{plot_number:0{padding_zeros}}.png"
            )
            _plot_and_save_contour_plot(cube_slice, plot_filename, title)
            plot_index.append(plot_filename)
            plot_number += 1
        _make_plot_html_page(plot_index)
        with open("meta.json", "r+t", encoding="UTF-8") as fp:
            fcntl.flock(fp, fcntl.LOCK_EX)
            fp.seek(0)
            meta = json.load(fp)
            meta["plots"] = plot_index
            fp.seek(0)
            fp.truncate()
            json.dump(meta, fp)

    return cube


def postage_stamp_contour_plot(
    cube: iris.cube.Cube,
    filename: Path = None,
    coordinate: str = "realization",
    **kwargs,
) -> iris.cube.Cube:
    """Plot postage stamp contour plots from an ensemble.

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
    if filename is None:
        filename = slugify(get_recipe_metadata().get("title", "Untitled"))
    filename = Path(filename).with_suffix(".png")

    # Validate input is in the right form.
    cube = _check_single_cube(cube)
    try:
        cube.coord(coordinate)
    except iris.exceptions.CoordinateNotFoundError as err:
        raise ValueError(f"Cube must have a {coordinate} dimension.") from err

    # Use the smallest square grid that will fit the members.
    grid_size = int(math.ceil(math.sqrt(len(cube.coord(coordinate).points))))

    plt.figure(figsize=(10, 10))
    subplot = 1
    for member in cube.slices_over(coordinate):
        plt.subplot(grid_size, grid_size, subplot)
        plot = iplt.contourf(member)
        plt.title(f"Member #{member.coord(coordinate).points[0]}")
        plt.axis("off")
        plt.gca().coastlines()
        subplot += 1

    # Make an axes to put the shared colorbar in.
    colorbar_axes = plt.gcf().add_axes([0.15, 0.07, 0.7, 0.03])
    colorbar = plt.colorbar(plot, colorbar_axes, orientation="horizontal")
    colorbar.set_label(f"{cube.name()} / {cube.units}")

    plt.savefig(filename, bbox_inches="tight", dpi=150)
    logging.info("Saved contour postage stamp plot to %s", filename)
    _make_plot_html_page(filename)
    return cube
