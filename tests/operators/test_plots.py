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

"""Test plotting operators."""

import json
from pathlib import Path

import iris.cube
import matplotlib as mpl
import numpy as np
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


def test_load_colorbar_map():
    """Colorbar is loaded correctly."""
    colorbar = plot._load_colorbar_map()
    assert isinstance(colorbar, dict)
    # Check we can find an example definition.
    assert colorbar["temperature_at_screen_level"] == {
        "cmap": "RdYlBu_r",
        "max": 323,
        "min": 223,
    }


def test_load_colorbar_map_override(tmp_path):
    """Colorbar is loaded correctly and overridden by the user definition."""
    # Setup a user provided colorbar override.
    user_definition = {"temperature_at_screen_level": {"max": 1000, "min": 0}}
    user_colorbar_file = tmp_path / "colorbar.json"
    with open(user_colorbar_file, "wt") as fp:
        json.dump(user_definition, fp)

    colorbar = plot._load_colorbar_map(user_colorbar_file)

    assert isinstance(colorbar, dict)
    # Check definition is updated.
    assert colorbar["temperature_at_screen_level"] == {
        "cmap": "RdYlBu_r",
        "max": 1000,
        "min": 0,
    }
    # Check we can still see unchanged definitions.
    assert colorbar["temperature_at_screen_level_difference"] == {
        "cmap": "bwr",
        "max": 10,
        "min": -10,
    }


def test_load_colorbar_map_override_file_not_found(tmp_path):
    """Colorbar overridden by the user definition in non-existent file."""
    user_colorbar_file = tmp_path / "colorbar.json"
    colorbar = plot._load_colorbar_map(user_colorbar_file)
    # Check it still returns the built-in one.
    assert isinstance(colorbar, dict)


def test_colorbar_map_levels(cube, tmp_working_dir):
    """Colorbar definition is found for cube."""
    cmap, levels, norm = plot._colorbar_map_levels(cube)
    assert cmap == mpl.colormaps["RdYlBu_r"]
    assert (levels == np.linspace(223, 323, 51)).all()
    assert norm is None


# Test will fail (but not cause an overall fail) as we can't test using levels
# until there is at least one variable that uses them.
@pytest.mark.xfail(reason="No colorbar currently uses levels")
def test_colorbar_map_levels_def_on_levels(cube, tmp_working_dir):
    """Colorbar definition that uses levels is found for cube."""
    cmap, levels, norm = plot._colorbar_map_levels(cube)
    assert cmap == mpl.colormaps[...]
    assert levels == [1, 2, 3]
    assert norm == ...


def test_colorbar_map_levels_name_fallback(cube, tmp_working_dir):
    """Colorbar definition is found for cube after checking its other names."""
    cube.standard_name = None
    cmap, levels, norm = plot._colorbar_map_levels(cube)
    assert cmap == mpl.colormaps["RdYlBu_r"]
    assert (levels == np.linspace(223, 323, 51)).all()
    assert norm is None


def test_colorbar_map_levels_unknown_variable_fallback(cube, tmp_working_dir):
    """Colorbar definition doesn't exist for cube."""
    cube.standard_name = None
    cube.long_name = None
    cube.var_name = "unknown"
    cmap, levels, norm = plot._colorbar_map_levels(cube)
    assert cmap == mpl.colormaps["viridis"]
    assert levels is None
    assert norm is None


def test_colorbar_map_levels_pressure_level(transect_source_cube, tmp_working_dir):
    """Pressure level specific colorbar definition is picked up."""
    cube_250hPa = transect_source_cube.extract(iris.Constraint(pressure=250))
    cmap, levels, norm = plot._colorbar_map_levels(cube_250hPa)
    assert cmap == mpl.colormaps["RdYlBu_r"]
    assert (levels == np.linspace(200, 240, 51)).all()
    assert norm is None


def test_spatial_contour_plot(cube, tmp_working_dir):
    """Plot spatial contour plot of instant air temp."""
    # Remove realization coord to increase coverage, and as its not needed.
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
    cube.remove_coord("time")
    with pytest.raises(ValueError):
        plot.spatial_contour_plot(cube)


def test_spatial_pcolormesh_plot(cube, tmp_working_dir):
    """Plot spatial pcolormesh plot of instant air temp."""
    # Remove realization coord to increase coverage, and as its not needed.
    cube.remove_coord("realization")
    cube_2d = cube.slices_over("time").next()
    plot.spatial_pcolormesh_plot(cube_2d, filename="plot")
    assert Path("plot_462147.0.png").is_file()


def test_pcolormesh_plot_sequence(cube, tmp_working_dir):
    """Plot sequence of pcolormesh plots."""
    plot.spatial_pcolormesh_plot(cube, sequence_coordinate="time")
    assert Path("untitled_462147.0.png").is_file()
    assert Path("untitled_462148.0.png").is_file()
    assert Path("untitled_462149.0.png").is_file()


def test_postage_stamp_pcolormesh_plot(monkeypatch, tmp_path):
    """Plot postage stamp plots of ensemble data."""
    ensemble_cube = read.read_cube("tests/test_data/exeter_em*.nc")
    # Get a single time step.
    ensemble_cube_3d = next(ensemble_cube.slices_over("time"))
    monkeypatch.chdir(tmp_path)
    plot.spatial_pcolormesh_plot(ensemble_cube_3d)
    assert Path("untitled_463858.0.png").is_file()


def test_postage_stamp_pcolormesh_plot_sequence_coord_check(cube, tmp_working_dir):
    """Check error when cube has no time coordinate."""
    # What does this even physically mean? No data?
    cube.remove_coord("time")
    with pytest.raises(ValueError):
        plot.spatial_pcolormesh_plot(cube)


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
    assert Path("test_473721.0.png").is_file()


def test_plot_and_save_postage_stamp_histogram_series(histogram_cube, tmp_working_dir):
    """Test plotting a postage stamp histogram."""
    plot._plot_and_save_postage_stamp_histogram_series(
        cube=histogram_cube,
        filename="test.png",
        title="Test",
        stamp_coordinate="realization",
        vmin=250,
        vmax=350,
        histtype="step",
    )
    assert Path("test.png").is_file()


def test_plot_and_save_postage_stamps_in_single_plot_histogram_series(
    histogram_cube, tmp_working_dir
):
    """Test plotting a multiline histogram for multiple ensemble members."""
    plot._plot_and_save_postage_stamps_in_single_plot_histogram_series(
        cube=histogram_cube,
        filename="test.png",
        title="Test",
        stamp_coordinate="realization",
        vmin=250,
        vmax=350,
        histtype="step",
    )
    assert Path("test.png").is_file()


def test_scatter_plot(cube, vertical_profile_cube, tmp_working_dir):
    """Save a scatter plot."""
    cube_y = collapse.collapse(cube, ["time", "grid_longitude"], "MEAN")[0:4]
    cube_x = collapse.collapse(vertical_profile_cube, ["time"], "MEAN")[0:4]
    plot.scatter_plot(
        cube_y,
        cube_x,
    )
    assert Path("untitled.png").is_file()


def test_scatter_plot_with_filename(cube, vertical_profile_cube, tmp_working_dir):
    """Save a scatter plot with a file name."""
    cube_y = collapse.collapse(cube, ["time", "grid_longitude"], "MEAN")[0:4]
    cube_x = collapse.collapse(vertical_profile_cube, ["time"], "MEAN")[0:4]
    plot.scatter_plot(
        cube_y,
        cube_x,
        filename="scatter_plot.ext",
    )
    assert Path("scatter_plot.png").is_file()


def test_scatter_plot_no_one_to_one_line(cube, vertical_profile_cube, tmp_working_dir):
    """Save a scatter plot without a one-to-one line."""
    cube_y = collapse.collapse(cube, ["time", "grid_longitude"], "MEAN")[0:4]
    cube_x = collapse.collapse(vertical_profile_cube, ["time"], "MEAN")[0:4]
    plot.scatter_plot(
        cube_y,
        cube_x,
        one_to_one=False,
    )
    assert Path("untitled.png").is_file()


def test_scatter_plot_too_many_x_dimensions(
    cube, vertical_profile_cube, tmp_working_dir
):
    """Error when cube_x has more than one dimension."""
    cube_y = collapse.collapse(cube, ["time", "grid_longitude"], "MEAN")[0:4]
    cube_x = vertical_profile_cube.copy()
    with pytest.raises(ValueError):
        plot.scatter_plot(cube_x, cube_y)


def test_scatter_plot_too_many_y_dimensions(
    cube, vertical_profile_cube, tmp_working_dir
):
    """Error when cube_y has more than one dimension."""
    cube_y = cube.copy()
    cube_x = collapse.collapse(vertical_profile_cube, ["time"], "MEAN")[0:4]
    with pytest.raises(ValueError):
        plot.scatter_plot(cube_x, cube_y)


def test_get_plot_resolution(tmp_working_dir):
    """Test getting the plot resolution."""
    with open("meta.json", "wt", encoding="UTF-8") as fp:
        fp.write('{"plot_resolution": 72}')
    resolution = plot._get_plot_resolution()
    assert resolution == 72


def test_get_plot_resolution_unset(tmp_working_dir):
    """Test getting the default plot resolution when unset."""
    resolution = plot._get_plot_resolution()
    assert resolution == 100


def test_invalid_plotting_method_spatial_plot(cube, tmp_working_dir):
    """Test plotting a spatial plot with an invalid method."""
    with pytest.raises(ValueError, match="Unknown plotting method"):
        plot._plot_and_save_spatial_plot(cube, "filename", "title", "invalid")


def test_invalid_plotting_method_postage_stamp_spatial_plot(cube, tmp_working_dir):
    """Test plotting a postage stamp spatial plot with an invalid method."""
    with pytest.raises(ValueError, match="Unknown plotting method"):
        plot._plot_and_save_postage_stamp_spatial_plot(
            cube, "filename", "realization", "title", "invalid"
        )


def test_append_to_plot_index(monkeypatch, tmp_working_dir):
    """Ensure the datetime is written along with the plot index."""
    # Setup environment and required file.
    monkeypatch.setenv("CYLC_TASK_CYCLE_POINT", "20000101T0000Z")
    with open("meta.json", "wt") as fp:
        fp.write('{"plots":["plot_1"]}\n')

    plot._append_to_plot_index(["plot_2"])

    with open("meta.json", "rt") as fp:
        meta = json.load(fp)
    assert meta == {"plots": ["plot_1", "plot_2"], "case_date": "20000101T0000Z"}
    assert "datetime" not in meta


def test_append_to_plot_index_case_aggregation_no_datetime(
    monkeypatch, tmp_working_dir
):
    """Ensure the datetime is not written for aggregation plots."""
    # Setup environment and required file.
    monkeypatch.setenv("CYLC_TASK_CYCLE_POINT", "20000101T0000Z")
    monkeypatch.setenv(
        "CYLC_TASK_NAMESPACE_HIERARCHY", "root PROCESS_CASE_AGGREGATION task_name"
    )
    with open("meta.json", "wt") as fp:
        fp.write("{}\n")

    plot._append_to_plot_index(["plot_1"])

    with open("meta.json", "rt") as fp:
        meta = json.load(fp)
    assert "case_date" not in meta
