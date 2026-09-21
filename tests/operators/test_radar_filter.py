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
    print("----> 1 obs ", obs)

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
