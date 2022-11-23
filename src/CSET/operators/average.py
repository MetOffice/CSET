"""
Operators to calculate various kinds of averages.
"""

from iris.cube import Cube
from datetime import datetime


def time_mean(
    cube: Cube, field: str, start_time: datetime = None, end_time: datetime = None
) -> Cube:
    """
    Averages a field over the time period specified.

    Parameters
    ----------
    cube: Cube
        An iris cube of the data to average.

    field: str
        The variable to average.

    start_time: datetime, optional
        The time to start averaging from. If None averages from the earliest
        instance of the data.

    end_time: datetime, optional
        The time to average until. If None averages until the latest instance of
        the data.

    Returns
    -------
    Cube
        A cube containing the averaged field.

    Raises
    ------
    IndexError
        If the cube does not contain `field`.

    Notes
    -----
    Not yet implemented.
    """
    pass
