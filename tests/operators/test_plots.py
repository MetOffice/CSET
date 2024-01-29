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

"""Test plotting operators."""

from pathlib import Path

import iris.cube
import pytest

from CSET.operators import execute_recipe, plot


def test_spatial_plot(tmp_path: Path):
    """Plot spatial contour plot of instant air temp."""
    input_file = Path("tests/test_data/air_temp.nc")
    output_dir = tmp_path / "output"
    recipe_file = Path("tests/test_data/plot_instant_air_temp.yaml")
    execute_recipe(recipe_file, input_file, output_dir)
    actual_output_file = output_dir / "plot.png"
    assert actual_output_file.is_file()


def test_postage_stamp_plots(tmp_path: Path):
    """Plot postage stamp plots of ensemble data."""
    input_file = Path("tests/test_data/")
    output_dir = tmp_path / "output"
    recipe_file = Path("tests/test_data/ensemble_air_temp.yaml")
    execute_recipe(recipe_file, input_file, output_dir)
    assert output_dir.joinpath("plot.png").is_file()


def test_postage_stamp_realization_check(tmp_path: Path, cube):
    """Check error when cube has no realization coordinate."""
    cube.remove_coord("realization")
    plot_path = tmp_path / "plot.png"
    with pytest.raises(ValueError):
        plot.postage_stamp_contour_plot(cube, plot_path)


def test_check_single_cube():
    """Conversion to a single cube, and rejection where not possible."""
    cube = iris.cube.Cube([0.0])
    cubelist = iris.cube.CubeList([cube])
    long_cubelist = iris.cube.CubeList([cube, cube])
    non_cube = 1
    assert plot._check_single_cube(cube) == cube
    assert plot._check_single_cube(cubelist) == cube
    with pytest.raises(TypeError):
        plot._check_single_cube(long_cubelist)
    with pytest.raises(TypeError):
        plot._check_single_cube(non_cube)


def test_contour_plot_sequence(cube, tmp_working_dir):
    """Plot sequence of contour plots."""
    plot.spatial_contour_plot(cube, sequence_coordinate="time")
    assert Path("untitled_1.png").is_file()
    assert Path("untitled_2.png").is_file()
    assert Path("untitled_3.png").is_file()
