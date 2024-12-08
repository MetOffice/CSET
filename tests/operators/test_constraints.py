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

"""Test constraint operators."""

from datetime import datetime

import pytest

from CSET.operators import constraints


def test_generate_stash_constraint():
    """Generate iris cube constraint for UM STASH code."""
    stash_constraint = constraints.generate_stash_constraint("m01s03i236")
    expected_stash_constraint = "AttributeConstraint({'STASH': 'm01s03i236'})"
    assert repr(stash_constraint) == expected_stash_constraint


def test_generate_var_constraint():
    """Generate iris cube constraint for str variable name."""
    var_constraint = constraints.generate_var_constraint("test")
    expected_var_constraint = "Constraint(name='test')"
    assert repr(var_constraint) == expected_var_constraint


def test_generate_var_constraint_stash():
    """Generate iris cube constraint for UM STASH code with var constraint."""
    var_constraint = constraints.generate_var_constraint("m01s03i236")
    expected_stash_constraint = "AttributeConstraint({'STASH': 'm01s03i236'})"
    assert repr(var_constraint) == expected_stash_constraint


def test_generate_cell_methods_constraint():
    """Generate iris cube constraint for cell methods."""
    cell_methods_constraint = constraints.generate_cell_methods_constraint(["mean"])
    expected_cell_methods_constraint = "Constraint(cube_func=<function generate_cell_methods_constraint.<locals>.check_cell_methods at"
    assert expected_cell_methods_constraint in repr(cell_methods_constraint)


def test_generate_cell_methods_constraint_no_aggregation():
    """Generate iris cube constraint for no aggregation cell methods."""
    cell_methods_constraint = constraints.generate_cell_methods_constraint([])
    expected_cell_methods_constraint = "Constraint(cube_func=<function generate_cell_methods_constraint.<locals>.check_no_aggregation at"
    assert expected_cell_methods_constraint in repr(cell_methods_constraint)


def test_generate_time_constraint():
    """Generate iris cube constraint for dates."""
    # Try with str dates
    time_constraint = constraints.generate_time_constraint(
        "2023-03-24T00:00", "2023-03-24T06:00"
    )
    expected_time_constraint = "Constraint(coord_values={'time': <function generate_time_constraint.<locals>.<lambda> at "
    assert expected_time_constraint in repr(time_constraint)
    # Try with datetime.datetime dates
    time_constraint = constraints.generate_time_constraint(
        datetime.fromisoformat("2023-03-24T00:00:00+00:00"),
        datetime.fromisoformat("2023-03-24T06:00:00+00:00"),
    )
    assert expected_time_constraint in repr(time_constraint)
    # Try with implicit end
    time_constraint = constraints.generate_time_constraint("2023-03-24T00:00:00+00:00")
    assert expected_time_constraint in repr(time_constraint)


def test_generate_level_constraint_single_level():
    """Generate constraint for a single level."""
    pressure_constraint = constraints.generate_level_constraint(
        coordinate="pressure", levels=1000
    )
    expected_pressure_constraint = "Constraint(coord_values={'pressure': [1000]})"
    assert expected_pressure_constraint in repr(pressure_constraint)


def test_generate_level_constraint_multi_level():
    """Generate constraint for multiple pressure levels."""
    pressure_constraint = constraints.generate_level_constraint(
        coordinate="pressure", levels=[200, 800]
    )
    expected_pressure_constraint = "Constraint(coord_values={'pressure': [200, 800]})"
    assert expected_pressure_constraint in repr(pressure_constraint)


def test_generate_level_constraint_all_level():
    """Generate constraint for all levels."""
    pressure_constraint = constraints.generate_level_constraint(
        coordinate="pressure", levels="*"
    )
    expected_pressure_constraint = "Constraint(coord_values={'pressure': <function generate_level_constraint.<locals>.<lambda> at"
    assert expected_pressure_constraint in repr(pressure_constraint)


def test_generate_level_constraint_no_pressure():
    """Generate constraint for not having pressure levels."""
    pressure_constraint = constraints.generate_level_constraint(
        coordinate="pressure", levels=[]
    )
    expected_pressure_constraint = (
        "Constraint(cube_func=<function generate_level_constraint.<locals>.no_levels at"
    )
    assert expected_pressure_constraint in repr(pressure_constraint)


def test_generate_area_constraint():
    """Generate area constraint with lat-lon limits."""
    area_constraint = constraints.generate_area_constraint(0.0, 0.0, 0.1, 0.1)
    actual = repr(area_constraint)
    assert "Constraint(coord_values={" in actual
    assert (
        "'grid_latitude': <function generate_area_constraint.<locals>.bound_lat at 0x"
        in actual
    )
    assert (
        "'grid_longitude': <function generate_area_constraint.<locals>.bound_lon at 0x"
        in actual
    )


def test_generate_area_constraint_no_limits():
    """Generate area constraint with no limits."""
    area_constraint = constraints.generate_area_constraint(None, None, None, None)
    expected_area_constraint = "Constraint()"
    assert expected_area_constraint in repr(area_constraint)


def test_generate_area_constraint_invalid_arguments():
    """Generate area constraint raises exception with invalid arguments."""
    # Non-numbers are rejected.
    with pytest.raises(TypeError):
        constraints.generate_area_constraint(1, 2, 3, "four")

    # Mixed numbers and Nones are rejected.
    with pytest.raises(TypeError):
        constraints.generate_area_constraint(None, None, None, 0)


def test_combine_constraints():
    """Combine constraint."""
    stash_constraint = constraints.generate_stash_constraint("m01s03i236")
    var_constraint = constraints.generate_var_constraint("test")
    combined_constraint = constraints.combine_constraints(
        stash_constraint,
        a=var_constraint,
    )
    expected_combined_constraint = "ConstraintCombination(AttributeConstraint({'STASH': 'm01s03i236'}), Constraint(name='test'), <built-in function and_>)"
    assert repr(combined_constraint) == expected_combined_constraint
    var_constraint_2 = constraints.generate_var_constraint("test_2")
    combined_constraint = constraints.combine_constraints(
        stash_constraint,
        a=var_constraint,
        b=var_constraint_2,
    )
    expected_combined_constraint = "ConstraintCombination(ConstraintCombination(AttributeConstraint({'STASH': 'm01s03i236'}), Constraint(name='test'), <built-in function and_>), Constraint(name='test_2'), <built-in function and_>)"
    assert repr(combined_constraint) == expected_combined_constraint
