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

import cf_units
import iris.cube
import numpy as np
import pytest

from CSET.operators import aggregate, constraints, filters, read

constraint_single = constraints.combine_constraints(
    constraints.generate_stash_constraint("m01s03i236"),
    a=constraints.generate_cell_methods_constraint([]),
)


def test_filter_cubes_cubelist(cubes):
    """Test filtering a CubeList."""
    constraint = constraints.generate_cell_methods_constraint([])
    cube = filters.filter_cubes(cubes, constraint)
    assert cube.cell_methods == ()
    expected_cube = "<iris 'Cube' of air_temperature / (K) (time: 3; grid_latitude: 17; grid_longitude: 13)>"
    assert repr(cube) == expected_cube


def test_filter_cubes_cubelist_per_model(cube):
    """Test filtering a CubeList with multiple models."""
    constraint = constraints.generate_cell_methods_constraint([])
    model1 = cube.copy()
    model1.attributes["model_name"] = "model_1"
    model2 = cube.copy()
    model2.attributes["model_name"] = "model_2"

    cube = filters.filter_cubes(
        iris.cube.CubeList([model1, model2]), constraint, per_model=True
    )

    expected_cube = "<iris 'Cube' of air_temperature / (K) (time: 3; grid_latitude: 17; grid_longitude: 13)>"
    assert [repr(c) for c in cube] == [expected_cube, expected_cube]

    model1.attributes.pop("model_name")
    with pytest.raises(ValueError):
        filters.filter_cubes(
            iris.cube.CubeList([model1, model2]), constraint, per_model=True
        )


def test_filter_cubes_cube(cube):
    """Test filtering a Cube."""
    constraint = constraints.generate_cell_methods_constraint([])
    single_cube = filters.filter_cubes(cube, constraint)
    assert repr(cube) == repr(single_cube)


def test_filter_cubes_single_cube_per_model(cube):
    """Test filtering a single Cube in per_model mode."""
    constraint = constraints.generate_cell_methods_constraint([])
    cube = cube.copy()
    cube.attributes["model_name"] = "model_1"
    returned_cubes = filters.filter_cubes(cube, constraint, per_model=True)
    assert isinstance(returned_cubes, iris.cube.CubeList)
    assert len(returned_cubes) == 1
    assert repr(cube) == repr(returned_cubes[0])


def test_filter_cubes_single_entry_cubelist_per_model(cube):
    """Test filtering a CubeList with one entry in per_model mode."""
    constraint = constraints.generate_cell_methods_constraint([])
    cube = cube.copy()
    cube.attributes["model_name"] = "model_1"
    returned_cubes = filters.filter_cubes(
        iris.cube.CubeList((cube,)), constraint, per_model=True
    )
    assert isinstance(returned_cubes, iris.cube.CubeList)
    assert len(returned_cubes) == 1
    assert repr(cube) == repr(returned_cubes[0])


def test_filter_cubes_multiple_returned_exception(cubes):
    """Test for exception when multiple cubes returned."""
    constraint = constraints.generate_stash_constraint("m01s03i236")
    with pytest.raises(ValueError):
        filters.filter_cubes(cubes, constraint)


def test_filter_cubes_no_level_coord(cube):
    """Test a cube without the level coordinate is passed through."""
    pressure_constraint = constraints.generate_level_constraint(
        coordinate="pressure", levels=[]
    )
    assert filters.filter_cubes(cube, pressure_constraint)


def test_filter_cubes_no_level_coord_none_returned(cube):
    """Test exception when pressure coordinate is excluded."""
    pressure_constraint = constraints.generate_level_constraint(
        coordinate="pressure", levels=[]
    )
    cube.add_aux_coord(iris.coords.DimCoord(100, var_name="pressure"))
    with pytest.raises(ValueError):
        filters.filter_cubes(cube, pressure_constraint)


def test_filter_multiple_cubes(cubes):
    """Test to a CubeList of a single Cube."""
    filtered_cubes = filters.filter_multiple_cubes(cubes, c=constraint_single)
    assert isinstance(filtered_cubes, iris.cube.CubeList)
    assert len(filtered_cubes) == 1
    assert filtered_cubes[0].cell_methods == ()


def test_filter_multiple_cubes_single_cube(cube):
    """Test filtering a Cube."""
    filtered_cube = filters.filter_multiple_cubes(cube, c=constraint_single)
    assert isinstance(filtered_cube, iris.cube.CubeList)
    assert len(filtered_cube) == 1


def test_filter_multiple_cubes_multiple_out(cubes):
    """Test filtering for multiple Cubes."""
    constraint_single_2 = constraints.combine_constraints(
        constraints.generate_stash_constraint("m01s03i236"),
        a=constraints.generate_cell_methods_constraint(
            cell_methods=["minimum"], coord="time", interval="1 hour"
        ),
    )
    filtered_multi_cubes = filters.filter_multiple_cubes(
        cubes, c1=constraint_single, c2=constraint_single_2
    )
    assert len(filtered_multi_cubes) == 2


def test_filter_multiple_cubes_no_constraint_exception(cubes):
    """Test exception when no constraints given."""
    with pytest.raises(ValueError):
        filters.filter_multiple_cubes(cubes)


def test_filter_multiple_cubes_none_returned(cubes):
    """Test exception when no Cubes returned."""
    constraint_none = constraints.generate_stash_constraint("m01s01i001")
    with pytest.raises(ValueError):
        filters.filter_multiple_cubes(cubes, c=constraint_none)


# Session scope fixtures, so the test data only has to be loaded once.
@pytest.fixture(scope="session")
def load_vertical_coord_cubelist() -> iris.cube.CubeList:
    """Get a cubelist with multiple vertical level cubes."""
    return read.read_cubes("tests/test_data/vertlevtestdata.nc", "y_wind")


def test_generate_level_constraint_return_single_level(load_vertical_coord_cubelist):
    """For a cubelist that contains 3 cubes on different vertical levels.

    Return one without a vertical coordinate.
    """
    constraint_1 = constraints.generate_level_constraint(
        coordinate="pressure", levels=[]
    )
    constraint_2 = constraints.generate_level_constraint(
        coordinate="model_level_number", levels=[]
    )
    combined = constraints.combine_constraints(constraint_1, a=constraint_2)
    cube = load_vertical_coord_cubelist.extract_cube(combined)
    coords = [coord.name() for coord in cube.coords()]
    assert "pressure" not in coords
    assert "model_level_number" not in coords


def test_generate_level_constraint_return_all_pressure(load_vertical_coord_cubelist):
    """For a cubelist that contains 3 cubes on different vertical levels.

    Return one with a pressure on all levels.
    """
    constraint = constraints.generate_level_constraint(
        coordinate="pressure", levels="*"
    )
    coord = load_vertical_coord_cubelist.extract_cube(constraint).coord("pressure")
    assert coord.shape == (34,)


def test_generate_level_constraint_return_all_model_levels(
    load_vertical_coord_cubelist,
):
    """For a cubelist that contains 3 cubes on different vertical levels.

    Return one with a model level on all levels.
    """
    constraint = constraints.generate_level_constraint(
        coordinate="model_level_number", levels="*"
    )
    coord = load_vertical_coord_cubelist.extract_cube(constraint).coord(
        "model_level_number"
    )
    assert coord.shape == (70,)


def test_generate_mask_fail_wrong_condition(cube):
    """Fails for a wrong condition."""
    with pytest.raises(ValueError):
        filters.generate_mask(cube, "!<", 10)


def test_generate_mask_rename(cube):
    """Generates a mask and checks rename."""
    expected = f"mask_for_{cube.name()}_eq_276"
    assert filters.generate_mask(cube, "eq", 276).name() == expected


def test_generate_mask_units(cube):
    """Generates a mask and checks units."""
    expected = cf_units.Unit("1")
    assert filters.generate_mask(cube, "eq", 276).units == expected


def test_generate_mask_equal_to(cube):
    """Generates a mask with values equal to a specified value."""
    mask = cube.copy()
    mask.data = np.zeros(mask.data.shape)
    mask.data[cube.data == 276] = 1.0
    assert np.allclose(
        filters.generate_mask(cube, "eq", 276).data,
        mask.data,
        rtol=1e-06,
        atol=1e-02,
    )


def test_generate_mask_not_equal_to(cube):
    """Generates a mask with values not equal to a specified value."""
    mask = cube.copy()
    mask.data = np.zeros(mask.data.shape)
    mask.data[cube.data != 276] = 1.0
    assert np.allclose(
        filters.generate_mask(cube, "ne", 276).data,
        mask.data,
        rtol=1e-06,
        atol=1e-02,
    )


def test_generate_mask_greater_than(cube):
    """Generates a mask with values greater than a specified value."""
    mask = cube.copy()
    mask.data = np.zeros(mask.data.shape)
    mask.data[cube.data > 276] = 1.0
    assert np.allclose(
        filters.generate_mask(cube, "gt", 276).data,
        mask.data,
        rtol=1e-06,
        atol=1e-02,
    )


def test_generate_mask_greater_equal_to(cube):
    """Generates a mask with values greater than or equal to a specified value."""
    mask = cube.copy()
    mask.data = np.zeros(mask.data.shape)
    mask.data[cube.data >= 276] = 1.0
    assert np.allclose(
        filters.generate_mask(cube, "ge", 276).data,
        mask.data,
        rtol=1e-06,
        atol=1e-02,
    )


def test_generate_mask_less_than(cube):
    """Generates a mask with values less than a specified value."""
    mask = cube.copy()
    mask.data = np.zeros(mask.data.shape)
    mask.data[cube.data < 276] = 1.0
    assert np.allclose(
        filters.generate_mask(cube, "lt", 276).data,
        mask.data,
        rtol=1e-06,
        atol=1e-02,
    )


def test_generate_mask_less_equal_to(cube):
    """Generates a mask with values less than or equal to a specified value."""
    mask = cube.copy()
    mask.data = np.zeros(mask.data.shape)
    mask.data[cube.data <= 276] = 1.0
    assert np.allclose(
        filters.generate_mask(cube, "le", 276).data,
        mask.data,
        rtol=1e-06,
        atol=1e-02,
    )


def test_generate_mask_cube_list(cubes):
    """Generates masks for a cubelist."""
    masks = filters.generate_mask(cubes, "le", 276)
    assert isinstance(masks, iris.cube.CubeList)
    masks_calc = iris.cube.CubeList([])
    for cube in cubes:
        mask = cube.copy()
        mask.data[:] = 0.0
        mask.data[cube.data <= 276] = 1.0
        masks_calc.append(mask)
    for cube, mask in zip(masks, masks_calc, strict=True):
        assert np.allclose(cube.data, mask.data, rtol=1e-06, atol=1e-02)


def test_apply_mask(cube):
    """Apply a mask to a cube."""
    mask = filters.generate_mask(cube, "eq", 276)
    mask.data[mask.data == 0.0] = np.nan
    mask.data[~np.isnan(mask.data)] = 1.0
    test_data = cube.copy()
    test_data.data *= mask.data
    assert np.allclose(
        filters.apply_mask(cube, mask).data,
        test_data.data,
        rtol=1e-06,
        atol=1e-02,
        equal_nan=True,
    )


def test_apply_mask_cubelist(cube):
    """Apply a mask to a cube list."""
    mask = filters.generate_mask(cube, "eq", 276)
    mask.data[mask.data == 0.0] = np.nan
    mask.data[~np.isnan(mask.data)] = 1.0
    test_data = cube.copy()
    test_data.data *= mask.data
    expected_list = iris.cube.CubeList([test_data, test_data])
    mask_list = iris.cube.CubeList([mask, mask])
    input_list = iris.cube.CubeList([cube, cube])
    actual_cubelist = filters.apply_mask(input_list, mask_list)
    for cube, mask in zip(expected_list, actual_cubelist, strict=True):
        assert np.allclose(cube.data, mask.data, rtol=1e-06, atol=1e-02, equal_nan=True)


def test_generate_single_ensemble_member_constraint_reduced_member(ensemble_cube):
    """Remove a single ensemble member from a cube."""
    remove_member_constraint = (
        constraints.generate_remove_single_ensemble_member_constraint(ensemble_member=1)
    )
    filter_cube = filters.filter_cubes(
        ensemble_cube, constraint=remove_member_constraint
    )
    # Assert one of the ensemble members have been removed.
    assert len(filter_cube.coord("realization").points) == (
        len(ensemble_cube.coord("realization").points) - 1
    )
    # Assert remain ensemble member is expected one.
    assert filter_cube.coord("realization").points == [2]


def test_generate_realization_constraint_single_member(ensemble_cube):
    """Select a single ensemble member from a cube."""
    single_member_constraint = constraints.generate_realization_constraint(
        ensemble_members=1
    )
    filter_cube = filters.filter_cubes(
        ensemble_cube, constraint=single_member_constraint
    )
    # Assert filtered realization coordinate matches expected coordinate point.
    assert filter_cube.coord("realization").points == [1]


def test_generate_realization_constraint_multiple_members(ensemble_cube):
    """Select multiple ensemble members from a cube."""
    multi_member_constraint = constraints.generate_realization_constraint(
        ensemble_members=[1, 2]
    )
    filter_cube = filters.filter_cubes(
        ensemble_cube, constraint=multi_member_constraint
    )
    # Assert filtered realization coordinates match expected realization coordinates.
    assert (filter_cube.coord("realization").points == [1, 2]).all()


def test_generate_hour_constraint_single_hour(cube):
    """Select a single hour of day from cube."""
    new_cube = aggregate.add_hour_coordinate(cube)
    expected_cube = filters.filter_cubes(
        new_cube, constraints.generate_hour_constraint(hour_start=3)
    )
    assert expected_cube.coord("hour").points == [3]


def test_generate_hour_constraint_hour_range(cube):
    """Select hours of day within a given range."""
    new_cube = aggregate.add_hour_coordinate(cube)
    expected_cube = filters.filter_cubes(
        new_cube, constraints.generate_hour_constraint(hour_start=3, hour_end=4)
    )
    assert (expected_cube.coord("hour").points == [3, 4]).all()
