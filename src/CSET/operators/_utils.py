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

"""
Common operator functionality used across CSET.

Functions below should only be added if it is not suitable as a standalone
operator, and will be used across multiple operators.
"""

import logging
import re
from datetime import timedelta

import iris
import iris.cube
import iris.exceptions
import iris.util
from iris.time import PartialDateTime


def pdt_fromisoformat(
    datestring,
) -> tuple[iris.time.PartialDateTime, timedelta | None]:
    """Generate PartialDateTime object.

    Function that takes an ISO 8601 date string and returns a PartialDateTime object.

    Arguments
    ---------
    datestring: str
        ISO 8601 date.

    Returns
    -------
    time_object: iris.time.PartialDateTime
    """

    def make_offset(sign, value) -> timedelta:
        if len(value) not in [2, 4, 5]:
            raise ValueError(f'expected "hh", "hhmm", or "hh:mm", got {value}')

        hours = int(value[:2])
        minutes = 0
        if len(value) in [4, 5]:
            minutes = int(value[-2:])
        return timedelta(hours=sign * hours, minutes=sign * minutes)

    # Remove the microseconds coord due to no support in PartialDateTime
    datestring = re.sub(r"\.\d+", "", datestring)

    datetime_split = datestring.split("T")
    date = datetime_split[0]
    if len(datetime_split) == 1:
        time = ""
    elif len(datetime_split) == 2:
        time = datetime_split[1]
    else:
        raise ValueError("datesting in an unexpected format")

    offset = None
    time_split = time.split("+")
    if len(time_split) == 2:
        time = time_split[0]
        offset = make_offset(1, time_split[1])
    else:
        time_split = time.split("-")
        if len(time_split) == 2:
            time = time_split[0]
            offset = make_offset(-1, time_split[1])
        else:
            offset = None

    if re.fullmatch(r"\d{8}", date):
        date = f"{date[0:4]}-{date[4:6]}-{date[6:8]}"
    elif re.fullmatch(r"\d{6}", date):
        date = f"{date[0:4]}-{date[4:6]}"

    if len(date) < 7:
        raise ValueError(f"Invalid datestring: {datestring}, must be at least YYYY-MM")

    # Returning a PartialDateTime for the special case of string form "YYYY-MM"
    if re.fullmatch(r"\d{4}-\d{2}", date):
        pdt = PartialDateTime(
            year=int(date[0:4]),
            month=int(date[5:7]),
            day=None,
            hour=None,
            minute=None,
            second=None,
        )
        return pdt, offset

    year = int(date[0:4])
    month = int(date[5:7])
    day = int(date[8:10])

    kwargs = dict(year=year, month=month, day=day, hour=0, minute=0, second=0)

    # Normalise the time parts into standard format
    if re.fullmatch(r"\d{4}", time):
        time = f"{time[0:2]}:{time[2:4]}"
    if re.fullmatch(r"\d{6}", time):
        time = f"{time[0:2]}:{time[2:4]}:{time[4:6]}"

    if len(time) >= 2:
        kwargs["hour"] = int(time[0:2])
    if len(time) >= 5:
        kwargs["minute"] = int(time[3:5])
    if len(time) >= 8:
        kwargs["second"] = int(time[6:8])

    pdt = PartialDateTime(**kwargs)

    return pdt, offset


def get_cube_yxcoordname(cube: iris.cube.Cube) -> tuple[str, str]:
    """
    Return horizontal dimension coordinate name(s) from a given cube.

    Arguments
    ---------

    cube: iris.cube.Cube
        An iris cube which will be checked to see if it contains coordinate
        names that match a pre-defined list of acceptable horizontal
        dimension coordinate names.

    Returns
    -------
    (y_coord, x_coord)
        A tuple containing the horizontal coordinate name for latitude and longitude respectively
        found within the cube.

    Raises
    ------
    ValueError
        If a unique y/x horizontal coordinate cannot be found.
    """
    # Acceptable horizontal coordinate names.
    X_COORD_NAMES = ["longitude", "grid_longitude", "projection_x_coordinate", "x"]
    Y_COORD_NAMES = ["latitude", "grid_latitude", "projection_y_coordinate", "y"]

    # Get a list of dimension coordinate names for the cube
    dim_coord_names = [coord.name() for coord in cube.coords(dim_coords=True)]
    coord_names = [coord.name() for coord in cube.coords()]

    # Check which x-coordinate we have, if any
    x_coords = [coord for coord in coord_names if coord in X_COORD_NAMES]
    if len(x_coords) != 1:
        x_coords = [coord for coord in dim_coord_names if coord in X_COORD_NAMES]
        if len(x_coords) != 1:
            raise ValueError("Could not identify a unique x-coordinate in cube")

    # Check which y-coordinate we have, if any
    y_coords = [coord for coord in coord_names if coord in Y_COORD_NAMES]
    if len(y_coords) != 1:
        y_coords = [coord for coord in dim_coord_names if coord in Y_COORD_NAMES]
        if len(y_coords) != 1:
            raise ValueError("Could not identify a unique y-coordinate in cube")

    return (y_coords[0], x_coords[0])


def get_cube_coordindex(cube: iris.cube.Cube, coord_name) -> int:
    """
    Return coordinate dimension for a named coordinate from a given cube.

    Arguments
    ---------

    cube: iris.cube.Cube
        An iris cube which will be checked to see if it contains coordinate
        names that match a pre-defined list of acceptable horizontal
        coordinate names.

    coord_name: str
        A cube dimension name

    Returns
    -------
    coord_index
        An integer specifying where in the cube dimension list a specified coordinate name is found.

    Raises
    ------
    ValueError
        If a specified dimension coordinate cannot be found.
    """
    # Get a list of dimension coordinate names for the cube
    coord_names = [coord.name() for coord in cube.coords(dim_coords=True)]

    # Check if requested dimension is found in cube and get index
    if coord_name in coord_names:
        coord_index = cube.coord_dims(coord_name)[0]
    else:
        raise ValueError("Could not find requested dimension %s", coord_name)

    return coord_index


def is_spatialdim(cube: iris.cube.Cube) -> bool:
    """Determine whether a cube is has two spatial dimension coordinates.

    If cube has both spatial dims, it will contain two unique coordinates
    that explain space (latitude and longitude). The coordinates have to
    be iterable/contain usable dimension data, as cubes may contain these
    coordinates as scalar dimensions after being collapsed.

    Arguments
    ---------
    cube: iris.cube.Cube
        An iris cube which will be checked to see if it contains coordinate
        names that match a pre-defined list of acceptable coordinate names.

    Returns
    -------
    bool
        If true, then the cube has a spatial projection and thus can be plotted
        as a map.
    """
    # Acceptable horizontal coordinate names.
    X_COORD_NAMES = ["longitude", "grid_longitude", "projection_x_coordinate", "x"]
    Y_COORD_NAMES = ["latitude", "grid_latitude", "projection_y_coordinate", "y"]

    # Get a list of coordinate names for the cube
    coord_names = [coord.name() for coord in cube.dim_coords]
    x_coords = [coord for coord in coord_names if coord in X_COORD_NAMES]
    y_coords = [coord for coord in coord_names if coord in Y_COORD_NAMES]

    # If there is one coordinate for both x and y direction return True.
    if len(x_coords) == 1 and len(y_coords) == 1:
        return True
    else:
        return False


def is_transect(cube: iris.cube.Cube) -> bool:
    """Determine whether a cube is a transect.

    If cube is a transect, it will contain only one spatial (map) coordinate,
    and one vertical coordinate (either pressure or model level).

    Arguments
    ---------
    cube: iris.cube.Cube
        An iris cube which will be checked to see if it contains coordinate
        names that match a pre-defined list of acceptable coordinate names.

    Returns
    -------
    bool
        If true, then the cube is a transect that contains one spatial (map)
        coordinate and one vertical coordinate.
    """
    # Acceptable spatial (map) coordinate names.
    SPATIAL_MAP_COORD_NAMES = [
        "longitude",
        "grid_longitude",
        "projection_x_coordinate",
        "x",
        "latitude",
        "grid_latitude",
        "projection_y_coordinate",
        "y",
        "distance",
    ]

    # Acceptable vertical coordinate names
    VERTICAL_COORD_NAMES = ["pressure", "model_level_number", "level_height"]

    # Get a list of coordinate names for the cube
    coord_names = [coord.name() for coord in cube.coords(dim_coords=True)]

    # Check which spatial coordinates we have.
    spatial_coords = [
        coord for coord in coord_names if coord in SPATIAL_MAP_COORD_NAMES
    ]
    if len(spatial_coords) != 1:
        return False

    # Check which vertical coordinates we have.
    vertical_coords = [coord for coord in coord_names if coord in VERTICAL_COORD_NAMES]
    if len(vertical_coords) != 1:
        return False

    # Passed criteria so return True
    return True


def fully_equalise_attributes(cubes: iris.cube.CubeList):
    """Remove any unique attributes between cubes or coordinates in place."""
    # Equalise cube attributes.
    removed = iris.util.equalise_attributes(cubes)
    logging.debug("Removed attributes from cube: %s", removed)

    # Equalise coordinate attributes.
    coord_sets = [{coord.name() for coord in cube.coords()} for cube in cubes]

    all_coords = set.union(*coord_sets)
    coords_to_equalise = set.intersection(*coord_sets)
    coords_to_remove = set.difference(all_coords, coords_to_equalise)

    logging.debug("All coordinates: %s", all_coords)
    logging.debug("Coordinates to remove: %s", coords_to_remove)
    logging.debug("Coordinates to equalise: %s", coords_to_equalise)

    for coord in coords_to_remove:
        for cube in cubes:
            try:
                cube.remove_coord(coord)
                logging.debug("Removed coordinate %s from %s cube.", coord, cube.name())
            except iris.exceptions.CoordinateNotFoundError:
                pass

    for coord in coords_to_equalise:
        removed = iris.util.equalise_attributes([cube.coord(coord) for cube in cubes])
        logging.debug("Removed attributes from coordinate %s: %s", coord, removed)

    return cubes


def is_time_aggregatable(cube: iris.cube.Cube) -> bool:
    """Determine whether a cube can be aggregated in time.

    If a cube is aggregatable it will contain both a 'forecast_reference_time'
    and 'forecast_period' coordinate as dimensional coordinates.

    Arguments
    ---------
    cube: iris.cube.Cube
        An iris cube which will be checked to see if it is aggregatable based
        on a set of pre-defined dimensional time coordinates:
        'forecast_period' and 'forecast_reference_time'.

    Returns
    -------
    bool
        If true, then the cube is aggregatable and contains dimensional
        coordinates including both 'forecast_reference_time' and
        'forecast_period'.
    """
    # Acceptable time coordinate names for aggregatable cube.
    TEMPORAL_COORD_NAMES = ["forecast_period", "forecast_reference_time"]

    # Coordinate names for the cube.
    coord_names = [coord.name() for coord in cube.coords(dim_coords=True)]

    # Check which temporal coordinates we have.
    temporal_coords = [coord for coord in coord_names if coord in TEMPORAL_COORD_NAMES]
    # Return whether both coordinates are in the temporal coordinates.
    return len(temporal_coords) == 2
