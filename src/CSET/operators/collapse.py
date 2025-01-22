# © Crown copyright, Met Office (2022-2025) and CSET contributors.
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

import warnings

import iris
import iris.analysis
import iris.coord_categorisation
import iris.cube

from CSET.operators._utils import ensure_aggregatable_across_cases


def collapse(
    cube: iris.cube.Cube,
    coordinate: str | list[str],
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
    if method == "PERCENTILE" and additional_percent is None:
        raise ValueError("Must specify additional_percent")
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore", "Cannot check if coordinate is contiguous", UserWarning
        )
        warnings.filterwarnings(
            "ignore", "Collapsing spatial coordinate.+without weighting", UserWarning
        )
        if method == "PERCENTILE":
            collapsed_cube = cube.collapsed(
                coordinate, getattr(iris.analysis, method), percent=additional_percent
            )
        else:
            collapsed_cube = cube.collapsed(coordinate, getattr(iris.analysis, method))
    return collapsed_cube


def collapse_by_lead_time(
    cube: iris.cube.Cube | iris.cube.CubeList,
    method: str,
    additional_percent: float = None,
    **kwargs,
) -> iris.cube.Cube:
    """Collapse a cube around lead time for multiple cases.

    First checks if the data can be aggregated by lead time easily. Then
    collapses by lead time for a specified method using the collapse function.

    Arguments
    ---------
    cube: iris.cube.Cube | iris.cube.CubeList
        Cube to collapse by lead time or CubeList that will be converted
        to a cube before collapsing by lead time.
    method: str
         Type of collapse i.e. method: 'MEAN', 'MAX', 'MIN', 'MEDIAN',
         'PERCENTILE'. For 'PERCENTILE' the additional_percent must be specified.

    Returns
    -------
    cube: iris.cube.Cube
        Single variable collapsed by lead time based on chosen method.

    Raises
    ------
    ValueError
        If additional_percent wasn't supplied while using PERCENTILE method.
    """
    if method == "PERCENTILE" and additional_percent is None:
        raise ValueError("Must specify additional_percent")
    # Ensure the cube can be aggregated over multiple cases.
    cube_to_collapse = ensure_aggregatable_across_cases(cube)
    # Collapse by lead time.
    if method == "PERCENTILE":
        collapsed_cube = collapse(
            cube_to_collapse,
            "forecast_period",
            method,
            additional_percent=additional_percent,
        )
    else:
        collapsed_cube = collapse(cube_to_collapse, "forecast_period", method)
    return collapsed_cube


def collapse_by_hour_of_day(
    cube: iris.cube.Cube,
    method: str,
    additional_percent: float = None,
    **kwargs,
) -> iris.cube.Cube:
    """Collapse a cube by hour of the day.

    Arguments
    ---------
    cube: iris.cube.Cube
        Cube to collapse and iterate over one dimension. It should contain only
        one time dimension.
    method: str
        Type of collapse i.e. method: 'MEAN', 'MAX', 'MIN', 'MEDIAN',
        'PERCENTILE'. For 'PERCENTILE' the additional_percent must be specified.

    Returns
    -------
    cube: iris.cube.Cube
        Single variable but several methods of aggregation.

    Raises
    ------
    ValueError
        If additional_percent wasn't supplied while using PERCENTILE method.

    Notes
    -----
    Collapsing of the cube is around the 'time' coordinate. The coordinates are
    first grouped by the hour of day, and then aggregated by the hour of day
    to create a diurnal cycle. This operator is applicable for both single
    forecasts and for multiple forecasts. The hour used is based on the units of
    the time coordinate. If the time coordinate is in UTC, hour will be in UTC.

    To apply this operator successfully there must only be one time dimension.
    Should a MultiDim exception be raised the user first needs to apply the
    collapse operator to reduce the time dimensions before applying this
    operator.
    """
    if method == "PERCENTILE" and additional_percent is None:
        raise ValueError("Must specify additional_percent")
    # Categorise the time coordinate by hour of the day.
    iris.coord_categorisation.add_hour(cube, "time", name="hour")
    # Aggregate by the new category coordinate.
    if method == "PERCENTILE":
        collapsed_cube = cube.aggregated_by(
            "hour", getattr(iris.analysis, method), percent=additional_percent
        )
    else:
        collapsed_cube = cube.aggregated_by("hour", getattr(iris.analysis, method))
    # Remove unnecessary time coordinates.
    collapsed_cube.remove_coord("time")
    collapsed_cube.remove_coord("forecast_reference_time")
    collapsed_cube.remove_coord("forecast_period")
    return collapsed_cube


# TODO
# Collapse function that calculates means, medians etc across members of an
# ensemble or stratified groups. Need to allow collapse over realisation
# dimension for fixed time. Hence will require reading in of CubeList
