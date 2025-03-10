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

import datetime
import logging
import warnings

import iris
import iris.analysis
import iris.coord_categorisation
import iris.coords
import iris.cube
import iris.exceptions
import iris.util

from CSET._common import iter_maybe
from CSET.operators._utils import is_time_aggregatable
from CSET.operators.aggregate import add_hour_coordinate


def collapse(
    cubes: iris.cube.Cube | iris.cube.CubeList,
    coordinate: str | list[str],
    method: str,
    additional_percent: float = None,
    **kwargs,
) -> iris.cube.Cube | iris.cube.CubeList:
    """Collapse coordinate(s) of a single cube or of every cube in a cube list.

    Collapses similar fields in each cube into a cube collapsing around the
    specified coordinate(s) and method. This could be a (weighted) mean or
    percentile.

    Arguments
    ---------
    cubes: iris.cube.Cube | iris.cube.CubeList
        Cube or CubeList to collapse and iterate over one dimension
    coordinate: str | list[str]
        Coordinate(s) to collapse over e.g. 'time', 'longitude', 'latitude',
        'model_level_number', 'realization'. A list of multiple coordinates can
        be given.
    method: str
        Type of collapse i.e. method: 'MEAN', 'MAX', 'MIN', 'MEDIAN',
        'PERCENTILE' getattr creates iris.analysis.MEAN, etc For PERCENTILE YAML
        file requires i.e. method: 'PERCENTILE' additional_percent: 90
    additional_percent: float, optional
        Required for the PERCENTILE method. This is a number between 0 and 100.

    Returns
    -------
    collapsed_cubes: iris.cube.Cube | iris.cube.CubeList
        Single variable but several methods of aggregation

    Raises
    ------
    ValueError
        If additional_percent wasn't supplied while using PERCENTILE method.
    """
    if method == "PERCENTILE" and additional_percent is None:
        raise ValueError("Must specify additional_percent")
    collapsed_cubes = iris.cube.CubeList([])
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore", "Cannot check if coordinate is contiguous", UserWarning
        )
        warnings.filterwarnings(
            "ignore", "Collapsing spatial coordinate.+without weighting", UserWarning
        )
        for cube in iter_maybe(cubes):
            if method == "PERCENTILE":
                collapsed_cubes.append(
                    cube.collapsed(
                        coordinate,
                        getattr(iris.analysis, method),
                        percent=additional_percent,
                    )
                )
            else:
                collapsed_cubes.append(
                    cube.collapsed(coordinate, getattr(iris.analysis, method))
                )
    if len(collapsed_cubes) == 1:
        return collapsed_cubes[0]
    else:
        return collapsed_cubes


def collapse_by_hour_of_day(
    cubes: iris.cube.Cube | iris.cube.CubeList,
    method: str,
    additional_percent: float = None,
    **kwargs,
) -> iris.cube.Cube:
    """Collapse a cube by hour of the day.

    Collapses a cube by hour of the day in the time coordinates provided by the
    model. It is useful for creating diurnal cycle plots. It aggregates all 00
    UTC together regardless of lead time.

    Arguments
    ---------
    cubes: iris.cube.Cube | iris.cube.CubeList
        Cube to collapse and iterate over one dimension or CubeList to convert
        to a cube and then collapse prior to aggregating by hour. If a CubeList
        is provided each cube is handled separately.
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
    first grouped by the hour of day, and then aggregated by the hour of day to
    create a diurnal cycle. This operator is applicable for both single
    forecasts and for multiple forecasts. The hour used is based on the units of
    the time coordinate. If the time coordinate is in UTC, hour will be in UTC.

    To apply this operator successfully there must only be one time dimension.
    Should a MultiDim exception be raised the user first needs to apply the
    collapse operator to reduce the time dimensions before applying this
    operator. A cube containing the two time dimensions
    'forecast_reference_time' and 'forecast_period' will be automatically
    collapsed by lead time before being being collapsed by hour of day.
    """
    if method == "PERCENTILE" and additional_percent is None:
        raise ValueError("Must specify additional_percent")

    collapsed_cubes = iris.cube.CubeList([])
    for cube in iter_maybe(cubes):
        if is_time_aggregatable(cube):
            # Collapse by lead time to get a single time dimension.
            cube = collapse(
                cube,
                "forecast_reference_time",
                method,
                additional_percent=additional_percent,
            )
        else:
            # Remove forecast_reference_time if a single case, as collapse will
            # have effectively done this.
            cube.remove_coord("forecast_reference_time")

        # Categorise the time coordinate by hour of the day.
        cube = add_hour_coordinate(cube)
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

        # Sort hour coordinate.
        collapsed_cube.coord("hour").points.sort()

        # Promote "hour" to dim_coord.
        iris.util.promote_aux_coord_to_dim_coord(collapsed_cube, "hour")
        collapsed_cubes.append(collapsed_cube)
    if len(collapsed_cubes) == 1:
        return collapsed_cubes[0]
    else:
        return collapsed_cubes


def collapse_by_validity_time(
    cubes: iris.cube.Cube | iris.cube.CubeList,
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
    cubes: iris.cube.Cube | iris.cube.CubeList
        Cube to collapse by validity time or CubeList that will be converted
        to a cube before collapsing by validity time.
    method: str
         Type of collapse i.e. method: 'MEAN', 'MAX', 'MIN', 'MEDIAN',
         'PERCENTILE'. For 'PERCENTILE' the additional_percent must be specified.

    Returns
    -------
    cube: iris.cube.Cube | iris.cube.CubeList
        Single variable collapsed by lead time based on chosen method.

    Raises
    ------
    ValueError
        If additional_percent wasn't supplied while using PERCENTILE method.
    """
    if method == "PERCENTILE" and additional_percent is None:
        raise ValueError("Must specify additional_percent")

    collapsed_cubes = iris.cube.CubeList([])
    for cube in iter_maybe(cubes):
        # Slice over cube by both time dimensions to create a CubeList.
        new_cubelist = iris.cube.CubeList(
            cube.slices_over(["forecast_period", "forecast_reference_time"])
        )
        for sub_cube in new_cubelist:
            # Reconstruct the time coordinate if it is missing.
            if "time" not in [coord.name() for coord in sub_cube.coords()]:
                ref_time_coord = sub_cube.coord("forecast_reference_time")
                ref_units = ref_time_coord.units
                ref_time = ref_units.num2date(ref_time_coord.points)
                period_coord = sub_cube.coord("forecast_period")
                period_units = period_coord.units
                # Given how we are slicing there will only be one point.
                period_seconds = period_units.convert(period_coord.points[0], "seconds")
                period_duration = datetime.timedelta(seconds=period_seconds)
                time = ref_time + period_duration
                time_points = ref_units.date2num(time)
                time_coord = iris.coords.AuxCoord(
                    points=time_points, standard_name="time", units=ref_units
                )
                sub_cube.add_aux_coord(time_coord)
            # Remove forecast_period and forecast_reference_time coordinates.
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
        logging.debug("Pre-collapse validity time cube:\n%s", final_cube)

        # Collapse over equalised_validity_time as a proxy for equal validity
        # time.
        try:
            collapsed_cube = collapse(
                final_cube,
                "equalised_validity_time",
                method,
                additional_percent=additional_percent,
            )
        except iris.exceptions.CoordinateCollapseError as err:
            raise ValueError(
                "Cubes do not overlap therefore cannot collapse across validity time."
            ) from err
        collapsed_cube.remove_coord("equalised_validity_time")
        collapsed_cubes.append(collapsed_cube)

    if len(collapsed_cubes) == 1:
        return collapsed_cubes[0]
    else:
        return collapsed_cubes


# TODO
# Collapse function that calculates means, medians etc across members of an
# ensemble or stratified groups. Need to allow collapse over realisation
# dimension for fixed time. Hence will require reading in of CubeList
