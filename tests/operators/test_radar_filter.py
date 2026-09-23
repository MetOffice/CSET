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

"""Test filter operators."""

import iris
import numpy as np
from iris.cube import Cube

from CSET.operators import constraints, radar_filter

constraint_single = constraints.combine_constraints(
    constraints.generate_stash_constraint("m01s03i236"),
    a=constraints.generate_cell_methods_constraint([]),
)


def test_mask_list():
    """Test the mask_list function."""
    list_weights = radar_filter.mask_list(["UM_model", "Nimrod1km", "Nimrod2km"])
    expected_list = ["Nimrod2km_weights", "Nimrod1km_weights", "Nimrod2km_weights"]
    assert list_weights == expected_list


def test_mask_by_weights():
    """Test the mask_by_weights function."""
    obs = Cube([[1.0, 2.0], [3.0, 4.0]])
    wts = Cube([[13, 0], [10, 11]])
    out = Cube([[1.0, np.nan], [np.nan, 4.0]])

    var_name_obs = "hourly_rain_accumulation"
    var_name_wts = "hourly_wts_accumulation"

    obs_name = "Radar"
    wts_name = "Radar_wts"
    obs.attributes["model_name"] = obs_name
    wts.attributes["model_name"] = wts_name

    obs.rename(var_name_obs)
    obs.long_name = var_name_obs
    obs.var_name = var_name_obs

    wts.rename(var_name_wts)
    wts.long_name = var_name_wts
    wts.var_name = var_name_wts

    cube_list = iris.cube.CubeList([])
    cube_list.append(obs)
    cube_list.append(wts)

    masked = radar_filter.mask_by_weights(cube_list, [obs_name], [wts_name])
    assert np.array_equal(masked.data, out.data, equal_nan=True)


def test_match_varname_and_units():
    """Test the match_varname_and_units function."""
    var_name_cube1 = "surface_microphysical_rainfall_rate"
    var_name_cube3 = "Hourly rain accumulation"

    units_cube1 = "mm hr-1"
    units_cube3 = "mm"

    # Construct test_cube1.
    shape = (5, 4, 4)
    data = np.ones(shape, dtype=np.float32)

    lat_coord = iris.coords.DimCoord(
        np.linspace(-90, 90, 4), standard_name="latitude", units="degrees"
    )
    lon_coord = iris.coords.DimCoord(
        np.linspace(-180, 180, 4), standard_name="longitude", units="degrees"
    )

    time_points1 = np.array([0, 6, 12, 18, 24], dtype=np.float64)
    time_coord1 = iris.coords.DimCoord(
        time_points1,
        standard_name="time",
        units="hours since 2026-09-23 00:00:00",
    )

    fp_coord1 = iris.coords.DimCoord(
        time_points1, standard_name="forecast_period", units="hours"
    )

    test_cube1 = iris.cube.Cube(
        data,
        long_name=var_name_cube1,
        units=units_cube1,
        dim_coords_and_dims=[
            (time_coord1, 0),
            (lat_coord, 1),
            (lon_coord, 2),
        ],
    )

    test_cube1.add_aux_coord(fp_coord1, data_dims=0)

    frt_coord1 = iris.coords.AuxCoord(
        [0.0],
        standard_name="forecast_reference_time",
        units="hours since 2026-09-23 00:00:00",
    )
    test_cube1.add_aux_coord(frt_coord1)

    # Construct test_cube2.
    test_cube2 = test_cube1.copy()

    # Construct test_cube3.
    time_points3 = np.array([3, 9, 15, 21, 27], dtype=np.float64)

    time_coord3 = iris.coords.DimCoord(
        time_points3,
        standard_name="time",
        units="hours since 2026-09-23 00:00:00",
    )

    fp_coord3 = iris.coords.DimCoord(
        time_points3, standard_name="forecast_period", units="hours"
    )

    test_cube3 = iris.cube.Cube(
        data,
        long_name=var_name_cube3,
        units=units_cube3,
        dim_coords_and_dims=[
            (time_coord3, 0),
            (lat_coord, 1),
            (lon_coord, 2),
        ],
    )

    test_cube3.add_aux_coord(fp_coord3, data_dims=0)

    frt_coord3 = iris.coords.AuxCoord(
        [1.0],
        standard_name="forecast_reference_time",
        units="hours since 2026-09-23 00:00:00",
    )
    test_cube3.add_aux_coord(frt_coord3)

    print(" ")
    print("-----> test_cube1 ", test_cube1)
    print(" ")
    print("-----> test_cube3 ", test_cube3)

    ########

    # Construct the CubeList to test.
    cube_list = iris.cube.CubeList([])
    cube_list.append(test_cube1)
    cube_list.append(test_cube2)
    cube_list.append(test_cube3)

    # Push the test CubeList through the function match_varname_and_units.
    cubes_matched = radar_filter.match_varname_and_units(cube_list)

    assert cubes_matched[0].var_name == cubes_matched[1].var_name
    assert cubes_matched[0].var_name == cubes_matched[2].var_name

    assert cubes_matched[0].long_name == cubes_matched[1].long_name
    assert cubes_matched[0].long_name == cubes_matched[2].long_name

    assert cubes_matched[0].units == cubes_matched[1].units
    assert cubes_matched[0].units == cubes_matched[2].units

    assert cubes_matched[0].coord("forecast_reference_time") == cubes_matched[1].coord(
        "forecast_reference_time"
    )
    assert cubes_matched[0].coord("forecast_reference_time") == cubes_matched[2].coord(
        "forecast_reference_time"
    )

    assert cubes_matched[0].coord("forecast_period") == cubes_matched[1].coord(
        "forecast_period"
    )
    assert cubes_matched[0].coord("forecast_period") == cubes_matched[2].coord(
        "forecast_period"
    )

    print(" ")
    print("-----> cubes_matched[2] ", cubes_matched[2])


# def test_radar_apply_mask():
#    """Test the radar_apply_mask function."""
#    obs = Cube([0,[[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]]])
#    #wts = Cube([[13, 0, 13], [9, 12, 11], [13, 11, 10]])
#    msk = Cube([0,[[1, np.nan, 1], [np.nan, 1, 1], [1, 1, 1]]])
#
#    var_name_obs = "hourly_rain_accumulation"
#    var_name_msk = "hourly_wts_accumulation"
#
#    obs_name = "Radar"
#    msk_name = "Radar_msk"
#    obs.attributes["model_name"] = obs_name
#    msk.attributes["model_name"] = msk_name
#
#    obs.rename(var_name_obs)
#    obs.long_name = var_name_obs
#    obs.var_name = var_name_obs
#
#    msk.rename(var_name_msk)
#    msk.long_name = var_name_msk
#    msk.var_name = var_name_msk
#
#    masked = radar_filter.radar_apply_mask(obs, msk, boundary_margin = 1)
