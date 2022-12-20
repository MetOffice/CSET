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
Operators to calculate various kinds of averages.
"""

from datetime import datetime
from iris.cube import CubeList


def time_mean(
    cube: CubeList,
    field: str,
    start_time: datetime = None,
    end_time: datetime = None,
) -> CubeList:
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
