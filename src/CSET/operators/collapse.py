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
Operators to perform various kind of collapse on either 1 or 2 dimensions.
"""

import iris
import iris.cube
import iris.analysis


def collapse_1dim(
    cube: iris.cube.Cube, coordinate: str, method: str, **kwargs
) -> iris.cube.Cube:
    """
    Collapses similar (stash) fields in a cube into a cube collapsing around the specified coordinate and method.
    This could be a (weighted) mean or percentile.

    Arguments
    ---------
    cube: iris.cube.Cube
         Cube to collapse and iterate over one dimension
    coordinate: str
         Coordinate to collapse over i.e.
         'time', 'longitude', 'latitude','model_level_number'
    method: str
         Type of collapse i.e. method: 'MEAN', 'MAX', 'MIN', 'MEDIAN', 'PERCENTILE'
         getattr creates iris.analysis.MEAN, etc
         For PERCENTILE YAML file requires i.e.
         method: 'PERCENTILE'
         additional_percent: 90

    Returns
    -------
    cube: iris.cube.Cube
         Single variable but several methods of aggregation


    Raises
    ------
    ValueError
    If the constraint doesn't produce a single cube containing a field.
    """

    if method != "PERCENTILE":
        collapsed_cube = cube.collapsed(coordinate, getattr(iris.analysis, method))
    if method == "PERCENTILE":
        for num in kwargs.values():
            collapsed_cube = cube.collapsed(
                coordinate, getattr(iris.analysis, method), percent=num
            )

    return collapsed_cube


def collapse_cube_2dim(
    cube: iris.cube.Cube, coordinate1: str, coordinate2: str, method: str, **kargs
) -> iris.cube.Cube:
    """
    Collapses similar (stash) fields in a cube into a 2D field in a cube based on 2 coordinates and method to collapsed. This could include time and vertical coordinate for instance.
    This could be a (weighted) mean or an accumulation.

    Arguments
    ---------
    cube: iris.cube.Cube
         Cube to collapse and iterate over one dimension
    coordinate: str
         Coordinate to collapse over
    method: Type of collapse i.e. method: 'MEAN', 'MAX', 'MIN', 'MEDIAN', 'PERCENTILE'
         getattr creates iris.analysis.MEAN, etc
         For PERCENTILE YAML file requires i.e.
         method: 'PERCENTILE'
         additional_percent: 90


    Returns
    -------
    cube: iris.cube.Cube
         Single variable but several methods of collapse such as mean, median, max, min, percentile


    Raises
    ------
    ValueError
    If the constraint doesn't produce a single cube containing a field.
    """

    # collapse cube over single dimension
    # dimensions: 2 of i.e. 'time', 'longitude', 'latitude'
    # method: iris.analysis.MEAN, iris.analysis.MAX, iris.analysis.MIN
    # ensure that time is passed in as 'time'
    # collapsed_cube = cube.collapsed("time", iris.analysis.MEAN)
    collapsed_cube = cube.collapsed(
        [coordinate2, coordinate2], getattr(iris.analysis, method)
    )

    return collapsed_cube


# TODO
# collapse function that calculates means, medians etc across members of an ensemble or stratified groups.
# Need to allow collapse over realisation dimension for fixed time. Hence will require reading in of CubeList
