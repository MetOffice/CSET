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

"""
Operators to produce various kinds of plots.
"""

import math
from pathlib import Path

import iris
import iris.cube
import iris.quickplot as qplt
import matplotlib.pyplot as plt


def spatial_contour_plot(cube: iris.cube.Cube, file_path: Path, **kwargs) -> Path:
    """
    Plots a spatial variable onto a map.

    Parameters
    ----------
    cube: Cube
        An iris cube of the data to plot. It should be 2 dimensional (lat and lon).
    file_path: pathlike
        The path of the plot to write.

    Returns
    -------
    Path
        The path of the resultant plot.

    Raises
    ------
    ValueError
        If the cube doesn't have the right dimensions.
    """
    qplt.contourf(cube)
    file_path = Path(file_path).with_suffix(".svg")
    plt.savefig(file_path)
    return file_path


def postage_stamp_contour_plot(cube: iris.cube.Cube, file_path: Path, **kwargs) -> Path:
    """
    Plots postage stamp contour plots from an ensemble.

    Parameters
    ----------
    cube: Cube
        Iris cube of data to be plotted. It must have a realization coordinate.
    file_path: pathlike
        The path of the plot to write.

    Returns
    -------
    Path
        The path of the resultant plot.

    Raises
    ------
    ValueError
        If the cube doesn't have the right dimensions.
    """

    if not cube.coord("realization"):
        raise ValueError("Cube must have a realization dimension.")

    # Use the smallest square grid that will fit the members.
    grid_size = int(math.ceil(math.sqrt(len(cube.coord("realization").points))))
    plt.figure(figsize=(10, 10))
    for member in cube.slices(["latitude", "longitude"]):
        plt.subplot(grid_size, grid_size, member.coord("realization").points[0])
        plot = qplt.contourf(member)
        plt.axis("off")

    # Make an axes to put the shared colorbar in.
    colorbar_axes = plt.gcf().add_axes([0.15, 0.07, 0.7, 0.03])
    colorbar = plt.colorbar(plot, colorbar_axes, orientation="horizontal")
    colorbar.set_label(f"{cube.name()} / {cube.units}")
    file_path = Path(file_path).with_suffix(".svg")
    plt.savefig(file_path)
