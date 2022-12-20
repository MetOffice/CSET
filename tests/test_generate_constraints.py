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

from CSET.operators import generate_constraints


def test_generate_constraints_operator():
    """generate iris cube constraint for UM STASH code."""
    stash_constraint = generate_constraints.generate_stash_constraints("m01s03i236")
    # expected_stash_constraint = "<class 'iris._constraints.AttributeConstraint'>"
    # assert type(stash_constraint) == expected_stash_constraint
    expected_stash_constraint = "AttributeConstraint({'STASH': 'm01s03i236'})"
    assert repr(stash_constraint) == expected_stash_constraint

    """generate iris cube constraint for str variable name."""
    var_constraint = generate_constraints.generate_var_constraints("test")
    # expected_var_constraint = "<class 'iris._constraints.Constraint'>"
    # assert type(var_constraint) == expected_var_constraint
    expected_var_constraint = "Constraint(name='test')"
    assert repr(var_constraint) == expected_var_constraint
