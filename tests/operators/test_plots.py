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

from CSET.operators import collapse, plot, read


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


def test_spatial_contour_plot(cube, tmp_working_dir):
    """Plot spatial contour plot of instant air temp."""
    # Remove realization coord to increase coverage, and as its not needed.
    cube = cube.copy()
    cube.remove_coord("realization")
    cube_2d = cube.slices_over("time").next()
    plot.spatial_contour_plot(cube_2d, filename="plot")
    assert Path("plot_462147.0.png").is_file()


def test_contour_plot_sequence(cube, tmp_working_dir):
    """Plot sequence of contour plots."""
    plot.spatial_contour_plot(cube, sequence_coordinate="time")
    assert Path("untitled_462147.0.png").is_file()
    assert Path("untitled_462148.0.png").is_file()
    assert Path("untitled_462149.0.png").is_file()


def test_postage_stamp_contour_plot(monkeypatch, tmp_path):
    """Plot postage stamp plots of ensemble data."""
    ensemble_cube = read.read_cube("tests/test_data/exeter_em*.nc")
    # Get a single time step.
    ensemble_cube_3d = next(ensemble_cube.slices_over("time"))
    monkeypatch.chdir(tmp_path)
    plot.spatial_contour_plot(ensemble_cube_3d)
    assert Path("untitled_463858.0.png").is_file()


def test_postage_stamp_contour_plot_sequence_coord_check(cube, tmp_working_dir):
    """Check error when cube has no time coordinate."""
    # What does this even physically mean? No data?
    cube = cube.copy()
    cube.remove_coord("time")
    with pytest.raises(ValueError):
        plot.spatial_contour_plot(cube)


def test_plot_line_series(cube, tmp_working_dir):
    """Save a line series plot."""
    cube = collapse.collapse(cube, ["grid_latitude", "grid_longitude"], "MEAN")
    plot.plot_line_series(cube)
    assert Path("untitled.png").is_file()


def test_plot_line_series_with_filename(cube, tmp_working_dir):
    """Save a line series plot with specific filename and series coordinate."""
    cube = collapse.collapse(cube, ["time", "grid_longitude"], "MEAN")
    plot.plot_line_series(
        cube, filename="latitude_average.ext", series_coordinate="grid_latitude"
    )
    assert Path("latitude_average.png").is_file()


def test_plot_line_series_no_series_coordinate(tmp_working_dir):
    """Error when cube is missing series coordinate (time)."""
    cube = iris.cube.Cube([], var_name="nothing")
    with pytest.raises(ValueError):
        plot.plot_line_series(cube)


def test_plot_line_series_too_many_dimensions(cube, tmp_working_dir):
    """Error when cube has more than one dimension."""
    with pytest.raises(ValueError):
        plot.plot_line_series(cube)


def test_plot_vertical_line_series(vertical_profile_cube, tmp_working_dir):
    """Save a vertical line series plot."""
    plot.plot_vertical_line_series(
        vertical_profile_cube, series_coordinate="pressure", sequence_coordinate="time"
    )
    assert Path("untitled_473718.0.png").is_file()
    assert Path("untitled_473721.0.png").is_file()


def test_plot_vertical_line_series_with_filename(
    vertical_profile_cube, tmp_working_dir
):
    """Save a vertical line series plot with specific filename.

    The given filename does not haven extension to test that too.
    """
    plot.plot_vertical_line_series(
        vertical_profile_cube,
        filename="Test",
        series_coordinate="pressure",
        sequence_coordinate="time",
    )
    assert Path("Test_473718.0.png").is_file()
    assert Path("Test_473721.0.png").is_file()


def test_plot_vertical_line_series_no_series_coordinate(
    vertical_profile_cube, tmp_working_dir
):
    """Error when cube is missing series coordinate (pressure)."""
    vertical_profile_cube.remove_coord("pressure")
    with pytest.raises(ValueError, match="Cube must have a pressure coordinate."):
        plot.plot_vertical_line_series(
            vertical_profile_cube, series_coordinate="pressure"
        )


def test_plot_vertical_line_series_no_sequence_coordinate(
    vertical_profile_cube, tmp_working_dir
):
    """Error when cube is missing sequence coordinate (time)."""
    vertical_profile_cube.remove_coord("time")
    with pytest.raises(ValueError, match="Cube must have a time coordinate."):
        plot.plot_vertical_line_series(
            vertical_profile_cube, series_coordinate="pressure"
        )


def test_plot_vertical_line_series_too_many_dimensions(cube, tmp_working_dir):
    """Error when cube has more than one dimension."""
    with pytest.raises(
        ValueError, match="Cube must have a model_level_number coordinate."
    ):
        plot.plot_vertical_line_series(cube)


def test_plot_histogram_no_sequence_coordinate(histogram_cube, tmp_working_dir):
    """Error when cube is missing sequence coordinate (time)."""
    histogram_cube.remove_coord("time")
    with pytest.raises(ValueError, match="Cube must have a time coordinate."):
        plot.plot_histogram_series(histogram_cube, series_coordinate="pressure")


def test_plot_histogram_with_filename(histogram_cube, tmp_working_dir):
    """Plot sequence of contour plots."""
    plot.plot_histogram_series(
        histogram_cube, filename="test", sequence_coordinate="time"
    )
    assert Path("test_473718.0.png").is_file()
