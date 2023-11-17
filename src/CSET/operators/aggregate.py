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

"""Operators to aggregate across either 1 or 2 dimensions."""

import iris
import iris.analysis
import iris.coord_categorisation
import iris.cube
import isodate


def aggregate(
    cube: iris.cube.Cube,
    coordinate: str,
    method: str,
    interval_iso: str,
    **kwargs,
) -> iris.cube.Cube:
    """Aggregate a coordinate into bins of a field.

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
        iris.analysis.MEAN, etc For PERCENTILE YAML file requires i.e. method:
        'PERCENTILE' additional_percent: 90.
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
    # duration of ISO timedelta
    timedelta = isodate.parse_duration(interval_iso)

    # convert interval format to hours
    interval = timedelta.total_seconds() / 3600

    # round to nearest hour
    interval = int(interval)

    # add time categorisation overwriting hourly increment via lambda coord
    # https://scitools-iris.readthedocs.io/en/latest/_modules/iris/coord_categorisation.html
    iris.coord_categorisation.add_categorised_coord(
        cube, "interval", coordinate, lambda coord, cell: cell // interval * interval
    )

    # Calculate hourly aggregated data using SUM.
    aggregated_cube = cube.aggregated_by("interval", getattr(iris.analysis, method))
    aggregated_cube.remove_coord("interval")
    return aggregated_cube
