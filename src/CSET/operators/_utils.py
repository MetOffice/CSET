# Copyright 2022-2024 Met Office and contributors.
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

import iris
import iris.cube


def get_cube_yxcoordname(cube: iris.cube.Cube) -> tuple[str, str]:
    """
    Return horizontal coordinate name(s) from a given cube.

    Arguments
    ---------

    cube: iris.cube.Cube
        An iris cube which will be checked to see if it contains coordinate
        names that match a pre-defined list of acceptable horizontal
        coordinate names.

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

    # Get a list of coordinate names for the cube
    coord_names = [coord.name() for coord in cube.coords()]

    # Check which x-coordinate we have, if any
    x_coords = [coord for coord in coord_names if coord in X_COORD_NAMES]
    if len(x_coords) != 1:
        raise ValueError("Could not identify a unique x-coordinate in cube")

    # Check which y-coordinate we have, if any
    y_coords = [coord for coord in coord_names if coord in Y_COORD_NAMES]
    if len(y_coords) != 1:
        raise ValueError("Could not identify a unique y-coordinate in cube")

    return (y_coords[0], x_coords[0])


def _is_transect(cube: iris.cube.Cube) -> bool:
    """
    Determine whether a cube is a transect.

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
    VERTICAL_COORD_NAMES = ["pressure", "model_level_number"]

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
