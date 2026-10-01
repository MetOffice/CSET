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


def make_cube(data, name, model_name=None):
    """Create a cube with a model_name attribute when requested."""
    cube = iris.cube.Cube(np.asarray(data, dtype=float), long_name=name)
    cube.rename(name)
    if model_name is not None:
        cube.attributes["model_name"] = model_name
    return cube


class TestMaskList:
    """Tests for the Nimrod mask selection helper."""

    def test_returns_empty_list_when_no_nimrod_source_present(self):
        """No Nimrod source should produce no mask names."""
        assert radar_filter.mask_list(["UM_model", "UKV_model"]) == []

    def test_prefers_highest_resolution_nimrod_source(self):
        """The preferred Nimrod weights should match the highest resolution source."""
        result = radar_filter.mask_list(["UM_model", "Nimrod1km", "Nimrod2km"])
        assert result == [
            "Nimrod2km_weights",
            "Nimrod1km_weights",
            "Nimrod2km_weights",
        ]


class TestMaskByWeights:
    """Tests for applying a radar weight mask to a field."""

    def test_applies_mask_using_weight_threshold(self):
        """Only cells with a valid Nimrod weight should remain in the field."""
        field = make_cube(np.arange(12, dtype=float).reshape(1, 3, 4), "rain_rate")
        field.attributes["model_name"] = "UM_model"

        mask_values = np.array(
            [
                [
                    [0.0, 11.0, 12.0, 4.0],
                    [13.0, 0.0, 5.0, 14.0],
                    [10.0, 11.0, 0.0, 21.0],
                ]
            ],
            dtype=float,
        )
        weights = make_cube(
            mask_values, "Nimrod2km_weights", model_name="Nimrod2km_weights"
        )

        result = radar_filter.mask_by_weights(
            iris.cube.CubeList([field, weights]),
            ["UM_model"],
            ["Nimrod2km_weights"],
        )

        expected = np.full((1, 3, 4), np.nan, dtype=float)
        valid = np.array(
            [
                [
                    [False, True, True, False],
                    [True, False, False, True],
                    [False, True, False, True],
                ]
            ],
            dtype=bool,
        )
        expected[valid] = field.data[valid]

        np.testing.assert_allclose(result.data, expected, equal_nan=True)


class TestRadarApplyMask:
    """Tests for the boundary-aware radar mask application."""

    def test_masks_boundary_points_and_applies_valid_mask(self):
        """Boundary cells and mask zeros should both become NaN."""
        field = make_cube(np.arange(120, dtype=float).reshape(1, 10, 12), "rain_rate")
        mask = make_cube(np.ones((1, 10, 12), dtype=float), "mask")

        result = radar_filter.radar_apply_mask(field, mask, boundary_margin=2)

        assert np.isnan(result.data[0, 0, 0])
        assert np.isnan(result.data[0, 9, 11])
        assert result.data[0, 2, 2] == 26.0
        assert result.data[0, 5, 5] == 65.0


class TestRadarMask:
    """Tests for masking radar and model data together."""

    def test_returns_masked_radar_cube(self):
        """Valid model points should propagate to the radar field output."""
        model_field = make_cube(
            np.arange(120, dtype=float).reshape(1, 10, 12), "model_field"
        )
        radar_field = make_cube(
            np.arange(120, 240, dtype=float).reshape(1, 10, 12), "radar_field"
        )
        mask = make_cube(np.ones((1, 10, 12), dtype=float), "nimrod_mask")

        result = radar_filter.radar_mask(
            model_field, radar_field, mask, boundary_margin=2, outputs="radar"
        )

        assert isinstance(result, iris.cube.Cube)
        assert np.isnan(result.data[0, 0, 0])
        assert np.isnan(result.data[0, 9, 11])
        assert result.data[0, 2, 2] == 146.0

    def test_returns_both_model_and_radar_cubes_for_all_output(self):
        """The all-output mode should return both model and radar cubes."""
        model_field = make_cube(
            np.arange(120, dtype=float).reshape(1, 10, 12), "model_field"
        )
        radar_field = make_cube(
            np.arange(120, 240, dtype=float).reshape(1, 10, 12), "radar_field"
        )
        mask = make_cube(np.ones((1, 10, 12), dtype=float), "nimrod_mask")

        result = radar_filter.radar_mask(
            model_field, radar_field, mask, boundary_margin=2, outputs="all"
        )

        assert isinstance(result, iris.cube.CubeList)
        assert len(result) == 2
        assert result[0].name() == "model_field"
        assert result[1].name() == "radar_field"


def test_handles_multiple_field_and_mask_cubes():
    """Test the loop over both the mask and rainfall fields."""
    field1 = make_cube(np.ones((1, 3, 3), dtype=float), "field_a")
    field2 = make_cube(np.full((1, 3, 3), 2.0, dtype=float), "field_b")

    mask1 = make_cube(np.ones((1, 3, 3), dtype=float), "mask_a")
    mask2 = make_cube(np.ones((1, 3, 3), dtype=float), "mask_b")

    result = radar_filter.radar_apply_mask(
        iris.cube.CubeList([field1, field2]),
        iris.cube.CubeList([mask1, mask2]),
        boundary_margin=0,
    )

    assert isinstance(result, iris.cube.CubeList)
    assert len(result) == 2
    assert np.allclose(result[0].data, 1.0)
    assert np.allclose(result[1].data, 2.0)


def test_returns_masked_model_cube_when_output_is_model():
    """Test the branch that executes if just model output is required."""
    model_field = make_cube(
        np.arange(120, dtype=float).reshape(1, 10, 12), "model_field"
    )
    radar_field = make_cube(
        np.arange(120, 240, dtype=float).reshape(1, 10, 12), "radar_field"
    )
    mask = make_cube(np.ones((1, 10, 12), dtype=float), "nimrod_mask")

    result = radar_filter.radar_mask(
        model_field, radar_field, mask, boundary_margin=2, outputs="model"
    )

    assert isinstance(result, iris.cube.Cube)
    assert result.name() == "model_field"
    assert np.isnan(result.data[0, 0, 0])


def test_radar_mask_loop_returns_model_and_radar_outputs():
    """Test the loop over all models."""
    model_field = iris.cube.CubeList(
        [
            make_cube(np.ones((1, 3, 3), dtype=float), "model_1"),
            make_cube(np.full((1, 3, 3), 2.0, dtype=float), "model_2"),
        ]
    )
    radar_field = make_cube(np.full((1, 3, 3), 9.0, dtype=float), "radar_field")
    mask = make_cube(np.ones((1, 3, 3), dtype=float), "nimrod_mask")

    result = radar_filter.radar_mask_loop(
        model_field,
        radar_field,
        mask,
        boundary_margin=0,
        outputs="radar",
    )

    assert isinstance(result, iris.cube.CubeList)
    assert len(result) >= 2


def test_boundary_margin_zero_keeps_all_inner_points():
    """Test zero width boundary on model field."""
    field = make_cube(np.arange(9, dtype=float).reshape(1, 3, 3), "rain_rate")
    mask = make_cube(np.ones((1, 3, 3), dtype=float), "mask")

    result = radar_filter.radar_apply_mask(field, mask, boundary_margin=0)

    assert np.all(np.isfinite(result.data))


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
    new_data = np.array([[[11.0, 12.0, 13.0], [14.0, 15.0, 16.0], [17.0, 18.0, 19.0]]])
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


def test_radar_apply_mask(cube_model, cube_radar_wts):
    """Test the mask_by_weights function."""
    masked = radar_filter.radar_apply_mask(
        cube_model, cube_radar_wts, boundary_margin=0
    )
    print()
    print("---->masked from test_radar_apply_mask", masked)
    print()
    print("----> masked.data ", masked.data)


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
