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

from pathlib import Path
from uuid import uuid4
import tempfile

import iris.cube
import pytest

import CSET.operators


def test_spatial_plot():
    """Plot spatial contour plot of instant air temp."""

    input_file = Path("tests/test_data/air_temp.nc")
    output_file = Path(f"{tempfile.gettempdir()}/{uuid4()}")
    recipe_file = Path("tests/test_data/plot_instant_air_temp.yaml")
    CSET.operators.execute_recipe(recipe_file, input_file, output_file)
    actual_output_file = output_file.with_suffix(".svg")
    assert actual_output_file.exists()
    actual_output_file.unlink()


def test_postage_stamp_plots(tmp_path: Path):
    """Plot postage stamp plots of ensemble data."""

    input_file = Path("tests/test_data/")
    output_file = tmp_path / f"{uuid4()}.svg"
    recipe_file = Path("tests/test_data/ensemble_air_temp.yaml")
    CSET.operators.execute_recipe(recipe_file, input_file, output_file)
    assert output_file.exists()


def test_postage_stamp_realization_check(tmp_path: Path):
    """Check error when cube has no realization coordinate."""

    cube = CSET.operators.read.read_cubes("tests/test_data/air_temp.nc")[0]
    cube.remove_coord("realization")
    plot_path = tmp_path / "plot.svg"
    with pytest.raises(ValueError):
        CSET.operators.plot.postage_stamp_contour_plot(cube, plot_path)


def test_check_single_cube():
    """Conversion to a single cube, and rejection where not possible."""

    cube = iris.cube.Cube([0.0])
    cubelist = iris.cube.CubeList([cube])
    long_cubelist = iris.cube.CubeList([cube, cube])
    non_cube = 1
    assert CSET.operators.plot._check_single_cube(cube) == cube
    assert CSET.operators.plot._check_single_cube(cubelist) == cube
    with pytest.raises(TypeError):
        CSET.operators.plot._check_single_cube(long_cubelist)
    with pytest.raises(TypeError):
        CSET.operators.plot._check_single_cube(non_cube)
