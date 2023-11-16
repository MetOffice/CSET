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

import logging
import math
from pathlib import Path
from typing import Union

import iris
import iris.cube
import iris.exceptions
import iris.plot as iplt
import iris.quickplot as qplt
import matplotlib.pyplot as plt


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


def spatial_contour_plot(
    cube: iris.cube.Cube, filename: Path, **kwargs
) -> iris.cube.Cube:
    """Plot a spatial variable onto a map.

    Parameters
    ----------
    cube: Cube
        An iris cube of the data to plot. It should be 2 dimensional (lat and lon).
    filename: pathlike
        The path of the plot to write.

    Returns
    -------
    Cube
        The inputted cube (so further operations can be applied)

    Raises
    ------
    ValueError
        If the cube doesn't have the right dimensions.
    TypeError
        If cube isn't a Cube.
    """
    cube = _check_single_cube(cube)
    qplt.contourf(cube)
    filename = Path(filename).with_suffix(".svg")
    plt.savefig(filename)
    logging.info("Saved contour plot to %s", filename)
    return cube


def postage_stamp_contour_plot(
    cube: iris.cube.Cube, filename: Path, coordinate: str = "realization", **kwargs
) -> iris.cube.Cube:
    """Plot postage stamp contour plots from an ensemble.

    Parameters
    ----------
    cube: Cube
        Iris cube of data to be plotted. It must have a realization coordinate.
    filename: pathlike
        The path of the plot to write.
    coordinate: str
        The coordinate that becomes different plots. Defaults to "realization".

    Returns
    -------
    Cube
        The inputted cube (so further operations can be applied)

    Raises
    ------
    ValueError
        If the cube doesn't have the right dimensions.
    TypeError
        If cube isn't a Cube.
    """
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

    filename = Path(filename).with_suffix(".svg")
    plt.savefig(filename)
    logging.info("Saved contour postage stamp plot to %s", filename)

    return cube


def time_series_contour_plot(
    cube: iris.cube.Cube, filename: Path, **kwargs
) -> iris.cube.Cube:
    """Plot a spatial variable for all time values.

    The files are named sequentially, e.g. 1.svg, 2.svg, ...

    Parameters
    ----------
    cube: Cube
        An iris cube of the data to plot. It should be 2 dimensional (lat and lon).

    Returns
    -------
    Cube
        The inputted cube (so further operations can be applied)

    Raises
    ------
    ValueError
        If the cube doesn't have the right dimensions.
    TypeError
        If cube isn't a Cube.
    """
    raise NotImplementedError
