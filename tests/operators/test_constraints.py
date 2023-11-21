# Copyright 2022 Met Office and contributors.
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


def test_generate_model_level_constraint():
    """Generate iris cube constraint for model level number."""
    var_constraint = constraints.generate_model_level_constraint("2")
    expected_model_level_constraint = (
        "Constraint(coord_values={'model_level_number': 2})"
    )
    assert repr(var_constraint) == expected_model_level_constraint


def test_generate_cell_methods_constraint():
    """Generate iris cube constraint for cell methods."""
    cell_methods_constraint = constraints.generate_cell_methods_constraint([])
    expected_cell_methods_constraint = "Constraint(cube_func=<function generate_cell_methods_constraint.<locals>.check_cell_methods at"
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
