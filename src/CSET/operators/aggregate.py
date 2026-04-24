# © Crown copyright, Met Office (2022-2024) and CSET contributors.
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

"""Operators to aggregate across either 1 or 2 dimensions."""

import itertools
import logging

import iris
import iris.analysis
import iris.coord_categorisation
import iris.cube
import iris.exceptions
import iris.util
import isodate
import numpy as np

from CSET._common import iter_maybe
from CSET.operators._utils import (
    identify_unique_times,
    is_time_aggregatable,
    is_time_aux_coord,
    remove_cell_method,
    remove_duplicates,
)


def _add_nref(cube: iris.cube.Cube):
    """Retain information on number of forecast_reference_time inputs.

    This preserves information on number of aggregated cases that can
    otherwise be lost on subsequent calls to collapse functions.
    """
    nref = np.size(cube.coord("forecast_reference_time").points)
    cube.coord("time").attributes["number_reference_times"] = nref
    return cube


def time_aggregate(
    cube: iris.cube.Cube,
    method: str,
    interval_iso: str,
    **kwargs,
) -> iris.cube.Cube:
    """Aggregate cube by its time coordinate.

    Aggregates similar (stash) fields in a cube for the specified coordinate and
    using the method supplied. The aggregated cube will keep the coordinate and
    add a further coordinate with the aggregated end time points.

    Examples are: 1. Generating hourly or 6-hourly precipitation accumulations
    given an interval for the new time coordinate.

    We use the isodate class to convert ISO 8601 durations into time intervals
    for creating a new time coordinate for aggregation.

    We use the lambda function to pass coord and interval into the callable
    category function in add_categorised to allow users to define their own
    sub-daily intervals for the new time coordinate.

    Arguments
    ---------
    cube: iris.cube.Cube
        Cube to aggregate and iterate over one dimension
    coordinate: str
        Coordinate to aggregate over i.e. 'time', 'longitude',
        'latitude','model_level_number'.
    method: str
        Type of aggregate i.e. method: 'SUM', getattr creates
        iris.analysis.SUM, etc.
    interval_iso: isodate timedelta ISO 8601 object i.e PT6H (6 hours), PT30M (30 mins)
        Interval to aggregate over.

    Returns
    -------
    cube: iris.cube.Cube
        Single variable but several methods of aggregation

    Raises
    ------
    ValueError
        If the constraint doesn't produce a single cube containing a field.
    """
    # Duration of ISO timedelta.
    timedelta = isodate.parse_duration(interval_iso)

    # Convert interval format to whole hours.
    interval = int(timedelta.total_seconds() / 3600)

    # Add time categorisation overwriting hourly increment via lambda coord.
    # https://scitools-iris.readthedocs.io/en/latest/_modules/iris/coord_categorisation.html
    iris.coord_categorisation.add_categorised_coord(
        cube, "interval", "time", lambda coord, cell: cell // interval * interval
    )

    # Aggregate cube using supplied method.
    aggregated_cube = cube.aggregated_by("interval", getattr(iris.analysis, method))
    aggregated_cube.remove_coord("interval")
    return aggregated_cube


def ensure_aggregatable_across_cases(
    cubes: iris.cube.Cube | iris.cube.CubeList,
    time_coord_name: str,
) -> iris.cube.CubeList:
    """Ensure a Cube or CubeList can be aggregated across multiple cases.

    The cubes are grouped into buckets of compatible cubes. Each bucket is then
    processed to create aggregatable cubes. The function handles two types of
    time coordinates:

    - Dimension coordinates: Cubes with ``forecast_period`` and
      ``forecast_reference_time`` as dimension coordinates are sliced and merged.
    - Auxiliary coordinates: Cubes with time as an auxiliary coordinate are
      aggregated at each unique time point and then merged.

    Arguments
    ---------
    cubes: iris.cube.Cube | iris.cube.CubeList
        Each cube is checked to determine if it has the necessary time
        coordinates (either as dimension or auxiliary coordinates) to be
        aggregatable, being processed if needed.
    time_coord_name: str
        Name of the time coordinate to aggregate over, typically "time" or
        "forecast_period".

    Returns
    -------
    cubes: iris.cube.CubeList
        A CubeList of time aggregatable cubes. Each cube will have a
        ``number_reference_times`` attribute on its time coordinate indicating
        the number of forecast reference times aggregated.

    Raises
    ------
    ValueError
        If any of the provided cubes cannot be made aggregatable (i.e., missing
        required time coordinates).

    Notes
    -----
    This operator is designed to ensure that cubes can be aggregated across
    multiple cases (e.g., different model runs or forecast times). Its
    functionality is particularly useful for case study or trial aggregation
    when computing statistics such as percentiles, Q-Q plots, and histograms.

    For cubes to be aggregatable, they must have either:

    - ``forecast_period`` and ``forecast_reference_time`` as dimension
      or auxiliary coordinates
    """

    # Group compatible cubes.
    class Buckets:
        def __init__(self):
            self.buckets = []

        def add(self, cube: iris.cube.Cube):
            """Add a cube into a bucket.

            If the cube is compatible with an existing bucket it is added there.
            Otherwise it gets its own bucket.
            """
            for bucket in self.buckets:
                if bucket[0].is_compatible(cube):
                    bucket.append(cube)
                    return
            self.buckets.append(iris.cube.CubeList([cube]))

        def get_buckets(self) -> list[iris.cube.CubeList]:
            return self.buckets

    b = Buckets()
    for cube in iter_maybe(cubes):
        b.add(cube)
    buckets = b.get_buckets()

    logging.debug("Buckets:\n%s", "\n---\n".join(str(b) for b in buckets))

    # Ensure each bucket is a single aggregatable cube.
    aggregatable_cubes = iris.cube.CubeList()
    for bucket in buckets:
        # Single cubes that are already aggregatable won't need processing.
        if len(bucket) == 1 and is_time_aggregatable(bucket[0]):
            aggregatable_cube = bucket[0]
            aggregatable_cube = _add_nref(aggregatable_cube)
            aggregatable_cubes.append(aggregatable_cube)
            continue

        for cube in bucket:
            if is_time_aggregatable(cube):
                to_merge = iris.cube.CubeList()
                try:
                    to_merge.extend(
                        cube.slices_over(["forecast_period", "forecast_reference_time"])
                    )
                except iris.exceptions.CoordinateNotFoundError as err:
                    raise ValueError(
                        "Cube should have 'forecast_period' and 'forecast_reference_time' dimension coordinates.",
                        cube,
                    ) from err
                aggregatable_cube = to_merge.merge_cube()

                # Add attribute on number of forecast_reference_times
                aggregatable_cube = _add_nref(aggregatable_cube)

                aggregatable_cubes.append(aggregatable_cube)

            elif is_time_aux_coord(cube):
                times = identify_unique_times(cube, time_coord_name)

                aggregated_list = [
                    _aggregate_without_time_dimcoords(
                        cube, time, iris.analysis.MEAN, None
                    )
                    for time in times
                ]

                cubes_to_merge = iris.cube.CubeList(
                    itertools.chain.from_iterable(aggregated_list)
                )

                aggregatable_cubes = cubes_to_merge.merge_cube()

            else:
                raise ValueError(
                    "Cube is missing required dimension or auxliary time coordinates",
                    cube,
                )

    return aggregatable_cubes


def add_hour_coordinate(
    cubes: iris.cube.Cube | iris.cube.CubeList,
) -> iris.cube.Cube | iris.cube.CubeList:
    """Add a category coordinate of hour of day to a Cube or CubeList.

    Arguments
    ---------
    cubes: iris.cube.Cube | iris.cube.CubeList
        Cube of any variable that has a time coordinate.
        Note input Cube or CubeList items should only have 1 time dimension.

    Returns
    -------
    cube: iris.cube.Cube
        A Cube with an additional auxiliary coordinate of hour.

    Notes
    -----
    This is a simple operator designed to be used prior to case aggregation for
    histograms, Q-Q plots, and percentiles when aggregated by hour of day.
    """
    new_cubelist = iris.cube.CubeList()
    for cube in iter_maybe(cubes):
        # Add a category coordinate of hour into each cube.
        iris.util.promote_aux_coord_to_dim_coord(cube, "time")
        iris.coord_categorisation.add_hour(cube, "time", name="hour")
        cube.coord("hour").units = "hours"
        new_cubelist.append(cube)

    if len(new_cubelist) == 1:
        return new_cubelist[0]
    else:
        return new_cubelist


def rolling_window_time_aggregation(
    cubes: iris.cube.Cube | iris.cube.CubeList, method: str, window: int
) -> iris.cube.Cube | iris.cube.CubeList:
    """Aggregate a cube along the time dimension using a rolling window.

    Arguments
    ---------
    cubes: iris.cube.Cube | iris.cube.CubeList
        Cube or Cubelist of any variable to be aggregated over a rolling window
        in time.
    method: str
        Type of aggregate i.e. method: 'MAX', getattr creates
        iris.analysis.MAX, etc.
    window: int
        The rolling window size.

    Returns
    -------
    cube: iris.cube.Cube | iris.cube.CubeList
        A Cube or Cubelist of the rolling window aggregate. The Cubes will have
        a time dimension that is reduced in size to the original cube by the
        window size.

    Notes
    -----
    This operator is designed to be used to help create daily maxima and minima
    for any variable.
    """
    new_cubelist = iris.cube.CubeList()
    for cube in iter_maybe(cubes):
        # Use a rolling window in time to applied specified aggregation method
        # over a specified window length.
        window_cube = cube.rolling_window(
            "time", getattr(iris.analysis, method), window
        )
        new_cubelist.append(window_cube)

    if len(new_cubelist) == 1:
        return new_cubelist[0]
    else:
        return new_cubelist


def _aggregate_without_time_dimcoords(cubes, time_coord, aggregator, percentile):
    """Aggregate cubes at a specific time without time dimension coordinates.

    Arguments
    ---------
    cubes: iris.cube.CubeList
        Cubes to aggregate.
    time_coord: iris.coords.Coord
        Single time coordinate point to aggregate at.
    aggregator: iris.analysis.Aggregator
        Aggregation method (e.g., iris.analysis.MEAN).
    percentile: float, optional
        Percentile value if using PERCENTILE aggregator.
    """
    # Handle single cube input
    if isinstance(cubes, iris.cube.Cube):
        cubes = iris.cube.CubeList([cubes])

    # Check the supplied time coordinate to make sure it corresponds to a
    # single time only
    if len(time_coord.points) != 1:
        raise ValueError("Time coordinate should specify a single time only")

    # Remove any duplicate cubes in the input
    cubes = remove_duplicates(cubes)

    time_coord_name = time_coord.name()

    time_constraint = iris.Constraint(
        coord_values={time_coord_name: lambda cell: cell.point in time_coord.cells()}
    )
    cubes_at_time = cubes.extract(time_constraint)

    # Add a temporary "number" coordinate to uniquely label the different
    # data points at this time
    number = 0
    numbered_cubes = iris.cube.CubeList()
    for cube in cubes_at_time:
        for slc in cube.slices_over(time_coord_name):
            number_coord = iris.coords.AuxCoord(number, long_name="number")
            slc.add_aux_coord(number_coord)
            numbered_cubes.append(slc)
            number += 1
    cubes_at_time = numbered_cubes

    cubes_at_time = cubes_at_time.merge()

    aggregated_cubes = iris.cube.CubeList()
    for cube in cubes_at_time:
        # If there was only a single data point at this time, then "number"
        # will be a scalar coordinate. If so, make it a dimension coordinate
        # to allow collapsing
        if not cube.coord_dims("number"):
            cube = iris.util.new_axis(cube, scalar_coord="number")

        num_cases = cube.coord("number").points.size
        num_cases_coord = iris.coords.AuxCoord(num_cases, long_name="num_cases")
        cube.add_aux_coord(num_cases_coord)

        # Do aggregation across the temporary "number" coordinate
        if isinstance(aggregator, type(iris.analysis.PERCENTILE)):
            cube = cube.collapsed("number", aggregator, percent=percentile)
        else:
            cube = cube.collapsed("number", aggregator)

        # Now remove the "number" coordinate and its cell method
        cube.remove_coord("number")
        cell_method = iris.coords.CellMethod(aggregator.name(), coords="number")
        cube = remove_cell_method(cube, cell_method)

        aggregated_cubes.append(cube)

    return aggregated_cubes
