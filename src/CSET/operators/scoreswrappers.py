# © Crown copyright, Met Office (2022-2026) and CSET contributors.
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

"""A module containing wrappers for the scores module."""

import logging

import iris
import numpy as np
import scores
import xarray as xr
from iris.cube import Cube

from CSET._common import is_increasing
from CSET.operators._utils import fully_equalise_attributes, get_cube_yxcoordname
from CSET.operators.misc import _extract_common_time_points
from CSET.operators.regrid import regrid_onto_cube


def _sort_cubes_for_verification(cubes: iris.cube.CubeList):
    """Prepare cubes ready for verification in scores.

    Parameters
    ----------
    cubes: iris.cube.CubeList
        A CubeList of exact 2 cubes, one from each model.

    Returns
    -------
    base: iris.cube.Cube
        The cube from the "analysis" in the same format as the other model.
    other: iris.cube.Cube
        The cube from the model in the same format as the base model.

    Raises
    ------
    ValueError: "cubes should contain exactly 2 cubes."
        If any other number of cubes are present.

    Notes
    -----
    This operators is used for sorting the data into the correct format. It
    is likely going to need to be refactored out of CSET and perhaps moved into
    `CSET._utils` given common code between here and `misc.differenece`.
    """
    # Set cubes into correct format using code from difference operator
    if len(cubes) != 2:
        raise ValueError("cubes should contain exactly 2 cubes.")
    base: Cube = cubes.extract_cube(iris.AttributeConstraint(cset_comparison_base=1))
    other: Cube = cubes.extract_cube(
        iris.Constraint(
            cube_func=lambda cube: "cset_comparison_base" not in cube.attributes
        )
    )

    # If cubes contain a pressure coordinate, ensure it is increasing.
    for cube in cubes:
        try:
            if len(cube.coord("pressure").points) > 2:
                if not is_increasing(cube.coord("pressure").points):
                    cube.data = np.flip(cube.data, axis=cube.coord_dims("pressure")[0])

        except iris.exceptions.CoordinateNotFoundError:
            pass

    # Get spatial coord names.
    base_lat_name, base_lon_name = get_cube_yxcoordname(base)
    other_lat_name, other_lon_name = get_cube_yxcoordname(other)

    # Ensure cubes to compare are on common differencing grid.
    # This is triggered if either
    #      i) latitude and longitude shapes are not the same. Note grid points
    #         are not compared directly as these can differ through rounding
    #         errors.
    #     ii) or variables are known to often sit on different grid staggering
    #         in different models (e.g. cell center vs cell edge), as is the case
    #         for UM and LFRic comparisons.
    # In future greater choice of regridding method might be applied depending
    # on variable type. Linear regridding can in general be appropriate for smooth
    # variables. Care should be taken with interpretation of differences
    # given this dependency on regridding.
    if (
        base.coord(base_lat_name).shape != other.coord(other_lat_name).shape
        or base.coord(base_lon_name).shape != other.coord(other_lon_name).shape
    ) or (
        base.long_name
        in [
            "eastward_wind_at_10m",
            "northward_wind_at_10m",
            "northward_wind_at_cell_centres",
            "eastward_wind_at_cell_centres",
            "zonal_wind_at_pressure_levels",
            "meridional_wind_at_pressure_levels",
            "potential_vorticity_at_pressure_levels",
            "vapour_specific_humidity_at_pressure_levels_for_climate_averaging",
        ]
    ):
        logging.debug(
            "Linear regridding base cube to other grid to compute differences"
        )
        base = regrid_onto_cube(base, other, method="Linear")

    # Figure out if we are comparing between UM and LFRic; flip array if so.
    base_lat_direction = is_increasing(base.coord(base_lat_name).points)
    other_lat_direction = is_increasing(other.coord(other_lat_name).points)
    if base_lat_direction != other_lat_direction:
        other.data = np.flip(other.data, other.coord(other_lat_name).cube_dims(other))

    # Extract just common time points.
    base, other = _extract_common_time_points(base, other)

    # Equalise attributes so we can merge.
    fully_equalise_attributes([base, other])
    logging.debug("Base: %s\nOther: %s", base, other)
    return base, other


def scores_rmse(
    cubes: iris.cube.CubeList, preserved_coordinates: list | str | None = None
):
    """Calculate the RMSE using scores."""
    base, other = _sort_cubes_for_verification(cubes)

    RMSE = xr.DataArray.to_iris(
        scores.continuous.rmse(
            xr.DataArray.from_iris(other),
            xr.DataArray.from_iris(base),
            preserve_coords=preserved_coordinates,
        )
    )
    RMSE.rename(f"RMSE_of_{base.name()}")
    return RMSE
