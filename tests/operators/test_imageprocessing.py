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
from skimage.metrics import structural_similarity

from CSET.operators import aggregate, imageprocessing


def test_structural_similarity_model_comparisons_MSSIM(cube: iris.cube.Cube):
    """Test taking the MSSIM between two cubes."""
    # Data preparation.
    other_cube = cube.copy()
    del other_cube.attributes["cset_comparison_base"]
    cubes = iris.cube.CubeList([cube, other_cube])

    # Find MSSIM.
    MSSIM_cube = imageprocessing.mean_structural_similarity_model_comparisons(
        cubes, sigma=1.5
    )

    # As both cubes use the same data, check the MSSIM is one.
    assert isinstance(MSSIM_cube, iris.cube.Cube)
    assert np.allclose(MSSIM_cube.data, np.ones_like(MSSIM_cube.data), atol=1e-9)


def test_structural_similarity_model_comparisons_SSIM(cube: iris.cube.Cube):
    """Test taking the SSIM between two cubes."""
    # Data preparation.
    other_cube = cube.copy()
    del other_cube.attributes["cset_comparison_base"]
    cubes = iris.cube.CubeList([cube, other_cube])

    # Find MSSIM.
    SSIM_cube = imageprocessing.spatial_structural_similarity_model_comparisons(
        cubes, sigma=1.5
    )

    # As both cubes use the same data, check the SSIM is one everywhere.
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
    MSSIM_cube = imageprocessing.mean_structural_similarity_model_comparisons(
        cubes, sigma=0.5
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
    MSSIM_cube = imageprocessing.mean_structural_similarity_model_comparisons(cubes)
    assert MSSIM_cube.standard_name is None
    assert MSSIM_cube.long_name == "structural_similarity"


def test_structural_similarity_model_comparisons_MSSIM_units(cube: iris.cube.Cube):
    """Test renaming of cube."""
    # Data preparation.
    other_cube = cube.copy()
    del other_cube.attributes["cset_comparison_base"]
    cubes = iris.cube.CubeList([cube, other_cube])

    assert imageprocessing.mean_structural_similarity_model_comparisons(
        cubes
    ).units == cf_units.Unit("1")


def test_structural_similarity_model_comparisons_SSIM_name(cube: iris.cube.Cube):
    """Test renaming of cube."""
    # Data preparation.
    other_cube = cube.copy()
    del other_cube.attributes["cset_comparison_base"]
    cubes = iris.cube.CubeList([cube, other_cube])

    # Find MSSIM.
    MSSIM_cube = imageprocessing.spatial_structural_similarity_model_comparisons(cubes)
    assert MSSIM_cube.standard_name is None
    assert MSSIM_cube.long_name == "structural_similarity"


def test_structural_similarity_model_comparisons_SSIM_units(cube: iris.cube.Cube):
    """Test renaming of cube."""
    # Data preparation.
    other_cube = cube.copy()
    del other_cube.attributes["cset_comparison_base"]
    cubes = iris.cube.CubeList([cube, other_cube])

    assert imageprocessing.spatial_structural_similarity_model_comparisons(
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
        imageprocessing._SSIM_cube_preparation(cubes)


def test_SSIM_incorrect_number_of_cubes(cube: iris.cube.Cube):
    """Test exception when incorrect number of cubes provided."""
    no_cubes = iris.cube.CubeList([])
    with pytest.raises(ValueError, match="cubes should contain exactly 2 cubes."):
        imageprocessing._SSIM_cube_preparation(no_cubes)

    one_cube = iris.cube.CubeList([cube])
    with pytest.raises(ValueError, match="cubes should contain exactly 2 cubes."):
        imageprocessing._SSIM_cube_preparation(one_cube)

    three_cubes = iris.cube.CubeList([cube, cube, cube])
    with pytest.raises(ValueError, match="cubes should contain exactly 2 cubes."):
        imageprocessing._SSIM_cube_preparation(three_cubes)


def test_SSIM_no_time_coord(cube: iris.cube.Cube):
    """Test SSIM fails with no time coordinate."""
    c1 = cube.extract(iris.Constraint(time=datetime.datetime(2022, 9, 21, 3, 30)))
    c1.remove_coord("time")
    c2 = c1.copy()
    del c2.attributes["cset_comparison_base"]
    cubes = iris.cube.CubeList([c1, c2])
    with pytest.raises(ValueError, match="Cubes should contain a time coordinate."):
        imageprocessing._SSIM_cube_preparation(cubes)


def test_SSIM_different_data_shape_regrid(cube: iris.cube.Cube):
    """Test when data shape differs, but gets regridded.

    For any cube shapes differ.
    """
    rearranged_cube = cube.copy()
    rearranged_cube = rearranged_cube[:, :, 1:]
    del cube.attributes["cset_comparison_base"]
    cubes = iris.cube.CubeList([rearranged_cube, cube])
    MSSIM = imageprocessing.spatial_structural_similarity_model_comparisons(
        cubes,
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
    MSSIM = imageprocessing.spatial_structural_similarity_model_comparisons(
        cubes,
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
    MSSIM_cube = imageprocessing.mean_structural_similarity_model_comparisons(
        cubes,
    )

    assert isinstance(MSSIM_cube, iris.cube.Cube)
    # As both cubes use the same data, check the MSSIM is one.
    assert np.allclose(MSSIM_cube.data, np.ones_like(MSSIM_cube.data), atol=1e-9)


def test_MSSIM_hour_coordinates(cube: iris.cube.Cube):
    """Test MSSIM with hour coordinate."""
    # Data preparation.
    other_cube = cube.copy()
    del other_cube.attributes["cset_comparison_base"]
    cubes = iris.cube.CubeList([cube, other_cube])
    cubes = aggregate.add_hour_coordinate(cubes)
    for cube in cubes:
        cube.remove_coord("time")
    # Find MSSIM.
    MSSIM_cube = imageprocessing.mean_structural_similarity_model_comparisons(
        cubes, sigma=1.5
    )

    # As both cubes use the same data, check the MSSIM is one.
    assert isinstance(MSSIM_cube, iris.cube.Cube)
    assert np.allclose(MSSIM_cube.data, np.ones_like(MSSIM_cube.data), atol=1e-9)


def test_SSIM_hour_coordinates(cube: iris.cube.Cube):
    """Test SSIM with hour coordinate."""
    # Data preparation.
    other_cube = cube.copy()
    del other_cube.attributes["cset_comparison_base"]
    cubes = iris.cube.CubeList([cube, other_cube])
    cubes = aggregate.add_hour_coordinate(cubes)
    for cube in cubes:
        cube.remove_coord("time")
    # Find SSIM.
    SSIM_cube = imageprocessing.spatial_structural_similarity_model_comparisons(
        cubes,
        sigma=1.5,
    )

    # As both cubes use the same data, check the SSIM is one.
    assert isinstance(SSIM_cube, iris.cube.Cube)
    assert np.allclose(SSIM_cube.data, np.ones_like(SSIM_cube.data), atol=1e-9)


def test_structural_similarity_model_comparisons_MSSIM_different_sigma_not_one(
    cube: iris.cube.Cube,
):
    """Test taking the MSSIM between two cubes with different sigma."""
    # Data preparation.
    other_cube = cube.copy()
    # Flip cube to change data so MSSIM does not equal one.
    other_cube.data = np.flip(other_cube.data)
    del other_cube.attributes["cset_comparison_base"]
    cubes = iris.cube.CubeList([cube, other_cube])
    # Expected MSSIM
    expected_mssim = iris.cube.CubeList()
    for base_r, other_r in zip(
        cube.slices_over("realization"),
        other_cube.slices_over("realization"),
        strict=True,
    ):
        for base_t, other_t in zip(
            base_r.slices_over("time"), other_r.slices_over("time"), strict=True
        ):
            # Use the full array as output will be as a 2D map.
            ssim_map = base_t[0, 0].copy()
            ssim_map.data = structural_similarity(
                base_t.data,
                other_t.data,
                data_range=other_t.data.max() - other_t.data.min(),
                gaussian_weights=True,
                sigma=0.5,
            )
            expected_mssim.append(ssim_map)
    # Merge the cube slices into one cube, rename, and change units.
    expected_mssim = expected_mssim.merge_cube()
    # Find MSSIM.
    MSSIM_cube = imageprocessing.mean_structural_similarity_model_comparisons(
        cubes, sigma=0.5
    )

    # As both cubes use the same data, check the MSSIM is one.
    assert isinstance(MSSIM_cube, iris.cube.Cube)
    assert np.allclose(MSSIM_cube.data, expected_mssim.data, atol=1e-9)


def test_structural_similarity_model_comparisons_SSIM_different_sigma_not_one(
    cube: iris.cube.Cube,
):
    """Test taking the SSIM between two cubes with different sigma."""
    # Data preparation.
    other_cube = cube.copy()
    other_cube.data = np.flip(other_cube.data)
    del other_cube.attributes["cset_comparison_base"]
    cubes = iris.cube.CubeList([cube, other_cube])

    # Find SSIM.
    SSIM_cube = imageprocessing.spatial_structural_similarity_model_comparisons(
        cubes, sigma=0.5
    )

    expected_ssim = iris.cube.CubeList()

    # Loop over realization and time coordinates.
    for base_r, other_r in zip(
        cube.slices_over("realization"),
        other_cube.slices_over("realization"),
        strict=True,
    ):
        for base_t, other_t in zip(
            base_r.slices_over("time"), other_r.slices_over("time"), strict=True
        ):
            # Use the full array as output will be as a 2D map.
            ssim_map = base_t.copy()
            _, ssim_map.data = structural_similarity(
                base_t.data,
                other_t.data,
                data_range=other_t.data.max() - other_t.data.min(),
                gaussian_weights=True,
                sigma=0.5,
                full=True,
            )
            expected_ssim.append(ssim_map)
    # Merge the cube slices into one cube, rename, and change units.
    ssim = expected_ssim.merge_cube()

    # As both cubes use the same data, check the SSIM is one.
    assert isinstance(SSIM_cube, iris.cube.Cube)
    assert np.allclose(SSIM_cube.data, ssim.data, atol=1e-9)
