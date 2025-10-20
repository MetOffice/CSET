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

from datetime import datetime, timedelta

import pytest
from iris.time import PartialDateTime

from CSET.operators import constraints


def test_my_pdt_fromstring_returns_pdt():
    """Output of the constraints.my_pdt_fromstring() function is a PartialDateTime."""
    pdt, offset = constraints.my_pdt_fromstring("2022-01-01")
    assert isinstance(pdt, PartialDateTime)
    assert offset is None


def test_year_month_day_parse_correctly():
    """The constraints.my_pdt_fromstring() function correctly parses out the year, month, day coordinates."""
    pdt, offset = constraints.my_pdt_fromstring("2022-01-01")
    assert pdt.year == 2022
    assert pdt.month == 1
    assert pdt.day == 1
    assert pdt.hour == 0
    assert pdt.minute == 0
    assert pdt.second == 0
    assert offset is None


def test_hour_parse_correctly():
    """The constraints.my_pdt_fromstring() function correctly parses out only the hour coordinate."""
    pdt, offset = constraints.my_pdt_fromstring("2022-01-01T12")
    assert pdt.year == 2022
    assert pdt.month == 1
    assert pdt.day == 1
    assert pdt.hour == 12
    assert pdt.minute == 0
    assert pdt.second == 0
    assert offset is None


def test_hour_minute_parse_correctly():
    """The constraints.my_pdt_fromstring() function correctly parses out only the hour and minute coordinate."""
    pdt, offset = constraints.my_pdt_fromstring("2022-01-01T12:30")
    assert pdt.year == 2022
    assert pdt.month == 1
    assert pdt.day == 1
    assert pdt.hour == 12
    assert pdt.minute == 30
    assert pdt.second == 0
    assert offset is None


def test_hour_minute_second_parse_correctly():
    """The constraints.my_pdt_fromstring() function correctly parses out hour, minute and second coordinates."""
    pdt, offset = constraints.my_pdt_fromstring("2022-01-01T12:30:45")
    assert pdt.year == 2022
    assert pdt.month == 1
    assert pdt.day == 1
    assert pdt.hour == 12
    assert pdt.minute == 30
    assert pdt.second == 45
    assert offset is None


def test_basic_year_month_parse_correctly():
    """The constraints.my_pdt_fromstring() function correctly parses out the year and month coordinates for a basic format."""
    pdt, offset = constraints.my_pdt_fromstring("202201")
    assert pdt.year == 2022
    assert pdt.month == 1
    assert pdt.day is None
    assert pdt.hour is None
    assert pdt.minute is None
    assert pdt.second is None
    assert offset is None


def test_basic_year_month_day_parse_correctly():
    """The constraints.my_pdt_fromstring() function correctly parses out the year, month, day coordinates for a basic format."""
    pdt, offset = constraints.my_pdt_fromstring("20220101")
    assert pdt.year == 2022
    assert pdt.month == 1
    assert pdt.day == 1
    assert pdt.hour == 0
    assert pdt.minute == 0
    assert pdt.second == 0
    assert offset is None


def test_basic_with_time_hour_minute_second_parse_correctly():
    """The constraints.my_pdt_fromstring() function correctly parses out hour, minute and second coordinates for a basic format."""
    pdt, offset = constraints.my_pdt_fromstring("20220101T123030")
    assert pdt.year == 2022
    assert pdt.month == 1
    assert pdt.day == 1
    assert pdt.hour == 12
    assert pdt.minute == 30
    assert pdt.second == 30
    assert offset is None


def test_microseconds_parse_correctly():
    """The constraints.my_pdt_fromstring() function correctly removes microsecond resolution."""
    pdt, offset = constraints.my_pdt_fromstring("2022-01-01T12:30:30.123456")
    assert pdt.year == 2022
    assert pdt.month == 1
    assert pdt.day == 1
    assert pdt.hour == 12
    assert pdt.minute == 30
    assert pdt.second == 30
    assert offset is None


def test_month_precision_parse_correctly():
    """The constraints.my_pdt_fromstring() function correctly parses out the year and month coordinates."""
    pdt, offset = constraints.my_pdt_fromstring("2022-01")
    assert pdt.year == 2022
    assert pdt.month == 1
    assert pdt.day is None
    assert pdt.hour is None
    assert pdt.minute is None
    assert pdt.second is None
    assert offset is None


def test_alternate_UTC_representation():
    """The constraints.my_pdt_fromstring() function correctly removes offset of +-00:00."""
    pdt, offset = constraints.my_pdt_fromstring("2022-01-01T12:30+00:00")
    assert pdt.year == 2022
    assert pdt.month == 1
    assert pdt.day == 1
    assert pdt.hour == 12
    assert pdt.minute == 30
    assert pdt.second == 0
    assert offset == timedelta(0)


def test_Indian_standard_time():
    """The constraints.my_pdt_fromstring() function correctly parses the offset."""
    pdt, offset = constraints.my_pdt_fromstring("2022-01-01T12:30+05:30")
    assert pdt.year == 2022
    assert pdt.month == 1
    assert pdt.day == 1
    assert pdt.hour == 12
    assert pdt.minute == 30
    assert pdt.second == 0
    assert offset == timedelta(seconds=19800)


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


def test_generate_cell_methods_constraint_sum():
    """Generate aggregate iris cube constraint for cell methods."""
    cell_methods_constraint = constraints.generate_cell_methods_constraint(["sum"])
    expected_cell_methods_constraint = "Constraint(cube_func=<function generate_cell_methods_constraint.<locals>.check_cell_methods at"
    assert expected_cell_methods_constraint in repr(cell_methods_constraint)


def test_generate_cell_methods_constraint_no_aggregation():
    """Generate iris cube constraint for no aggregation cell methods."""
    cell_methods_constraint = constraints.generate_cell_methods_constraint([])
    expected_cell_methods_constraint = "Constraint(cube_func=<function generate_cell_methods_constraint.<locals>.check_no_aggregation at"
    assert expected_cell_methods_constraint in repr(cell_methods_constraint)


def test_generate_cell_methods_constraint_varname():
    """Generate variable-dependent iris cube constraint for cell methods."""
    cell_methods_constraint = constraints.generate_cell_methods_constraint(
        [], "number_of_lightning_flashes"
    )
    expected_cell_methods_constraint = "Constraint(cube_func=<function generate_cell_methods_constraint.<locals>.check_cell_sum at"
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


def test_generate_remove_single_ensemble_member_constraint():
    """Generate a constraint to remove a single ensemble member using default value."""
    single_member_constraint = (
        constraints.generate_remove_single_ensemble_member_constraint()
    )
    assert (
        "Constraint(coord_values={'realization': <function generate_remove_single_ensemble_member_constraint.<locals>.<lambda> at 0x"
        in repr(single_member_constraint)
    )


def test_generate_remove_single_ensemble_member_constraint_any_value():
    """Generate a constraint to remove a single ensemble member using chosen value."""
    single_member_constraint = (
        constraints.generate_remove_single_ensemble_member_constraint(ensemble_member=2)
    )
    assert (
        "Constraint(coord_values={'realization': <function generate_remove_single_ensemble_member_constraint.<locals>.<lambda> at 0x"
        in repr(single_member_constraint)
    )


def test_generate_realization_constraint():
    """Generate a constraint for a single realization."""
    single_member_constraint = constraints.generate_realization_constraint(
        ensemble_members=2
    )
    assert "Constraint(coord_values={'realization': (2,)})" in repr(
        single_member_constraint
    )


def test_generate_realization_constraint_multiple_realizations():
    """Generate a constraint for multiple realizations."""
    multi_member_constraint = constraints.generate_realization_constraint(
        ensemble_members=[2, 4, 6, 8]
    )
    assert "Constraint(coord_values={'realization': [2, 4, 6, 8]})" in repr(
        multi_member_constraint
    )


def test_generate_hour_constraint():
    """Generate hour constraint with hour_start."""
    hour_constraint = constraints.generate_hour_constraint(hour_start=12)
    expected_hour_constraint = "Constraint(coord_values={'hour': <function generate_hour_constraint.<locals>.<lambda> at"
    assert expected_hour_constraint in repr(hour_constraint)


def test_generate_hour_constraint_both_limits():
    """Generate hour constraint with hour_start and hour_end."""
    hour_constraint = constraints.generate_hour_constraint(hour_start=12, hour_end=15)
    expected_hour_constraint = "Constraint(coord_values={'hour': <function generate_hour_constraint.<locals>.<lambda> at"
    assert expected_hour_constraint in repr(hour_constraint)


def test_generate_hour_constraint_negative_values():
    """Generate hour constraint raises exception when arguments are negative."""
    with pytest.raises(ValueError):
        constraints.generate_hour_constraint(hour_start=-1)

    with pytest.raises(ValueError):
        constraints.generate_hour_constraint(hour_start=0, hour_end=-1)


def test_generate_hour_constraint_too_large_values():
    """Generate hour constraint raises exception when arguments are too big."""
    with pytest.raises(ValueError):
        constraints.generate_hour_constraint(hour_start=24)

    with pytest.raises(ValueError):
        constraints.generate_hour_constraint(hour_start=22, hour_end=24)


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
