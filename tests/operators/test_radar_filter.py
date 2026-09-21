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
