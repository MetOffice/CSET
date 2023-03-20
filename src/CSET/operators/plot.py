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
from iris.cube import CubeList


def spacial_plot_global(
    cube: CubeList, field: str, filename: Path, overwrite: bool = False, **kwargs
) -> Path:
    """
    Plots a spacial variable onto a global map.

    Parameters
    ----------
    cube: Cube
        An iris cube of the data to plot.

    field: str
        The variable to plot.

    filename: pathlike
        The path of the plot to write.

    overwrite: bool, default False
        Whether to overwrite already existing files.

    Returns
    -------
    Path
        The path of the resultant plot.

    Raises
    ------
    FileExistsError
        If the file already exists and `overwrite` is False

    ValueError
        If `field` is not in `cube`.
    """
    pass
