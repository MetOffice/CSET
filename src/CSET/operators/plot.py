"""
Operators to produce various kinds of plots.
"""

from pathlib import Path
from iris.cube import CubeList


def spacial_plot_global(
    cube: CubeList, field: str, filename: Path, overwrite: bool = False
) -> Path:
    """
    Plots a spacial variable onto a global map.

    Parameters
    ----------
    cube: Cube
        An iris cube of the data to plot.

    field: str
        The variable to plot.

    filename: Path or pathlike
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
