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
import pytest

from CSET.operators import constraints, radar_filter

constraint_single = constraints.combine_constraints(
    constraints.generate_stash_constraint("m01s03i236"),
    a=constraints.generate_cell_methods_constraint([]),
)


# Session scope fixtures, so the test data only has to be loaded once.
@pytest.fixture(scope="session")
def cube_radar() -> iris.cube.Cube:
    """Construct a radar rainfall accumulation cube."""
    shape = (1, 3, 3)
    data = np.ones(shape, dtype=np.float32)

    lat_coord = iris.coords.DimCoord(
        np.linspace(-90, 90, 3), standard_name="latitude", units="degrees"
    )
    lon_coord = iris.coords.DimCoord(
        np.linspace(-180, 180, 3), standard_name="longitude", units="degrees"
    )

    time_points = np.array([3], dtype=np.float64)
    time_coord = iris.coords.DimCoord(
        time_points,
        standard_name="time",
        units="hours since 2026-09-23 00:00:00",
    )

    fp_coord = iris.coords.DimCoord(
        time_points, standard_name="forecast_period", units="hours"
    )

    test_cube = iris.cube.Cube(
        data,
        long_name="Hourly rain accumulation",
        units="mm",
        dim_coords_and_dims=[
            (time_coord, 0),
            (lat_coord, 1),
            (lon_coord, 2),
        ],
    )

    test_cube.add_aux_coord(fp_coord, data_dims=0)

    frt_coord = iris.coords.AuxCoord(
        [0.0],
        standard_name="forecast_reference_time",
        units="hours since 2026-09-23 00:00:00",
    )
    test_cube.add_aux_coord(frt_coord)

    test_cube.attributes["model_name"] = "RadarA"

    new_data = np.array([[[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]]])
    test_cube.data = new_data

    return test_cube


@pytest.fixture(scope="session")
def cube_radar_wts(cube_radar) -> iris.cube.Cube:
    """Construct a radar rainfall accumulation weights cube."""
    test_cube = cube_radar.copy()
    new_data = np.array([[[13, 0, 13], [9, 12, 11], [13, 11, 10]]])
    test_cube.data = new_data
    test_cube.attributes["model_name"] = "RadarA_wts"
    test_cube.long_name = "Hourly wts accumulation"
    test_cube.units = "1"
    return test_cube


@pytest.fixture(scope="session")
def cube_radar_masked_by_wts(cube_radar) -> iris.cube.Cube:
    """Construct a radar rainfall accumulation cube that has been masked by the weights."""
    test_cube = cube_radar.copy()
    new_data = np.array([[[1.0, np.nan, 3.0], [np.nan, 5.0, 6.0], [7.0, 8.0, np.nan]]])
    test_cube.data = new_data
    test_cube.attributes["mask"] = "mask_of_" + test_cube.long_name
    return test_cube


@pytest.fixture(scope="session")
def cube_model(cube_radar) -> iris.cube.Cube:
    """Construct a model rainfall rate cube."""
    test_cube = cube_radar.copy()
    new_data = np.array([[[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]]])
    test_cube.data = new_data
    test_cube.attributes["model_name"] = "ModelA"
    test_cube.long_name = "surface_microphysical_rainfall_rate"
    test_cube.units = "mm hr-1"
    return test_cube


def test_print_cube_radar(cube_radar):
    """Print the radar cube."""
    print("----> cube_radar ", cube_radar)
    print()
    print("----> cube_radar.data ", cube_radar.data)
    print()
    print(
        '----> cube_radar.attributes["model_name"] ',
        cube_radar.attributes["model_name"],
    )


def test_print_cube_radar_mask(cube_radar_wts):
    """Print the radar wts cube."""
    print("----> cube_radar_wts ", cube_radar_wts)
    print()
    print("----> cube_radar_wts.data ", cube_radar_wts.data)


def test_print_cube_radar_masked_by_wts(cube_radar_masked_by_wts):
    """Print the radar masked by wts cube."""
    print("----> cube_radar_masked_by_wts ", cube_radar_masked_by_wts)
    print()
    print("----> cube_radar_masked_by_wts.data ", cube_radar_masked_by_wts.data)


def test_mask_list():
    """Test the mask_list function."""
    list_weights = radar_filter.mask_list(["UM_model", "Nimrod1km", "Nimrod2km"])
    expected_list = ["Nimrod2km_weights", "Nimrod1km_weights", "Nimrod2km_weights"]
    assert list_weights == expected_list


def test_mask_by_weights(cube_radar, cube_radar_wts, cube_radar_masked_by_wts):
    """Test the mask_by_weights function."""
    obs_name = cube_radar.attributes["model_name"]
    wts_name = cube_radar_wts.attributes["model_name"]
    cube_list = iris.cube.CubeList([])
    cube_list.append(cube_radar)
    cube_list.append(cube_radar_wts)
    masked = radar_filter.mask_by_weights(cube_list, [obs_name], [wts_name])
    print()
    print("---->masked ", masked)
    print()
    print("----> masked.data ", masked.data)
    assert np.array_equal(masked.data, cube_radar_masked_by_wts.data, equal_nan=True)


def test_match_varname_and_units(cube_model, cube_radar):
    """Test the match_varname_and_units function."""
    cube1 = cube_model.copy()
    cube2 = cube_model.copy()
    cube3 = cube_radar.copy()

    # Construct the CubeList to test.
    cube_list = iris.cube.CubeList([])
    cube_list.append(cube1)
    cube_list.append(cube2)
    cube_list.append(cube3)

    # Push the test CubeList through the function match_varname_and_units.
    cubes_matched = radar_filter.match_varname_and_units(cube_list)

    assert cubes_matched[0].var_name == cubes_matched[1].var_name
    assert cubes_matched[0].var_name == cubes_matched[2].var_name

    assert cubes_matched[0].long_name == cubes_matched[1].long_name
    assert cubes_matched[0].long_name == cubes_matched[2].long_name

    assert cubes_matched[0].units == cubes_matched[1].units
    assert cubes_matched[0].units == cubes_matched[2].units


def test_match_varname_and_units_single_cube(cube_model):
    """Test the match_varname_and_units function."""
    cube1 = cube_model.copy()

    # Push the test Cube through the function match_varname_and_units.
    cubes_matched = radar_filter.match_varname_and_units(cube1)

    assert cubes_matched.var_name == cube1.var_name
    assert cubes_matched.long_name == cube1.long_name
    assert cubes_matched.units == cube1.units


def test_match_varname_and_units_single_cube_in_cubelist(cube_model):
    """Test the match_varname_and_units function."""
    cube1 = cube_model.copy()

    # Construct the CubeList to test.
    cube_list = iris.cube.CubeList([])
    cube_list.append(cube1)

    # Push the test CubeList through the function match_varname_and_units.
    cubes_matched = radar_filter.match_varname_and_units(cube_list)

    assert cubes_matched[0].var_name == cube_model.var_name
    assert cubes_matched[0].long_name == cube_model.long_name
    assert cubes_matched[0].units == cube_model.units


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
