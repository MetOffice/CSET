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

from pathlib import Path
import iris
import iris.cube
import iris.quickplot as qplt
import matplotlib.pyplot as plt


def spatial_contour_plot(cube: iris.cube.Cube, file_path: Path) -> Path:
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
