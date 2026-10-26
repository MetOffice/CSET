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

"""Test vorticity operators."""

import numpy as np
from iris.analysis.calculus import curl

from CSET.operators import vorticity


def test_vertical_relative_vorticity(xwind, ywind):
    """Test vertical relative vorticity calculation."""
    _, _, expected = curl(xwind, ywind)
    assert np.allclose(
        vorticity.relative_vorticity(xwind, ywind).data,
        expected.data,
        rtol=1e-6,
        atol=1e-2,
    )
