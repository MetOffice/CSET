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

"""Operators to perform various kind of collapse on either 1 or 2 dimensions."""

from typing import Union

import iris
import iris.analysis
import iris.cube


def collapse(
    cube: iris.cube.Cube,
    coordinate: Union[str, list[str]],
    method: str,
    additional_percent: float = None,
    **kwargs,
) -> iris.cube.Cube:
    """Collapse coordinate(s) of a cube.

    Collapses similar (stash) fields in a cube into a cube collapsing around the
    specified coordinate(s) and method. This could be a (weighted) mean or
    percentile.

    Arguments
    ---------
    cube: iris.cube.Cube
         Cube to collapse and iterate over one dimension
    coordinate: str | list[str]
         Coordinate(s) to collapse over e.g. 'time', 'longitude', 'latitude',
         'model_level_number', 'realization'. A list of multiple coordinates can
         be given.
    method: str
         Type of collapse i.e. method: 'MEAN', 'MAX', 'MIN', 'MEDIAN',
         'PERCENTILE' getattr creates iris.analysis.MEAN, etc For PERCENTILE
         YAML file requires i.e. method: 'PERCENTILE' additional_percent: 90

    Returns
    -------
    cube: iris.cube.Cube
         Single variable but several methods of aggregation

    Raises
    ------
    ValueError
        If additional_percent wasn't supplied while using PERCENTILE method.
    """
    if method == "PERCENTILE":
        if not additional_percent:
            raise ValueError("Must specify additional_percent")
        collapsed_cube = cube.collapsed(
            coordinate, iris.analysis.PERCENTILE, percent=additional_percent
        )
        return collapsed_cube
    collapsed_cube = cube.collapsed(coordinate, getattr(iris.analysis, method))
    return collapsed_cube


# TODO
# Collapse function that calculates means, medians etc across members of an
# ensemble or stratified groups. Need to allow collapse over realisation
# dimension for fixed time. Hence will require reading in of CubeList
