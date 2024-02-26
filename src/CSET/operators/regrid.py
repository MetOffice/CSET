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

"""Operators to regrid cubes."""

from datetime import datetime
from typing import Union

import iris
import iris.cube


def regrid_onto_cube(incube: iris.cube.Cube, targetcube: iris.cube.Cube, methodplaceholder,
                     **kwargs) -> iris.cube.Cube:
    """Regrid cube using another cube as a target.

    Parameters
    ----------
    incube: Cube
        An iris cube of the data to regrid. As a minimum, it needs to be 2D with a latitude,
        longitude coordinates.
    targetcube: Cube
        An iris cube of the data to regrid onto. It needs to be 2D with a latitude,
        longitude coordinate, though I think more dims are acceptable and are ignored.
    methodplaceholder: iris.analysis
        Method used to regrid onto, such as iris.analysis.Linear()

    Returns
    -------
    regriddedcube: Cube
        An iris cube of the data that has been regridded.
    """

    # TODO: Can iris recognise both 'latitude' and 'grid_latitude'? For cell stats there
    # was a function to identify x,y coordinate names.

    return incube.regrid(targetcube, methodplaceholder)


