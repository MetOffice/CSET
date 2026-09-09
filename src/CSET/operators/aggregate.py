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
from CSET.operators._utils import is_time_aggregatable

logger = logging.getLogger(__name__)


def time_aggregate(
    cubes: iris.cube.Cube | iris.cube.CubeList,
    method: str,
    interval_iso: str,
    **kwargs,
) -> iris.cube.Cube | iris.cube.CubeList:
    """Aggregate cube/cubes by its time coordinate.

    Aggregates similar (stash) fields in a cube or cube list for the specified coordinate and
    using the method supplied. The aggregated cube/cubelist will keep the coordinate and
    add a coordinate with the aggregated end time points.

    Can also handle multiple forecast reference times.

    Examples are: 1. Generating hourly or 6-hourly precipitation accumulations
    given an interval for the new time coordinate.

    We use the isodate class to convert ISO 8601 durations into time intervals
    for creating a new time coordinate for aggregation.

    We use the lambda function to pass coord and interval into the callable
    category function in add_categorised to allow users to define their own
    sub-daily intervals for the new time coordinate.

    Arguments
    ---------
    cubes: iris.cube.Cube | iris.cube.CubeList
        Cube or CubeList to aggregate and iterate over one dimension
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
    resambpled_cubes: iris.cube.Cube | iris.cube.CubeList
        Single variable but several methods of aggregation

    Raises
    ------
    ValueError
        If the constraint doesn't produce a single cube containing a field.
    """
    if interval_iso == "0":
        return cubes

    if isinstance(cubes, iris.cube.Cube):
        cubes = iris.cube.CubeList([cubes])

    resampled_cubes = iris.cube.CubeList()

    timedelta = isodate.parse_duration(interval_iso)
    interval = int(timedelta.total_seconds() / 3600)

    for cube in cubes:
        # Handle cubes with multiple forecast cycles.
        if cube.coord("forecast_reference_time").shape[0] > 1:
            aggregated_cube = _aggregate_multi_frt_cube(cube, method, interval)
        else:
            aggregated_cube = _aggregate_by_interval(cube, method, interval)

    resampled_cubes.append(aggregated_cube)
    if len(resampled_cubes) == 1:
        return resampled_cubes[0]
    return resampled_cubes


def ensure_aggregatable_across_cases(
    cubes: iris.cube.Cube | iris.cube.CubeList,
) -> iris.cube.CubeList:
    """Ensure a Cube or CubeList can be aggregated across multiple cases.

    The cubes are grouped into buckets of compatible cubes, then each bucket is
    converted into a single aggregatable cube with ``forecast_period`` and
    ``forecast_reference_time`` dimension coordinates.

    Arguments
    ---------
    cubes: iris.cube.Cube | iris.cube.CubeList
        Each cube is checked to determine if it has the the necessary
        dimensional coordinates to be aggregatable, being processed if needed.

    Returns
    -------
    cubes: iris.cube.CubeList
        A CubeList of time aggregatable cubes.

    Raises
    ------
    ValueError
        If any of the provided cubes cannot be made aggregatable.

    Notes
    -----
    This is a simple operator designed to ensure that a Cube is aggregatable
    across cases. If a CubeList is presented it will create an aggregatable Cube
    from that list. Its functionality is for case study (or trial) aggregation
    to ensure that the full dataset can be loaded as a single cube. This
    functionality is particularly useful for percentiles, Q-Q plots, and
    histograms.

    The necessary dimension coordinates for a cube to be aggregatable are
    ``forecast_period`` and ``forecast_reference_time``.
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

    logger.debug("Buckets:\n%s", "\n---\n".join(str(b) for b in buckets))

    # Ensure each bucket is a single aggregatable cube.
    aggregatable_cubes = iris.cube.CubeList()
    for bucket in buckets:
        # Single cubes that are already aggregatable won't need processing.
        if len(bucket) == 1 and is_time_aggregatable(bucket[0]):
            aggregatable_cube = bucket[0]
            aggregatable_cube = _add_nref(aggregatable_cube)
            aggregatable_cubes.append(aggregatable_cube)
            continue

        # Create an aggregatable cube from the provided CubeList.
        to_merge = iris.cube.CubeList()
        for cube in bucket:
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

        # Verify cube is now aggregatable.
        if not is_time_aggregatable(aggregatable_cube):
            raise ValueError(
                "Cube should have 'forecast_period' and 'forecast_reference_time' dimension coordinates.",
                aggregatable_cube,
            )
        aggregatable_cubes.append(aggregatable_cube)

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


def _add_nref(cube: iris.cube.Cube):
    """Retain information on number of forecast_reference_time inputs.

    This preserves information on number of aggregated cases that can
    otherwise be lost on subsequent calls to collapse functions.
    """
    nref = np.size(cube.coord("forecast_reference_time").points)
    cube.coord("time").attributes["number_reference_times"] = nref
    return cube


def _aggregate_multi_frt_cube(
    cube: iris.cube.Cube, method: str, interval: int
) -> iris.cube.Cube:
    """Aggregate a cube with multiple forecast reference times.

    Aggregates each forecast cycle separately, then concatenates the results
    back into a single cube along forecast_reference_time.
    """
    aggregated_cycles = iris.cube.CubeList()
    for frt_cube in cube.slices_over("forecast_reference_time"):
        iris.coord_categorisation.add_categorised_coord(
            frt_cube,
            "interval",
            "time",
            lambda coord, cell: cell // interval * interval,
        )
        agg = frt_cube.aggregated_by(
            "interval",
            getattr(iris.analysis, method),
        )
        agg.remove_coord("interval")
        agg = iris.util.new_axis(
            agg,
            agg.coord("forecast_reference_time"),
        )
        aggregated_cycles.append(agg)
    # 2d auxtime causes issues concatenating. Solution is to nuke it. Do we need it downstream?
    # as we can construct it if needed.
    for cb in aggregated_cycles:
        cb.remove_coord("time")
    return aggregated_cycles.concatenate_cube()


def _aggregate_by_interval(cube: iris.cube.Cube, method: str, interval: int):
    iris.coord_categorisation.add_categorised_coord(
        cube,
        "interval",
        "time",
        lambda coord, cell: cell // interval * interval,
    )
    aggregated_cube = cube.aggregated_by(
        "interval",
        getattr(iris.analysis, method),
    )
    return aggregated_cube.remove_coord("interval")
