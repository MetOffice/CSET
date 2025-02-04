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

import iris
import iris.analysis
import iris.coord_categorisation
import iris.cube
import isodate

from CSET._common import iter_maybe
from CSET.operators._utils import is_time_aggregatable


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
    cube: iris.cube.Cube | iris.cube.CubeList,
) -> iris.cube.Cube:
    """Ensure a Cube or CubeList can be aggregated across multiple cases.

    Arguments
    ---------
    cube: iris.cube.Cube | iris.cube.CubeList
        If a Cube is provided it is checked to determine if it has the
        the necessary dimensional coordinates to be aggregatable.
        These necessary coordinates are 'forecast_period' and
        'forecast_reference_time'.If a CubeList is provided a Cube is created
        by slicing over all time coordinates and the resulting list is merged
        to create an aggregatable cube.

    Returns
    -------
    cube: iris.cube.Cube
        A time aggregatable cube with dimension coordinates including
        'forecast_period' and 'forecast_reference_time'.

    Raises
    ------
    ValueError
        If a Cube is provided and it is not aggregatable a ValueError is
        raised. The user should then provide a CubeList to be turned into an
        aggregatable cube to allow aggregation across multiple cases to occur.

    Notes
    -----
    This is a simple operator designed to ensure that a Cube is aggregatable
    across cases. If a CubeList is presented it will create an aggregatable Cube
    from that list. Its functionality is for case study (or trial) aggregation
    to ensure that the full dataset can be loaded as a single cube. This
    functionality is particularly useful for percentiles, Q-Q plots, and
    histograms.
    """
    # Check to see if a cube is input and if that cube is iterable.
    if isinstance(cube, iris.cube.Cube):
        if is_time_aggregatable(cube):
            return cube
        else:
            raise ValueError(
                "Single Cube should have 'forecast_period' and"
                "'forecast_reference_time' dimensional coordinates. "
                "To make a time aggregatable Cube input a CubeList."
            )
    # Create an aggregatable cube from the provided CubeList.
    else:
        new_cube_list = iris.cube.CubeList()
        for sub_cube in cube:
            for cube_slice in sub_cube.slices_over(
                ["forecast_period", "forecast_reference_time"]
            ):
                new_cube_list.append(cube_slice)
        new_merged_cube = new_cube_list.merge_cube()
        return new_merged_cube


def add_hour_coordinate(
    cubes: iris.cube.Cube | iris.cube.CubeList,
) -> iris.cube.Cube | iris.cube.CubeList:
    """Add a category coordinate of hour of day to a Cube or CubeList.

    Arguments
    ---------
    cubes: iris.cube.Cube | iris.cube.CubeList
        Cube of any variable that has a time coordinate.

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
        iris.coord_categorisation.add_hour(cube, "time", name="hour")
        cube.coord("hour").units = "hours"
        new_cubelist.append(cube)

    if len(new_cubelist) == 1:
        return new_cubelist[0]
    else:
        return new_cubelist
