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


def _add_nref(cube: iris.cube.Cube):
    """Retain information on number of forecast_reference_time inputs.

    This preserves information on number of aggregated cases that can
    otherwise be lost on subsequent calls to collapse functions.
    """
    nref = np.size(cube.coord("forecast_reference_time").points)
    cube.coord("time").attributes["number_reference_times"] = nref
    return cube


def time_aggregate(
    cubes: iris.cube.Cube | iris.cube.CubeList,
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
    cube: iris.cube.Cube
        Single variable but several methods of aggregation

    Raises
    ------
    ValueError
        If the constraint doesn't produce a single cube containing a field.
    """
    if timedelta == "0":
        return cubes

    resampled_cubes = iris.cube.CubeList()

    for cube in cubes:
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

        resampled_cubes.append(aggregated_cube)

    if len(resampled_cubes) == 1:
        return resampled_cubes[0]
    else:
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


import iris
from iris.coords import AuxCoord, DimCoord
from iris.cube import Cube


def combine_obs_across_forecasts(cubes):
    """
    Combine observation cubes from multiple forecast_reference_times.

    Input:
        CubeList of cubes with dimensions

            (time, station)

    Output:
        Cube with dimensions

            (forecast_reference_time,
             forecast_period,
             station)

    where

        time

    becomes a 2D auxiliary coordinate attached to

        (forecast_reference_time, forecast_period)

    Only stations present in every forecast are retained.
    All station metadata coordinates are preserved.
    """
    if len(cubes) < 2:
        raise ValueError("Need at least two cubes")

    # --------------------------------------------------------------
    # Find stations common to all cubes with complete data
    # --------------------------------------------------------------

    valid_station_sets = []

    for cube in cubes:
        names = cube.coord("Station_Name").points

        data = cube.data

        # Handle masked and unmasked arrays
        if np.ma.isMaskedArray(data):
            mask = np.ma.getmaskarray(data)
            station_valid = ~np.any(mask, axis=0) & np.all(
                np.isfinite(data.filled(np.nan)), axis=0
            )
        else:
            station_valid = np.all(np.isfinite(data), axis=0)

        valid_station_sets.append(set(names[station_valid]))

    common_stations = sorted(set.intersection(*valid_station_sets))

    logger.info(
        "Retaining %s/%s stations with complete observations",
        len(common_stations),
        cube.shape[1],
    )

    if not common_stations:
        raise ValueError(
            "No stations with complete data in all forecast_reference_times"
        )

    # --------------------------------------------------------------
    # Build station lookup for every cube
    # --------------------------------------------------------------

    subset_data = []
    frt_points = []
    time_points = []

    for cube in cubes:
        names = cube.coord("Station_Name").points

        lookup = {name: idx for idx, name in enumerate(names)}

        station_indices = [lookup[name] for name in common_stations]

        subcube = cube[:, station_indices]

        subset_data.append(subcube.data)

        frt_points.append(cube.coord("forecast_reference_time").points[0])

        time_points.append(cube.coord("time").points)

    # --------------------------------------------------------------
    # Check all cubes have same time axis length
    # --------------------------------------------------------------

    ntime = len(time_points[0])

    for t in time_points[1:]:
        if len(t) != ntime:
            raise ValueError("Forecasts have different numbers of lead times")

    # --------------------------------------------------------------
    # Generate forecast period
    # --------------------------------------------------------------

    time_coord = cubes[0].coord("time")
    frt_coord = cubes[0].coord("forecast_reference_time")

    frt_date = frt_coord.units.num2date(frt_coord.points[0])

    fp_hours = []

    for dt in time_coord.units.num2date(time_coord.points):
        fp_hours.append((dt - frt_date).total_seconds() / 3600)

    fp_hours = np.asarray(fp_hours)

    # --------------------------------------------------------------
    # Stack data
    # --------------------------------------------------------------

    data = np.stack(subset_data, axis=0)

    # shape:
    #
    # (forecast_reference_time,
    #  forecast_period,
    #  station)

    # --------------------------------------------------------------
    # Output coordinates
    # --------------------------------------------------------------

    frt_out = DimCoord(
        frt_points,
        standard_name="forecast_reference_time",
        units=cubes[0].coord("forecast_reference_time").units,
    )

    fp_out = DimCoord(
        fp_hours,
        standard_name="forecast_period",
        units="hours",
    )

    station_out = DimCoord(
        np.arange(len(common_stations)),
        long_name="station",
    )

    cube_out = Cube(
        data,
        standard_name=cubes[0].standard_name,
        long_name=cubes[0].long_name,
        var_name=cubes[0].var_name,
        units=cubes[0].units,
        attributes=cubes[0].attributes.copy(),
        dim_coords_and_dims=[
            (frt_out, 0),
            (fp_out, 1),
            (station_out, 2),
        ],
    )

    # --------------------------------------------------------------
    # Preserve station metadata coordinates
    # --------------------------------------------------------------

    ref_cube = cubes[0]

    ref_names = ref_cube.coord("Station_Name").points

    ref_lookup = {name: idx for idx, name in enumerate(ref_names)}

    common_idx = [ref_lookup[name] for name in common_stations]

    # skip coords as we have awkward station and station_0 arbritary monotonic arrays.
    for coord in ref_cube.aux_coords:
        try:
            dims = ref_cube.coord_dims(coord)
        except Exception:
            continue

        # only coords attached solely to station axis
        if dims != (1,):
            continue

        values = coord.points[common_idx]

        # verify same in every cube
        for cube in cubes[1:]:
            cube_names = cube.coord("Station_Name").points

            cube_lookup = {name: idx for idx, name in enumerate(cube_names)}

            idx = [cube_lookup[name] for name in common_stations]

            other_values = cube.coord(coord.name()).points[idx]

            if not np.array_equal(
                values,
                other_values,
            ):
                raise ValueError(f"Station metadata differs for coord '{coord.name()}'")

        aux = AuxCoord(
            values,
            standard_name=coord.standard_name,
            long_name=coord.long_name,
            var_name=coord.var_name,
            units=coord.units,
            attributes=coord.attributes.copy(),
        )

        cube_out.add_aux_coord(aux, (2,))

    # --------------------------------------------------------------
    # Add valid-time auxiliary coord
    # --------------------------------------------------------------

    time_2d = np.vstack(time_points)

    cube_out.add_aux_coord(
        AuxCoord(
            time_2d,
            standard_name="time",
            units=time_coord.units,
        ),
        (0, 1),
    )

    return cube_out


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
