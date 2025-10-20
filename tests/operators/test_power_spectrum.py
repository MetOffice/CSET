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

"""Tests power spectrum operator."""

import iris
import iris.cube
import numpy as np
import pytest

from CSET.operators import power_spectrum


def make_test_cube(shape=(1, 10, 10), time_points=None):
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


# def make_test_cube(shape, coord_values=None, coord_names=None, units=None, long_name="test_data"):
#    """
#    Create a test cube with arbitrary shape and coordinates.
#
#    Parameters:
#        shape (tuple): Shape of the data array.
#        coord_values (list of arrays): Optional list of coordinate values for each dimension.
#        coord_names (list of str): Optional list of coordinate names (standard_name or long_name).
#        units (list of str): Optional list of units for each coordinate.
#        long_name (str): Long name for the cube.
#
#    Returns:
#        iris.cube.Cube: The generated test cube.
#    """
#    data = np.random.rand(*shape)
#
#    dim_coords_and_dims = []
#    for i, dim_size in enumerate(shape):
#        # Default coordinate values
#        values = np.arange(dim_size) if coord_values is None or coord_values[i] is None else coord_values[i]
#        # Default name
#        name = coord_names[i] if coord_names and i < len(coord_names) else f"dim_{i}"
#        # Default units
#        unit = units[i] if units and i < len(units) else "1"
#
#        coord = iris.coords.DimCoord(values, long_name=name, units=unit)
#        dim_coords_and_dims.append((coord, i))
#
#    cube = iris.cube.Cube(
#        data,
#        dim_coords_and_dims=dim_coords_and_dims,
#        long_name=long_name
#    )
#    return cube


def test_calculate_power_spectrum_returns_cube():
    """Check calculate_power_spectrum returns a cube."""
    cube = make_test_cube()
    #    cube = make_test_cube(shape=(1, 10, 10))
    ps_cube = power_spectrum.calculate_power_spectrum(cube)
    assert isinstance(ps_cube, iris.cube.Cube)
    assert ps_cube.shape[0] == cube.shape[0]
    assert ps_cube.shape[1] > 0
    assert ps_cube.coord("frequency").shape[0] == ps_cube.shape[1]
    assert ps_cube.coord("time").shape[0] == cube.shape[0]


def test_calculate_power_spectrum_with_cubelist():
    """Check calculate_power_spectrum works with a cubelist."""
    cube = make_test_cube()
    #    cube = make_test_cube(shape=(1, 10, 10))
    cubelist = iris.cube.CubeList([cube])
    ps_cube = power_spectrum.calculate_power_spectrum(cubelist)
    assert isinstance(ps_cube, iris.cube.Cube)


def test_calculate_power_spectrum_raises_for_bad_dim():
    """Check error is raised if the cube dimensions are not supported."""
    cube_3d = make_test_cube()

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

    with pytest.raises(
        ValueError, match="Cube dimensions unsuitable for power spectra code"
    ):
        power_spectrum.calculate_power_spectrum(cube_5d)


def test_DCT_ps_output_shape():
    """Check power spectra cube from DCT_ps has the correct dimensions."""
    arr = np.random.rand(2, 8, 8)
    ps_cube = power_spectrum.DCT_ps(arr)
    assert ps_cube.shape == (2, 7)  # Nmin = min(7,7) = 7


def test_create_alpha_matrix_shape_and_values():
    """Check alpha_matrix has correct dimensions."""
    Ny, Nx = 5, 7
    alpha = power_spectrum.create_alpha_matrix(Ny, Nx)
    assert alpha.shape == (Ny, Nx)
    assert np.all(alpha >= 0)
