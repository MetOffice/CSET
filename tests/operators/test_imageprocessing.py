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

"""Test miscellaneous operators."""

import datetime

import cf_units
import iris
import iris.coords
import iris.cube
import iris.exceptions
import numpy as np
import pytest

from CSET.operators import imageprocessing


def test_structural_similarity_model_comparisons_MSSIM(cube: iris.cube.Cube):
    """Test taking the MSSIM between two cubes."""
    # Data preparation.
    other_cube = cube.copy()
    del other_cube.attributes["cset_comparison_base"]
    cubes = iris.cube.CubeList([cube, other_cube])

    # Find MSSIM.
    MSSIM_cube = imageprocessing.structural_similarity_model_comparisons(
        cubes, sigma=1.5, spatial_plot=False
    )

    # As both cubes use the same data, check the MSSIM is one.
    assert isinstance(MSSIM_cube, iris.cube.Cube)
    assert np.allclose(MSSIM_cube.data, np.ones_like(MSSIM_cube.data), atol=1e-9)


def test_structural_similarity_model_comparisons_SSIM(cube: iris.cube.Cube):
    """Test taking the SSUM between two cubes."""
    # Data preparation.
    other_cube = cube.copy()
    del other_cube.attributes["cset_comparison_base"]
    cubes = iris.cube.CubeList([cube, other_cube])

    # Find MSSIM.
    SSIM_cube = imageprocessing.structural_similarity_model_comparisons(
        cubes, sigma=1.5, spatial_plot=True
    )

    # As both cubes use the same data, check the MSSIM is one.
    assert isinstance(SSIM_cube, iris.cube.Cube)
    assert np.allclose(SSIM_cube.data, np.ones_like(SSIM_cube.data), atol=1e-9)


def test_structural_similarity_model_comparisons_MSSIM_different_sigma(
    cube: iris.cube.Cube,
):
    """Test taking the MSSIM between two cubes with different sigma."""
    # Data preparation.
    other_cube = cube.copy()
    del other_cube.attributes["cset_comparison_base"]
    cubes = iris.cube.CubeList([cube, other_cube])

    # Find MSSIM.
    MSSIM_cube = imageprocessing.structural_similarity_model_comparisons(
        cubes, sigma=0.5, spatial_plot=False
    )

    # As both cubes use the same data, check the MSSIM is one.
    assert isinstance(MSSIM_cube, iris.cube.Cube)
    assert np.allclose(MSSIM_cube.data, np.ones_like(MSSIM_cube.data), atol=1e-9)


def test_structural_similarity_model_comparisons_MSSIM_name(cube: iris.cube.Cube):
    """Test renaming of cube."""
    # Data preparation.
    other_cube = cube.copy()
    del other_cube.attributes["cset_comparison_base"]
    cubes = iris.cube.CubeList([cube, other_cube])

    # Find MSSIM.
    MSSIM_cube = imageprocessing.structural_similarity_model_comparisons(cubes)
    assert MSSIM_cube.standard_name is None
    assert MSSIM_cube.long_name == "structural_similarity"


def test_structural_similarity_model_comparisons_MSSIM_units(cube: iris.cube.Cube):
    """Test renaming of cube."""
    # Data preparation.
    other_cube = cube.copy()
    del other_cube.attributes["cset_comparison_base"]
    cubes = iris.cube.CubeList([cube, other_cube])

    assert imageprocessing.structural_similarity_model_comparisons(
        cubes
    ).units == cf_units.Unit("1")


def test_SSIM_no_common_points(cube: iris.cube.Cube):
    """Test exception when there are no common time points between cubes."""
    other_cube = cube.copy()
    # Offset times by 6 hours.
    new_times = other_cube.coord("time").points.copy()
    new_times += 6
    other_cube.coord("time").points = new_times
    del other_cube.attributes["cset_comparison_base"]
    cubes = iris.cube.CubeList([cube, other_cube])
    with pytest.raises(ValueError, match="No common time points found!"):
        imageprocessing.structural_similarity_model_comparisons(cubes)


def test_SSIM_incorrect_number_of_cubes(cube: iris.cube.Cube):
    """Test exception when incorrect number of cubes provided."""
    no_cubes = iris.cube.CubeList([])
    with pytest.raises(ValueError, match="cubes should contain exactly 2 cubes."):
        imageprocessing.structural_similarity_model_comparisons(no_cubes)

    one_cube = iris.cube.CubeList([cube])
    with pytest.raises(ValueError, match="cubes should contain exactly 2 cubes."):
        imageprocessing.structural_similarity_model_comparisons(one_cube)

    three_cubes = iris.cube.CubeList([cube, cube, cube])
    with pytest.raises(ValueError, match="cubes should contain exactly 2 cubes."):
        imageprocessing.structural_similarity_model_comparisons(three_cubes)


def test_MSSIM_no_time_coord(cube: iris.cube.Cube):
    """Test MSSIM fails with no time coordinate."""
    c1 = cube.extract(iris.Constraint(time=datetime.datetime(2022, 9, 21, 3, 30)))
    c1.remove_coord("time")
    c2 = c1.copy()
    del c2.attributes["cset_comparison_base"]
    cubes = iris.cube.CubeList([c1, c2])
    with pytest.raises(ValueError, match="Cubes should contain a time coordinate."):
        imageprocessing.structural_similarity_model_comparisons(cubes)


def test_SSIM_different_data_shape_regrid(cube: iris.cube.Cube):
    """Test when data shape differs, but gets regridded.

    For any cube shapes differ.
    """
    rearranged_cube = cube.copy()
    rearranged_cube = rearranged_cube[:, :, 1:]
    del cube.attributes["cset_comparison_base"]
    cubes = iris.cube.CubeList([rearranged_cube, cube])
    MSSIM = imageprocessing.structural_similarity_model_comparisons(
        cubes, spatial_plot=True
    )
    assert isinstance(MSSIM, iris.cube.Cube)
    assert MSSIM.shape == cube.shape
    assert MSSIM.shape != rearranged_cube.shape


def test_SSIM_grid_staggering_regrid(cube: iris.cube.Cube):
    """Test when data considered on staggered grid, so gets regridded."""
    rearranged_cube = cube.copy()
    rearranged_cube.rename("eastward_wind_at_10m")
    del cube.attributes["cset_comparison_base"]
    cubes = iris.cube.CubeList([rearranged_cube, cube])
    MSSIM = imageprocessing.structural_similarity_model_comparisons(
        cubes, spatial_plot=True
    )
    assert isinstance(MSSIM, iris.cube.Cube)
    assert MSSIM.shape == cube.shape


def test_SSIM_different_model_types(cube: iris.cube.Cube):
    """Other cube is flipped when model types differ."""
    flipped = cube.copy()
    flipped_coord = flipped.coord("grid_latitude")
    flipped_coord.points = np.flip(flipped_coord.points)
    flipped.data = np.flip(flipped.data, flipped_coord.cube_dims(flipped))
    del flipped.attributes["cset_comparison_base"]
    cubes = iris.cube.CubeList([cube, flipped])

    # Take MSSIM.
    MSSIM_cube = imageprocessing.structural_similarity_model_comparisons(
        cubes, spatial_plot=True
    )

    assert isinstance(MSSIM_cube, iris.cube.Cube)
    # As both cubes use the same data, check the MSSIM is one.
    assert np.allclose(MSSIM_cube.data, np.ones_like(MSSIM_cube.data), atol=1e-9)
