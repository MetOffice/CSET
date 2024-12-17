# © Crown copyright, Met Office (2022-2024) and CSET contributors.
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
import json
import logging
import math
import sys
from typing import Literal

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
from CSET.operators._utils import get_cube_yxcoordname, is_transect

# Use a non-interactive plotting backend.
mpl.use("agg")

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
def _load_colorbar_map() -> dict:
    """Load the colorbar definitions from a file.

    This is a separate function to make it cacheable.
    """
    # Grab the colorbar file from the recipe global metadata.
    try:
        colorbar_file = get_recipe_metadata()["style_file_path"]
        logging.debug("Colour bar file: %s", colorbar_file)
        with open(colorbar_file, "rt", encoding="UTF-8") as fp:
            colorbar = json.load(fp)
    except (FileNotFoundError, KeyError):
        logging.info("Colorbar file does not exist. Using default values.")
        operator_files = _py312_importlib_resources_files_shim()
        colorbar_def_file = operator_files.joinpath("_colorbar_definition.json")
        with open(colorbar_def_file, "rt", encoding="UTF-8") as fp:
            colorbar = json.load(fp)
    return colorbar


def _colorbar_map_levels(varname: str, **kwargs):
    """Specify the color map and levels.

    For the given variable name, from a colorbar dictionary file.

    Parameters
    ----------
    colorbar_file: str
        Filename of the colorbar dictionary to read.
    varname: str
        Variable name to extract from the dictionary

    Returns
    -------
    cmap:
        Matplotlib colormap.
    levels:
        List of levels to use for plotting. For continuous plots the min and max
        should be taken as the range.
    norm:
        BoundryNorm information.
    """
    colorbar = _load_colorbar_map()

    # Get the colormap for this variable.
    try:
        cmap = colorbar[varname]["cmap"]
        logging.debug("From colorbar dictionary: Using cmap")
    except KeyError:
        cmap = mpl.colormaps["viridis"]

    # Get the colorbar levels for this variable.
    try:
        levels = colorbar[varname]["levels"]
        actual_cmap = mpl.cm.get_cmap(cmap)
        norm = mpl.colors.BoundaryNorm(levels, ncolors=actual_cmap.N)
        logging.debug("From colorbar dictionary: Using levels")
    except KeyError:
        try:
            # Get the range for this variable.
            vmin, vmax = colorbar[varname]["min"], colorbar[varname]["max"]
            logging.debug("From colorbar dictionary: Using min and max")
            # Calculate levels from range.
            levels = np.linspace(vmin, vmax, 20)
            norm = None
        except KeyError:
            levels = None
            norm = None

    return cmap, levels, norm


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
    cmap, levels, norm = _colorbar_map_levels(cube.name())

    if method == "contourf":
        # Filled contour plot of the field.
        plot = iplt.contourf(cube, cmap=cmap, levels=levels, norm=norm)
    elif method == "pcolormesh":
        try:
            vmin = min(levels)
            vmax = max(levels)
        except TypeError:
            vmin, vmax = None, None
        # pcolormesh plot of the field.
        plot = iplt.pcolormesh(cube, cmap=cmap, norm=norm, vmin=vmin, vmax=vmax)
    else:
        raise ValueError(f"Unknown plotting method: {method}")

    # Using pyplot interface here as we need iris to generate a cartopy GeoAxes.
    axes = plt.gca()

    # Add coastlines if cube contains x and y map coordinates.
    # If is spatial map, fix extent to keep plot tight.
    try:
        lataxis, lonaxis = get_cube_yxcoordname(cube)
        axes.coastlines(resolution="10m")
        axes.set_extent(
            [
                np.min(cube.coord(lonaxis).points),
                np.max(cube.coord(lonaxis).points),
                np.min(cube.coord(lataxis).points),
                np.max(cube.coord(lataxis).points),
            ]
        )
    except ValueError:
        # Skip if no x and y map coordinates.
        pass

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
            f'{title}\n'
            f'Start Lat: {cube.attributes["transect_coords"].split("_")[0]}'
            f' Start Lon: {cube.attributes["transect_coords"].split("_")[1]}'
            f' End Lat: {cube.attributes["transect_coords"].split("_")[2]}'
            f' End Lon: {cube.attributes["transect_coords"].split("_")[3]}',
            fontsize=16,
        )

    else:
        # Add title.
        axes.set_title(title, fontsize=16)

    # Add watermark with min/max/mean. Currently not user toggable.
    # In the bbox dictionary, fc and ec are hex colour codes for grey shade.
    axes.annotate(
        f"Min: {np.min(cube.data):g} Max: {np.max(cube.data):g} Mean: {np.mean(cube.data):g}",
        xy=(1, 0),
        xycoords="axes fraction",
        xytext=(-5, 5),
        textcoords="offset points",
        ha="right",
        va="bottom",
        size=11,
        bbox=dict(boxstyle="round", fc="#cccccc", ec="#808080", alpha=0.9),
    )

    # Add colour bar.
    cbar = fig.colorbar(plot)
    cbar.set_label(label=f"{cube.name()} ({cube.units})", size=20)

    # Save plot.
    fig.savefig(filename, bbox_inches="tight", dpi=_get_plot_resolution())
    logging.info("Saved contour plot to %s", filename)
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
    cmap, levels, norm = _colorbar_map_levels(cube.name())

    # Make a subplot for each member.
    for member, subplot in zip(
        cube.slices_over(stamp_coordinate), range(1, grid_size**2 + 1), strict=False
    ):
        # Implicit interface is much easier here, due to needing to have the
        # cartopy GeoAxes generated.
        plt.subplot(grid_size, grid_size, subplot)
        if method == "contourf":
            # Filled contour plot of the field.
            plot = iplt.contourf(member, cmap=cmap, levels=levels, norm=norm)
        elif method == "pcolormesh":
            try:
                vmin = min(levels)
                vmax = max(levels)
            except TypeError:
                vmin, vmax = None, None
            # pcolormesh plot of the field.
            plot = iplt.pcolormesh(member, cmap=cmap, norm=norm, vmin=vmin, vmax=vmax)
        else:
            raise ValueError(f"Unknown plotting method: {method}")
        ax = plt.gca()
        ax.set_title(f"Member #{member.coord(stamp_coordinate).points[0]}")
        ax.set_axis_off()

        # Add coastlines if cube contains x and y map coordinates.
        # If is spatial map, fix extent to keep plot tight.
        try:
            lataxis, lonaxis = get_cube_yxcoordname(cube)
            ax.coastlines(resolution="10m")
            ax.set_extent(
                [
                    np.min(cube.coord(lonaxis).points),
                    np.max(cube.coord(lonaxis).points),
                    np.min(cube.coord(lataxis).points),
                    np.max(cube.coord(lataxis).points),
                ]
            )
        except ValueError:
            # Skip if no x and y map coordinates.
            pass

    # Put the shared colorbar in its own axes.
    colorbar_axes = fig.add_axes([0.15, 0.07, 0.7, 0.03])
    colorbar = fig.colorbar(plot, colorbar_axes, orientation="horizontal")
    colorbar.set_label(f"{cube.name()} / {cube.units}")

    # Overall figure title.
    fig.suptitle(title)

    fig.savefig(filename, bbox_inches="tight", dpi=_get_plot_resolution())
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
    fig = plt.figure(figsize=(10, 10), facecolor="w", edgecolor="k")
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
    fig.savefig(filename, bbox_inches="tight", dpi=_get_plot_resolution())
    logging.info("Saved line plot to %s", filename)
    plt.close(fig)


def _plot_and_save_vertical_line_series(
    cube: iris.cube.Cube,
    coord: iris.coords.Coord,
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
    cube: Cube
        1 dimensional Cube of the data to plot on x-axis.
    coord: Coord
        Coordinate to plot on y-axis.
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
    iplt.plot(cube, coord, "o-")
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
            "50",
            "30",
            "20",
            "10",
        ]
        y_ticks = [1000, 850, 700, 500, 300, 200, 100, 50, 30, 20, 10]

        # Set y-axis limits and ticks.
        ax.set_ylim(1100, 100)

    # Test if series_coordinate is model level data. The UM data uses
    # model_level_number and lfric uses full_levels as coordinate.
    elif series_coordinate in ("model_level_number", "full_levels", "half_levels"):
        # Define y-ticks and labels for vertical axis.
        y_ticks = cube.coord(series_coordinate).points
        y_tick_labels = [str(int(i)) for i in y_ticks]
        ax.set_ylim(min(y_ticks), max(y_ticks))

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
    ax.ticklabel_format(axis="x")
    ax.tick_params(axis="y")
    ax.autoscale()

    # Save plot.
    fig.savefig(filename, bbox_inches="tight", dpi=_get_plot_resolution())
    logging.info("Saved line plot to %s", filename)
    plt.close(fig)


def _plot_and_save_scatter_plot(
    cube_x: iris.cube.Cube,
    cube_y: iris.cube.Cube,
    filename: str,
    title: str,
    one_to_one: bool,
    **kwargs,
):
    """Plot and save a 1D scatter plot.

    Parameters
    ----------
    cube_x: Cube
        1 dimensional Cube of the data to plot on x-axis.
    cube_y: Cube
        1 dimensional Cube of the data to plot on y-axis.
    filename: str
        Filename of the plot to write.
    title: str
        Plot title.
    one_to_one: bool
        Whether a 1:1 line is plotted.
    """
    fig = plt.figure(figsize=(10, 10), facecolor="w", edgecolor="k")
    iplt.scatter(cube_x, cube_y)
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
    ax.set(
        xlabel=f"{cube_x.name()} / {cube_x.units}",
        ylabel=f"{cube_y.name()} / {cube_y.units}",
        title=title,
    )
    ax.ticklabel_format(axis="y", useOffset=False)
    ax.tick_params(axis="x", labelrotation=15)
    ax.autoscale()

    # Save plot.
    fig.savefig(filename, bbox_inches="tight", dpi=_get_plot_resolution())
    logging.info("Saved scatter plot to %s", filename)
    plt.close(fig)


def _plot_and_save_histogram_series(
    cube: iris.cube.Cube,
    filename: str,
    title: str,
    vmin: float,
    vmax: float,
    histtype: str = "step",
    **kwargs,
):
    """Plot and save a histogram series.

    Parameters
    ----------
    cube: Cube
        2 dimensional Cube of the data to plot as histogram.
        Plotting options are fixed:
        density=True, histtype='step',stacked=True to ensure that
        a probability density is plotted using matplotlib.pyplot.hist
        to plot the probability density so that the area under
        the histogram integrates to 1.
        stacked is set to True so the sum of the histograms is
        normalized to 1.
        ax.autoscale is switched off and the ylim range
        is preset as (0,1) to make figures comparable.
    filename: str
        Filename of the plot to write.
    title: str
        Plot title.
    vmin: float
        minimum for colourbar
    vmax: float
        maximum for colourbar
    histtype: str
        The type of histogram to plot. Options are "step" for a line
        histogram or "barstacked", "stepfilled". "Step" is the default option,
        but can be changed in the rose-suite.conf configuration.
    """
    fig = plt.figure(figsize=(10, 10), facecolor="w", edgecolor="k")
    # Reshape cube data into a single array to allow for a single histogram.
    # Otherwise we plot xdim histograms stacked.
    cube_data_1d = (cube.data).flatten()
    plt.hist(cube_data_1d, density=True, histtype=histtype, stacked=True)
    ax = plt.gca()

    # Add some labels and tweak the style.
    ax.set(
        title=title,
        xlabel=f"{cube.name()} / {cube.units}",
        ylabel="normalised probability density",
        ylim=(0, 1),
        xlim=(vmin, vmax),
    )

    ax.grid(linestyle="--", color="black", linewidth=0.5)

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
    histtype: str,
    **kwargs,
):
    """Plot and save postage (ensemble members) stamps for a histogram series.

    Parameters
    ----------
    cube: Cube
        2 dimensional Cube of the data to plot as histogram.
        Plotting options are fixed:
        density=True, histtype='bar', stacked=True to ensure that
        a probability density is plotted using matplotlib.pyplot.hist
        to plot the probability density so that the area under
        the histogram integrates to 1.
        stacked is set to True so the sum of the histograms is
        normalized to 1.
        ax.autoscale is switched off and the ylim range
        is preset as (0,1) to make figures comparable.
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
    histtype: str
        The type of histogram to plot. Options are "step" for a line
        histogram or "barstacked", "stepfilled". "Step" is the default option,
        but can be changed in the rose-suite.conf configuration.

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
        plt.hist(member_data_1d, density=True, histtype=histtype, stacked=True)
        ax = plt.gca()
        ax.set_title(f"Member #{member.coord(stamp_coordinate).points[0]}")
        ax.set_xlim(vmin, vmax)

    # Overall figure title.
    fig.suptitle(title)

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
    histtype: str = "step",
    **kwargs,
):
    fig, ax = plt.subplots(figsize=(10, 10), facecolor="w", edgecolor="k")
    ax.set_title(title)
    ax.set_xlim(vmin, vmax)
    ax.set_xlabel(f"{cube.name()} / {cube.units}")
    ax.set_ylabel("normalised probability density")
    # Loop over all slices along the stamp_coordinate
    for member in cube.slices_over(stamp_coordinate):
        # Flatten the member data to 1D
        member_data_1d = member.data.flatten()
        # Plot the histogram using plt.hist
        plt.hist(
            member_data_1d,
            density=True,
            histtype=histtype,
            stacked=True,
            label=f"Member #{member.coord(stamp_coordinate).points[0]}",
        )

    # Add a legend
    ax.legend()

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
    for cube_slice in cube.slices_over(sequence_coordinate):
        # Use sequence value so multiple sequences can merge.
        sequence_value = cube_slice.coord(sequence_coordinate).points[0]
        plot_filename = f"{filename.rsplit('.', 1)[0]}_{sequence_value}.png"
        coord = cube_slice.coord(sequence_coordinate)
        # Format the coordinate value in a unit appropriate way.
        title = f"{recipe_title}\n{coord.units.title(coord.points[0])}"
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
    series_coordinate: str = "model_level_number",
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
        Coordinate to plot on the y-axis. Can be ``pressure`` or
        ``model_level_number`` for UM, or ``full_levels`` or ``half_levels``
        for LFRic. Defaults to ``model_level_number``.
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

    try:
        if cube.ndim > 1:
            cube.coord(sequence_coordinate)
    except iris.exceptions.CoordinateNotFoundError as err:
        raise ValueError(
            f"Cube must have a {sequence_coordinate} coordinate or be 1D."
        ) from err

    # Ensure we have a name for the plot file.
    recipe_title = get_recipe_metadata().get("title", "Untitled")
    if filename is None:
        filename = slugify(recipe_title)

    # Set the lower and upper limit for the x-axis to ensure all plots have same
    # range. This needs to read the whole cube over the range of the sequence
    # and if applicable postage stamp coordinate.
    vmin = np.floor(cube.data.min())
    vmax = np.ceil(cube.data.max())

    # Create a plot for each value of the sequence coordinate.
    plot_index = []
    for cube_slice in cube.slices_over(sequence_coordinate):
        # Use sequence value so multiple sequences can merge.
        seq_coord = cube_slice.coord(sequence_coordinate)
        sequence_value = seq_coord.points[0]
        plot_filename = f"{filename.rsplit('.', 1)[0]}_{sequence_value}.png"
        # Format the coordinate value in a unit appropriate way.
        title = f"{recipe_title}\n{seq_coord.units.title(sequence_value)}"
        # Do the actual plotting.
        _plot_and_save_vertical_line_series(
            cube_slice,
            coord,
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

    return cube


def scatter_plot(
    cube_x: iris.cube.Cube,
    cube_y: iris.cube.Cube,
    filename: str = None,
    one_to_one: bool = True,
    **kwargs,
) -> iris.cube.CubeList:
    """Plot a scatter plot between two variables.

    Both cubes must be 1D.

    Parameters
    ----------
    cube_x: Cube
        1 dimensional Cube of the data to plot on y-axis.
    cube_y: Cube
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
    # Check cubes are correct shape.
    cube_x = _check_single_cube(cube_x)
    cube_y = _check_single_cube(cube_y)

    if cube_x.ndim > 1:
        raise ValueError("cube_x must be 1D.")
    if cube_y.ndim > 1:
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


def plot_histogram_series(
    cube: iris.cube.Cube,
    filename: str = None,
    sequence_coordinate: str = "time",
    stamp_coordinate: str = "realization",
    single_plot: bool = False,
    histtype: str = "step",
    **kwargs,
) -> iris.cube.Cube:
    """Plot a histogram plot for each vertical level provided.

    A histogram plot can be plotted, but if the sequence_coordinate (i.e. time)
    is present then a sequence of plots will be produced using the time slider
    functionality to scroll through histograms against time. If a
    stamp_coordinate is present then postage stamp plots will be produced. If
    stamp_coordinate and single_plot is True, all postage stamp plots will be
    plotted in a single plot instead of separate postage stamp plots.

    Parameters
    ----------
    cube: Cube
        Iris cube of the data to plot. It should have a single dimension other
        than the stamp coordinate.
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
    histtype: str, optional
        The type of histogram to plot. Options are "step" for a line histogram
        or "barstacked", "stepfilled". "Step" is the default option, but can be
        changed in the rose-suite.conf configuration.

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

    # Internal plotting function.
    plotting_func = _plot_and_save_histogram_series

    # Make postage stamp plots if stamp_coordinate exists and has more than a
    # single point. If single_plot is True, all postage stamp plots will be
    # plotted in a single plot instead of separate postage stamp plots.
    try:
        if cube.coord(stamp_coordinate).shape[0] > 1:
            if single_plot:
                plotting_func = (
                    _plot_and_save_postage_stamps_in_single_plot_histogram_series
                )
            else:
                plotting_func = _plot_and_save_postage_stamp_histogram_series
    except iris.exceptions.CoordinateNotFoundError:
        pass

    # If several histograms are plotted with time as sequence_coordinate for the
    # time slider option.
    try:
        cube.coord(sequence_coordinate)
    except iris.exceptions.CoordinateNotFoundError as err:
        raise ValueError(f"Cube must have a {sequence_coordinate} coordinate.") from err

    # Set the lower and upper limit for the colorbar to ensure all plots have
    # same range. This needs to read the whole cube over the range of the
    # sequence and if applicable postage stamp coordinate.
    vmin = np.floor((cube.data.min()))
    vmax = np.ceil((cube.data.max()))

    # Create a plot for each value of the sequence coordinate.
    plot_index = []
    for cube_slice in cube.slices_over(sequence_coordinate):
        # Use sequence value so multiple sequences can merge.
        sequence_value = cube_slice.coord(sequence_coordinate).points[0]
        plot_filename = f"{filename.rsplit('.', 1)[0]}_{sequence_value}.png"
        coord = cube_slice.coord(sequence_coordinate)
        # Format the coordinate value in a unit appropriate way.
        title = f"{recipe_title}\n{coord.units.title(coord.points[0])}"
        # Do the actual plotting.
        plotting_func(
            cube_slice,
            plot_filename,
            stamp_coordinate=stamp_coordinate,
            title=title,
            vmin=vmin,
            vmax=vmax,
            histtype=histtype,
        )
        plot_index.append(plot_filename)

    # Add list of plots to plot metadata.
    complete_plot_index = _append_to_plot_index(plot_index)

    # Make a page to display the plots.
    _make_plot_html_page(complete_plot_index)

    return cube
