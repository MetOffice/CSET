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

"""Tests for spectra calculation functionality across CSET."""

import numpy as np

from CSET.operators import spectra


def test_create_alpha_matrix_shape():
    """Test shape of alpha matrix used in power spectrum calculation."""
    Ny, Nx = 10, 15
    alpha = spectra._create_alpha_matrix(Ny, Nx)
    assert alpha.shape == (Ny, Nx), "Alpha matrix shape mismatch"


def test_create_alpha_matrix_values():
    """Test alpha matrix contains only positive values."""
    Ny, Nx = 4, 4
    alpha = spectra._create_alpha_matrix(Ny, Nx)
    assert np.all(alpha >= 0), "Alpha matrix contains negative values"
    assert np.isclose(alpha[0, 0], np.sqrt((1 / Nx) ** 2 + (1 / Ny) ** 2)), (
        "Alpha matrix value incorrect"
    )


def test_dct_ps_output_shape():
    """Test shape of power spectrum output from _DCT_ps."""
    Nt, Ny, Nx = 5, 10, 10
    y_3d = np.random.rand(Nt, Ny, Nx)
    ps = spectra._DCT_ps(y_3d)
    expected_shape = (Nt, min(Nx - 1, Ny - 1))
    assert ps.shape == expected_shape, "Power spectrum output shape mismatch"


def test_dct_ps_non_negative():
    """Test power spectrum only contains positive values."""
    Nt, Ny, Nx = 3, 8, 8
    y_3d = np.random.rand(Nt, Ny, Nx)
    ps = spectra._DCT_ps(y_3d)
    assert np.all(ps >= 0), "Power spectrum contains negative values"


def test_dct_ps_known_input():
    """Test _DCT_ps produces non-zero spectrum for constant input."""
    # Use a constant field to test expected behavior
    Nt, Ny, Nx = 2, 4, 4
    y_3d = np.ones((Nt, Ny, Nx))
    ps = spectra._DCT_ps(y_3d)
    assert np.allclose(ps[:, 1:], 0, atol=1e-6), "Non-zero spectrum for constant input"
