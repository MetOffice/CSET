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

"""Test mesoscale operators."""

import numpy as np
from scipy.ndimage import gaussian_filter, uniform_filter

import CSET.operators.mesoscale as mesoscale
from CSET.operators._utils import get_cube_yxcoordname


def test_spatial_perturbation_field_gaussian(cube):
    """Test smoothing a cube with a Gaussian filter."""
    calculated = cube.copy()
    coords = [coord.name() for coord in cube.coords()]
    axes = (
        coords.index(get_cube_yxcoordname(cube)[0]),
        coords.index(get_cube_yxcoordname(cube)[1]),
    )
    calculated.data -= gaussian_filter(cube.data, 40, axes=axes)
    assert np.allclose(
        calculated.data,
        mesoscale.spatial_perturbation_field(cube).data,
        rtol=1e-06,
        atol=1e-02,
    )

    calculated_2 = cube.copy()
    calculated_2.data -= gaussian_filter(cube.data, 100, axes=axes)
    assert np.allclose(
        calculated_2.data,
        mesoscale.spatial_perturbation_field(cube, filter_scale=100).data,
        rtol=1e-06,
        atol=1e-02,
    )


def test_spatial_perturbation_field_uniform(cube):
    """Test smoothing a cube with a uniform filter."""
    calculated = cube.copy()
    coords = [coord.name() for coord in cube.coords()]
    axes = (
        coords.index(get_cube_yxcoordname(cube)[0]),
        coords.index(get_cube_yxcoordname(cube)[1]),
    )
    calculated.data -= uniform_filter(cube.data, 40, axes=axes)
    assert np.allclose(
        calculated.data,
        mesoscale.spatial_perturbation_field(cube, apply_gaussian_filter=False).data,
        rtol=1e-06,
        atol=1e-02,
    )

    calculated_2 = cube.copy()
    calculated_2.data -= uniform_filter(cube.data, 100, axes=axes)
    assert np.allclose(
        calculated_2.data,
        mesoscale.spatial_perturbation_field(
            cube, apply_gaussian_filter=False, filter_scale=100
        ).data,
        rtol=1e-06,
        atol=1e-02,
    )
