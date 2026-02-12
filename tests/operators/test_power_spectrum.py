# © Crown copyright, Met Office (2022-2025) and CSET contributors.
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

"""Test power spectrum operator."""

import iris.coords
import iris.cube
import numpy as np
import pytest

from CSET.operators import power_spectrum


def test_create_alpha_matrix_shape():
    """Test shape of alpha matrix used in power spectrum calculation."""
    Ny, Nx = 10, 15
    alpha = power_spectrum._create_alpha_matrix(Ny, Nx)
    assert alpha.shape == (Ny, Nx), "Alpha matrix shape mismatch"


def test_create_alpha_matrix_values():
    """Test alpha matrix contains only positive values."""
    Ny, Nx = 4, 4
    alpha = power_spectrum._create_alpha_matrix(Ny, Nx)
    assert np.all(alpha >= 0), "Alpha matrix contains negative values"
    assert np.isclose(alpha[0, 0], np.sqrt((1 / Nx) ** 2 + (1 / Ny) ** 2)), (
        "Alpha matrix value incorrect"
    )


def test_dct_ps_output_shape():
    """Test shape of power spectrum output from _DCT_ps."""
    Nt, Ny, Nx = 5, 10, 10
    y_3d = np.random.rand(Nt, Ny, Nx)
    ps = power_spectrum._DCT_ps(y_3d)
    expected_shape = (Nt, min(Nx - 1, Ny - 1))
    assert ps.shape == expected_shape, "Power spectrum output shape mismatch"


def test_dct_ps_non_negative():
    """Test power spectrum only contains positive values."""
    Nt, Ny, Nx = 3, 8, 8
    y_3d = np.random.rand(Nt, Ny, Nx)
    ps = power_spectrum._DCT_ps(y_3d)
    assert np.all(ps >= 0), "Power spectrum contains negative values"


def test_dct_ps_known_input():
    """Test _DCT_ps produces non-zero spectrum for constant input."""
    # Use a constant field to test expected behavior
    Nt, Ny, Nx = 2, 4, 4
    y_3d = np.ones((Nt, Ny, Nx))
    ps = power_spectrum._DCT_ps(y_3d)
    assert np.allclose(ps[:, 1:], 0, atol=1e-6), "Non-zero spectrum for constant input"


def make_test_cube_power_spectrum(shape=(1, 10, 10), time_points=None):
    """Create test cube for use with the power spectrum tests."""
    data = np.random.rand(*shape)
    if time_points is None:
        time_points = [0]
    time_coord = iris.coords.DimCoord(
        time_points, standard_name="time", units="hours since 1970-01-01 00:00:00"
    )
    y_coord = iris.coords.DimCoord(np.arange(shape[1]), long_name="y", units="1")
    x_coord = iris.coords.DimCoord(np.arange(shape[2]), long_name="x", units="1")
    cube = iris.cube.Cube(
        data,
        dim_coords_and_dims=[(time_coord, 0), (y_coord, 1), (x_coord, 2)],
        long_name="test_data",
    )
    return cube


def test_calculate_power_spectrum_raises_for_bad_dim(tmp_working_dir):
    """Check error is raised if the cube has too many dimensions."""
    cube_3d = make_test_cube_power_spectrum()

    # Add 2 new dimensions to cube_3d to make 5D
    new_data = cube_3d.data[np.newaxis, np.newaxis, :, :, :]

    # Create dummy coordinates for the new dimensions
    coord_0 = iris.coords.DimCoord([0], long_name="extra_dim_0")
    coord_1 = iris.coords.DimCoord([0], long_name="extra_dim_1")

    # Build dim_coords_and_dims manually
    dim_coords_and_dims = [(coord_0, 0), (coord_1, 1)]
    for i, coord in enumerate(cube_3d.dim_coords):
        dim_coords_and_dims.append((coord, i + 2))  # shift by 2 for new axes

    # Create the new 4D cube
    cube_5d = iris.cube.Cube(new_data, dim_coords_and_dims=dim_coords_and_dims)

    if isinstance(cube_5d, iris.cube.CubeList):
        cube_5d = cube_5d[0]

    with pytest.raises(ValueError, match="Cube should be 2 or 3 dimensional"):
        power_spectrum.calculate_power_spectrum(cube_5d)


def test_calculate_power_spectrum_raises_for_bad_dim_1D(tmp_working_dir):
    """Check error is raised if the cube has too few dimensions."""
    cube_3d = make_test_cube_power_spectrum()

    # Make a 1D field

    cube_1d = cube_3d.collapsed(["x", "y"], iris.analysis.MEAN)

    if isinstance(cube_1d, iris.cube.CubeList):
        cube_1d = cube_1d[0]

    with pytest.raises(ValueError, match="Cube should be 2 or 3 dimensional"):
        power_spectrum.calculate_power_spectrum(cube_1d)
