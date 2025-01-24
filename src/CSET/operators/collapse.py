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
import iris.util

from CSET.operators._utils import ensure_aggregatable_across_cases, is_time_aggregatable


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
    This operator provides the average of all T+1, T+2, etc.

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
            "forecast_reference_time",
            method,
            additional_percent=additional_percent,
        )
    else:
        collapsed_cube = collapse(cube_to_collapse, "forecast_reference_time", method)
    return collapsed_cube


def collapse_by_hour_of_day(
    cube: iris.cube.Cube | iris.cube.CubeList,
    method: str,
    additional_percent: float = None,
    multi_case: bool = True,
    **kwargs,
) -> iris.cube.Cube:
    """Collapse a cube by hour of the day.

    Collapses a cube by hour of the day in the time coordinates provided by the
    model. It is useful for creating diurnal cycle plots. It aggregates all
    00 UTC together regardless of lead time.

    Arguments
    ---------
    cube: iris.cube.Cube | iris.cube.CubeList
        Cube to collapse and iterate over one dimension or CubeList to
        convert to a cube and then collapse prior to aggregating by hour.
        If a CubeList is provided multi_case must be set to True as the Cube List
        should only contain cubes of multiple dates and not different variables
        or models. A cube that only contains one time dimension must have
        multi_case set to False as it contains only one forecast. A cube
        containing two time dimensions, e.g., 'forecast_reference_time' and
        'forecast_period' must have multi_case set to True as it will contain
        multiple forecasts.
    method: str
        Type of collapse i.e. method: 'MEAN', 'MAX', 'MIN', 'MEDIAN',
        'PERCENTILE'. For 'PERCENTILE' the additional_percent must be specified.
    multi_case: boolean, optional
        Default is True. If True multiple cases will be aggregated by hour of
        day; if False a single forecast will be aggregated by hour of day.
        Information around the usage of multi_case is provided above under the
        description for the cube argument. It is kept as an argument rather
        than being automatically generated to maintain traceability for the
        users actions.

    Returns
    -------
    cube: iris.cube.Cube
        Single variable but several methods of aggregation.

    Raises
    ------
    ValueError
        If additional_percent wasn't supplied while using PERCENTILE method.
    TypeError
        If a CubeList is given and multi_case is not True;
        if a Cube is given and contains two time dimensions and multi_case is not True;
        if a Cube is given and contains one time dimensions and multi_case is not False.

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
    operator. If multi_case is true the collapse_by_lead_time operator is
    applied and performs this step.
    """
    if method == "PERCENTILE" and additional_percent is None:
        raise ValueError("Must specify additional_percent")
    elif (
        isinstance(cube, iris.cube.Cube)
        and is_time_aggregatable(cube)
        and not multi_case
    ):
        raise TypeError(
            "multi_case must be true for a cube containing two time dimensions"
        )
    elif (
        isinstance(cube, iris.cube.Cube)
        and not is_time_aggregatable(cube)
        and multi_case
    ):
        raise TypeError(
            "multi_case must be false for a cube containing one time dimension"
        )
    elif isinstance(cube, iris.cube.CubeList) and not multi_case:
        raise TypeError("multi_case must be true for a CubeList")

    if multi_case:
        # Collapse by lead time to get a single time dimension.
        cube = collapse_by_lead_time(
            cube, method, additional_percent=additional_percent
        )

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
    collapsed_cube.remove_coord("forecast_period")
    # Remove forecast_reference_time if a single case, as collapse_by_lead_time
    # will have effectively done this if multi_case is True.
    if not multi_case:
        collapsed_cube.remove_coord("forecast_reference_time")

    # Promote "hour" to dim_coord if monotonic.
    if collapsed_cube.coord("hour").is_monotonic():
        iris.util.promote_aux_coord_to_dim_coord(collapsed_cube, "hour")
    return collapsed_cube


def collapse_by_validity_time(
    cube: iris.cube.Cube | iris.cube.CubeList,
    method: str,
    additional_percent: float = None,
    **kwargs,
) -> iris.cube.Cube:
    """Collapse a cube around validity time for multiple cases.

    First checks if the data can be aggregated easily. Then creates a new cube
    by slicing over the time dimensions, removing the time dimensions,
    re-merging the data, and creating a new time coordinate. It then collapses
    by the new time coordinate for a specified method using the collapse
    function.

    Arguments
    ---------
    cube: iris.cube.Cube | iris.cube.CubeList
        Cube to collapse by validity time or CubeList that will be converted
        to a cube before collapsing by validity time.
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
    # Ensure the cube can be aggregated over multiple times.
    cube_to_collapse = ensure_aggregatable_across_cases(cube)
    # Convert to a cube that is split by validity time.
    # Slice over cube by both time dimensions to create a CubeList.
    new_cubelist = iris.cube.CubeList(
        cube_to_collapse.slices_over(["forecast_period", "forecast_reference_time"])
    )
    # Remove forecast_period and forecast_reference_time coordinates.
    for sub_cube in new_cubelist:
        sub_cube.remove_coord("forecast_period")
        sub_cube.remove_coord("forecast_reference_time")
    # Create new CubeList by merging with unique = False to produce a validity
    # time cube.
    merged_list_1 = new_cubelist.merge(unique=False)
    # Create a new "fake" coordinate and apply to each remaining cube to allow
    # final merging to take place into a single cube.
    equalised_validity_time = iris.coords.AuxCoord(
        points=0, long_name="equalised_validity_time", units="1"
    )
    for sub_cube, eq_valid_time in zip(
        merged_list_1, range(len(merged_list_1)), strict=True
    ):
        sub_cube.add_aux_coord(equalised_validity_time.copy(points=eq_valid_time))

    # Merge CubeList to create final cube.
    final_cube = merged_list_1.merge_cube()
    # Collapse over fake_time_coord to represent collapsing over validity time.
    if method == "PERCENTILE":
        collapsed_cube = collapse(
            final_cube,
            "equalised_validity_time",
            method,
            additional_percent=additional_percent,
        )
    else:
        collapsed_cube = collapse(final_cube, "equalised_validity_time", method)
    return collapsed_cube


# TODO
# Collapse function that calculates means, medians etc across members of an
# ensemble or stratified groups. Need to allow collapse over realisation
# dimension for fixed time. Hence will require reading in of CubeList
