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

"""Test plotting operators."""

import json
import logging
from pathlib import Path

import cartopy.crs as ccrs
import iris.coords
import iris.cube
import matplotlib as mpl
import numpy as np
import pytest

from CSET.operators import collapse, constraints, filters, plot, read


def test_setup_spatial_map(cube):
    """Setup spatial map."""
    # Test setup map function returns GeoAxes instance.
    figure = mpl.figure.Figure()
    axes = plot._setup_spatial_map(cube, figure, mpl.colormaps["viridis"])
    assert axes == figure.gca()
    # Test bounds - set as global as rotated pole input.
    bounds = axes.get_extent()
    assert bounds[0] == -180.0
    assert bounds[1] == 180.0
    assert bounds[2] == -90.0
    assert bounds[3] == 90.0


def test_setup_spatial_map_dateline(cube):
    """Setup spatial map for dateline-crossing example."""
    # Test for cube crossing dateline example.
    cube = read.read_cubes("tests/test_data/air_temperature_dateline.nc")[0]
    figure = mpl.figure.Figure()
    axes_dl = plot._setup_spatial_map(cube, figure, mpl.colormaps["viridis"])
    assert axes_dl == figure.gca()
    # Test map bounds based on known pre-set domain KGO values.
    bounds = axes_dl.get_extent()
    assert round(bounds[0], 2) == -6.99
    assert round(bounds[1], 2) == 1.65
    assert round(bounds[2], 2) == -41.99
    assert round(bounds[3], 2) == -33.35


def test_setup_spatial_map_global(cube):
    """Setup spatial map for global cube example."""
    # Test for global cube example.
    cube = read.read_cubes("tests/test_data/air_temperature_global.nc")[0]
    figure = mpl.figure.Figure()
    axes_gl = plot._setup_spatial_map(cube, figure, mpl.colormaps["viridis"])
    assert axes_gl == figure.gca()
    # Test map bounds based on cube-relative calculation of KGO values.
    bounds = axes_gl.get_extent()
    assert bounds[0] == np.min(cube.coord("longitude").points) - 180.0
    assert bounds[1] == np.max(cube.coord("longitude").points) - 180.0
    assert bounds[2] == np.min(cube.coord("latitude").points)
    assert bounds[3] == np.max(cube.coord("latitude").points)


def test_setup_spatial_map_npole(north_polar_cube):
    """Setup spatial map for Arctic example."""
    figure = mpl.figure.Figure()
    axes_gl = plot._setup_spatial_map(
        north_polar_cube, figure, mpl.colormaps["viridis"]
    )
    assert axes_gl == figure.gca()
    assert axes_gl.projection == ccrs.NorthPolarStereo(central_longitude=0.0)


def test_setup_spatial_map_spole(south_polar_cube):
    """Setup spatial map for Antarctic example."""
    figure = mpl.figure.Figure()
    axes_gl = plot._setup_spatial_map(
        south_polar_cube, figure, mpl.colormaps["viridis"]
    )
    assert axes_gl == figure.gca()
    assert axes_gl.projection == ccrs.SouthPolarStereo(central_longitude=180.0)


def test_setup_spatial_map_nocoast(cube):
    """Setup spatial map without coastline default."""
    cube.rename("surface_altitude")
    figure = mpl.figure.Figure()
    axes_gl = plot._setup_spatial_map(cube, figure, mpl.colormaps["viridis"])
    assert axes_gl == figure.gca()


def test_set_title_and_filename_filename_single_sequence(cube):
    """Setup plot title and filename for single output, sequence input."""
    seq_coord = cube.coord("time")
    nplot = 1
    plot_title, plot_filename = plot._set_title_and_filename(
        seq_coord, nplot, "recipe", "filename"
    )
    assert plot_filename == "filename.png"
    assert plot_title == "recipe\n [2022-09-21 03:00:00 to 2022-09-21 05:00:00]"


def test_set_title_and_filename_filename_single_nosequence(cube):
    """Setup plot title and filename for single output, no sequence."""
    seq_coord = cube.coord("time")[0]
    nplot = np.size(cube.coord("time").points)
    plot_title, plot_filename = plot._set_title_and_filename(
        seq_coord, nplot, "recipe", "filename"
    )
    assert plot_filename == "filename_20220921030000.png"
    assert plot_title == "recipe\n [2022-09-21 03:00:00]"


def test_set_title_and_filename_nofilename_single_sequence(cube):
    """Setup plot title and filename for single output with multi-sequence."""
    seq_coord = cube.coord("time")
    nplot = 1
    plot_title, plot_filename = plot._set_title_and_filename(
        seq_coord, nplot, "recipe", None
    )
    assert plot_filename == "recipe_20220921030000_20220921050000.png"
    assert plot_title == "recipe\n [2022-09-21 03:00:00 to 2022-09-21 05:00:00]"


def test_set_title_and_filename_nofilename_single_nobounds(cube):
    """Setup plot title and filename for single output with single sequence."""
    seq_coord = cube.coord("time")[0]
    seq_coord.bounds = None
    nplot = 1
    plot_title, plot_filename = plot._set_title_and_filename(
        seq_coord, nplot, "recipe", None
    )
    assert plot_filename == "recipe_20220921030000.png"
    assert plot_title == "recipe\n [2022-09-21 03:00:00]"


def test_set_title_and_filename_nofilename_multi_sequence(cube):
    """Setup plot title and filename for sequence output."""
    seq_coord = cube.coord("time")[0]
    nplot = np.size(cube.coord("time").points)
    plot_title, plot_filename = plot._set_title_and_filename(
        seq_coord, nplot, "recipe", None
    )
    assert plot_filename == "recipe_20220921030000.png"
    assert plot_title == "recipe\n [2022-09-21 03:00:00]"


def test_set_title_and_filename_filename_aggregated(long_forecast_multi_day):
    """Setup plot title and filename for aggregated output with filename."""
    collapsed_cube = collapse.collapse_by_hour_of_day(long_forecast_multi_day, "MEAN")
    seq_coord = collapsed_cube.coord("hour")
    nplot = 1
    plot_title, plot_filename = plot._set_title_and_filename(
        seq_coord, nplot, "recipe", "filename"
    )
    assert plot_filename == "filename.png"
    assert plot_title == "recipe\n [0 hours to 23 hours]"


def test_set_title_and_filename_nofilename_aggregated(long_forecast_multi_day):
    """Setup plot title and filename for aggregated output, no filename."""
    collapsed_cube = collapse.collapse_by_hour_of_day(long_forecast_multi_day, "MEAN")
    seq_coord = collapsed_cube.coord("hour")
    nplot = 1
    plot_title, plot_filename = plot._set_title_and_filename(
        seq_coord, nplot, "recipe", None
    )
    assert plot_filename == "recipe_0hours_23hours.png"
    assert plot_title == "recipe\n [0 hours to 23 hours]"


def test_set_title_and_filename_multidim_aggregated(long_forecast_multi_day):
    """Setup plot title and filename for 2D time aggregated output (3 cases)."""
    seq_coord = long_forecast_multi_day.coord("time")
    nplot = 1
    plot_title, plot_filename = plot._set_title_and_filename(
        seq_coord, nplot, "recipe", None
    )
    assert plot_filename == "recipe_3cases.png"
    assert plot_title == "recipe\n [3 cases]"


def test_set_title_and_filename_reference_time(cube):
    """Setup plot title and filename for single input with reference time attribute."""
    cube.coord("time").attributes["number_reference_times"] = 10
    seq_coord = cube.coord("time")[0]
    nplot = 1
    plot_title, plot_filename = plot._set_title_and_filename(
        seq_coord, nplot, "recipe", None
    )
    assert plot_filename == "recipe_10cases.png"
    assert plot_title == "recipe\n [10 cases]"


def test_set_title_and_filename_year_one(cube):
    """Ensure no time information in plot title and filename for dummy time output."""
    # Extract first time from test cube.
    cube = cube[0]
    # Set time coordinate to 0001-01-01 0hrs and remove bounds.
    cube.coord("time").units = "hours since 0001-01-01 00:00:00"
    cube.coord("time").points = 0
    cube.coord("time").bounds = None
    seq_coord = cube.coord("time")
    # Check no time information added to plot title or filename
    nplot = 1
    plot_title, plot_filename = plot._set_title_and_filename(
        seq_coord, nplot, "recipe", None
    )
    assert plot_filename == "recipe.png"
    assert plot_title == "recipe"


def test_set_axis_range_single_cube(cube, tmp_working_dir):
    """Test _set_axis_range with a single cube, without levels set."""
    cubes = iris.cube.CubeList([cube])

    vmin, vmax = plot._set_axis_range(cubes)

    assert vmin == cube.data.min()
    assert vmax == cube.data.max()


def test_set_axis_range_cubelist(cube, tmp_working_dir):
    """Test _set_axis_range with a cubelist, without levels set."""
    cubes = iris.cube.CubeList([cube, 2.0 * cube])

    vmin, vmax = plot._set_axis_range(cubes)

    assert vmin == cube.data.min()
    assert vmax == 2.0 * cube.data.max()


def test_set_axis_range_levels(cube, tmp_working_dir):
    """Test _set_axis_range with a single cube, for variable with levels set."""
    cube.rename("land_binary_mask")
    cubes = iris.cube.CubeList([cube])

    vmin, vmax = plot._set_axis_range(cubes)

    assert vmin == 0.0
    assert vmax == 1.0


def test_spatial_contour_plot(cube, tmp_working_dir):
    """Plot spatial contour plot of instant air temp."""
    # Remove realization coord to increase coverage, and as its not needed.
    cube.remove_coord("realization")
    cube_2d = cube.slices_over("time").next()
    plot.spatial_contour_plot(cube_2d, filename="plot")
    assert Path("plot.png").is_file()


def test_contour_plot_sequence(cube, tmp_working_dir):
    """Plot sequence of contour plots."""
    plot.spatial_contour_plot(cube, sequence_coordinate="time")
    assert Path("air_temperature_20220921030000.png").is_file()
    assert Path("air_temperature_20220921040000.png").is_file()
    assert Path("air_temperature_20220921050000.png").is_file()


def test_spatial_multi_variable_plot(cube, tmp_working_dir):
    """Plot spatial plot with multiple input variables."""
    # Here assume cube provides cube, overlay_cube and contour_cube.
    plot.spatial_multi_pcolormesh_plot(cube, cube, cube, sequence_coordinate="time")
    assert Path("air_temperature_20220921030000.png").is_file()
    assert Path("air_temperature_20220921040000.png").is_file()
    assert Path("air_temperature_20220921050000.png").is_file()


def test_spatial_multi_variable_plot_nolayers(cube, tmp_working_dir):
    """Plot spatial plot with single input cube only."""
    # Call spatial_multi_pcolormesh_plot with only cube as input.
    plot.spatial_multi_pcolormesh_plot(cube[0], sequence_coordinate="time")
    assert Path("air_temperature_20220921030000.png").is_file()


def test_spatial_multi_variable_plot_overlay_only(cube, tmp_working_dir):
    """Plot spatial plot with based and overlay cube only."""
    # Call spatial_multi_pcolormesh_plot with only cube and overlay_cube.
    plot.spatial_multi_pcolormesh_plot(
        cube[0], overlay_cube=cube[0], sequence_coordinate="time"
    )
    assert Path("air_temperature_20220921030000.png").is_file()


def test_spatial_multi_variable_plot_contour_only(cube, tmp_working_dir):
    """Plot spatial plot with based and contour cube only."""
    # Call spatial_multi_pcolormesh_plot with only cube and contour_cube.
    plot.spatial_multi_pcolormesh_plot(
        cube[0], contour_cube=cube[0], sequence_coordinate="time"
    )
    assert Path("air_temperature_20220921030000.png").is_file()


@pytest.mark.slow
def test_vector_plot_with_filename(vector_cubes, tmp_working_dir):
    """Plot a vector plot of u10 and v10 components."""
    cube_u = vector_cubes[0].slices_over("time").next()
    cube_v = vector_cubes[1].slices_over("time").next()
    plot.vector_plot(cube_u, cube_v, filename="testvector")
    assert Path("testvector.png").is_file()


@pytest.mark.slow
def test_vector_plot_sequence(vector_cubes, tmp_working_dir):
    """Plot a sequence of vector plots."""
    plot.vector_plot(
        vector_cubes[0],
        vector_cubes[1],
        filename="testvectorseq",
        sequence_coordinate="time",
    )
    assert Path("testvectorseq.png").is_file()
    assert Path("testvectorseq.png").is_file()
    assert Path("testvectorseq.png").is_file()


def test_vector_plot_check(vector_cubes, tmp_working_dir):
    """Check error when cubes has no time coordinate."""
    vector_cubes[0].remove_coord("time")
    vector_cubes[1].remove_coord("time")
    with pytest.raises(ValueError):
        plot.vector_plot(
            vector_cubes[0],
            vector_cubes[1],
            filename="testvector",
            sequence_coordinate="time",
        )


def test_postage_stamp_contour_plot(ensemble_cube, tmp_working_dir):
    """Plot postage stamp plots of ensemble data."""
    # Get a single time step.
    ensemble_cube_3d = next(ensemble_cube.slices_over("time"))
    plot.spatial_contour_plot(ensemble_cube_3d)
    assert Path("air_temperature_20221201100000.png").is_file()


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
    assert Path("plot.png").is_file()


def test_spatial_pcolormesh_levels(cube, tmp_working_dir, caplog):
    """Plot spatial pcolormesh based on defined levels."""
    # Pick a variable with defined levels
    cube.rename("surface_microphysical_rainfall_rate")
    with caplog.at_level(logging.DEBUG):
        plot.spatial_pcolormesh_plot(cube, sequence_coordinate="time")
        message_matchA = False
        message_matchB = False
        for _, _, message in caplog.record_tuples:
            if message == "Plotting using defined levels.":
                message_matchA = True
            if message == "Set colorbar ticks and labels.":
                message_matchB = True
        assert message_matchA
        assert message_matchB
    assert Path("surface_microphysical_rainfall_rate_20220921030000.png").is_file()
    assert Path("surface_microphysical_rainfall_rate_20220921040000.png").is_file()
    assert Path("surface_microphysical_rainfall_rate_20220921050000.png").is_file()


def test_pcolormesh_plot_sequence(cube, tmp_working_dir):
    """Plot sequence of pcolormesh plots."""
    plot.spatial_pcolormesh_plot(cube, sequence_coordinate="time")
    assert Path("air_temperature_20220921030000.png").is_file()
    assert Path("air_temperature_20220921040000.png").is_file()
    assert Path("air_temperature_20220921050000.png").is_file()


def test_pcolormesh_plot_global(global_cube, caplog, tmp_working_dir):
    """Plot global lat-lon cube."""
    with caplog.at_level(logging.DEBUG):
        plot.spatial_pcolormesh_plot(global_cube)
        message_match = False
        for _, _, message in caplog.record_tuples:
            if message == "Adjusting plot bounds to fit global extent.":
                message_match = True
    assert message_match


def test_spatial_scatter(cube, tmp_working_dir):
    """Save a spatial plot with scatter of cube points."""
    cube.coord("grid_latitude").rename("station")
    plot.spatial_pcolormesh_plot(cube, sequence_coordinate="time")
    assert Path("air_temperature_20220921030000.png").is_file()
    assert Path("air_temperature_20220921040000.png").is_file()
    assert Path("air_temperature_20220921050000.png").is_file()


def test_postage_stamp_pcolormesh_plot(ensemble_cube, tmp_working_dir):
    """Plot postage stamp plots of ensemble data."""
    # Get a single time step.
    ensemble_cube_3d = next(ensemble_cube.slices_over("time"))
    plot.spatial_pcolormesh_plot(ensemble_cube_3d)
    assert Path("air_temperature_20221201100000.png").is_file()


def test_postage_stamp_pcolormesh_plot_sequence_coord_check(cube, tmp_working_dir):
    """Check error when cube has no time coordinate."""
    # What does this even physically mean? No data?
    cube.remove_coord("time")
    with pytest.raises(ValueError):
        plot.spatial_pcolormesh_plot(cube)


def test_pcolormesh_coastline(cube, caplog, tmp_working_dir):
    """Check coastlines and borderlines plotted in black for air_temperature colormap."""
    with caplog.at_level(logging.DEBUG):
        plot.spatial_pcolormesh_plot(cube)
        message_match = False
        for _, _, message in caplog.record_tuples:
            if message == "Plotting coastlines and borderlines in colour black.":
                message_match = True
        assert message_match


def test_pcolormesh_coastline_m(cube, caplog, tmp_working_dir):
    """Check coastlines and borderlines plotted in magenta for viridis colormap."""
    with caplog.at_level(logging.DEBUG):
        # Set cube name to unknown to trigger viridis default cmap
        cube.rename("unknown_var_name")
        plot.spatial_pcolormesh_plot(cube)
        message_match = False
        for _, _, message in caplog.record_tuples:
            if message == "Plotting coastlines and borderlines in colour magenta.":
                message_match = True
        assert message_match


def test_plot_line_series(cube, tmp_working_dir):
    """Save a line series plot."""
    cube = collapse.collapse(cube, ["grid_latitude", "grid_longitude"], "MEAN")
    plot.plot_line_series(cube)
    assert Path("air_temperature_20220921030000_20220921050000.png").is_file()


def test_plot_power_spectrum(power_spectrum_cube_readonly, tmp_working_dir):
    """Save a power_spectrum plot using line series plot."""
    plot.plot_line_series(power_spectrum_cube_readonly, series_coordinate="frequency")
    assert Path("power_spectra_20220601000000.png").is_file()


def test_plot_line_series_with_filename(cube, tmp_working_dir):
    """Save a line series plot with specific filename and series coordinate."""
    cube = collapse.collapse(cube, ["time", "grid_longitude"], "MEAN")
    plot.plot_line_series(
        cube, filename="latitude_average.ext", series_coordinate="grid_latitude"
    )
    assert Path("latitude_average.png").is_file()


def test_plot_power_spectrum_with_filename(
    power_spectrum_cube_readonly, tmp_working_dir
):
    """Testing power spectrum plot in plot_line_series produces file."""
    plot.plot_line_series(
        power_spectrum_cube_readonly, series_coordinate="frequency", filename="test"
    )
    assert Path("test.png").is_file()


def test_plot_line_series_no_series_coordinate(tmp_working_dir):
    """Error when cube is missing series coordinate (time)."""
    cube = iris.cube.Cube([], var_name="nothing")
    with pytest.raises(ValueError):
        plot.plot_line_series(cube)


def test_plot_power_spectrum_no_sequence_coordinate(
    power_spectrum_cube, tmp_working_dir
):
    """Error when cube is missing sequence coordinate (time)."""
    power_spectrum_cube.remove_coord("time")
    with pytest.raises(ValueError, match="Cube must have a time coordinate."):
        plot.plot_line_series(power_spectrum_cube, series_coordinate="frequency")


def test_select_series_coord_frequency_fallback(power_spectrum_cube):
    """Select a valid fallback when frequency is missing."""
    freq = power_spectrum_cube.coord("frequency")
    dims = power_spectrum_cube.coord_dims(freq)
    # Remove frequency
    power_spectrum_cube.remove_coord("frequency")
    # Add both possible fallbacks
    pw = iris.coords.DimCoord(freq.points, long_name="physical_wavenumber")
    wl = iris.coords.DimCoord(freq.points, long_name="wavelength")
    power_spectrum_cube.add_aux_coord(pw, dims)
    power_spectrum_cube.add_aux_coord(wl, dims)
    xcoord = plot._select_series_coord(power_spectrum_cube, "frequency")
    assert xcoord.name() in {"physical_wavenumber", "wavelength"}


def test_select_series_coord_frequency_fallback_wavelength(power_spectrum_cube):
    """Select wavelength when it's the only fallback."""
    freq = power_spectrum_cube.coord("frequency")
    dims = power_spectrum_cube.coord_dims(freq)
    power_spectrum_cube.remove_coord("frequency")
    wl = iris.coords.DimCoord(freq.points, long_name="wavelength")
    power_spectrum_cube.add_aux_coord(wl, dims)
    xcoord = plot._select_series_coord(power_spectrum_cube, "frequency")
    assert xcoord.name() == "wavelength"


def test_select_series_coord_frequency_multiple_fallbacks(power_spectrum_cube):
    """Select any valid fallback when multiple exist."""
    freq = power_spectrum_cube.coord("frequency")
    dims = power_spectrum_cube.coord_dims(freq)
    power_spectrum_cube.remove_coord("frequency")
    pw = iris.coords.DimCoord(freq.points, long_name="physical_wavenumber")
    wl = iris.coords.DimCoord(freq.points, long_name="wavelength")
    power_spectrum_cube.add_aux_coord(pw, dims)
    power_spectrum_cube.add_aux_coord(wl, dims)
    xcoord = plot._select_series_coord(power_spectrum_cube, "frequency")
    assert xcoord.name() in {"physical_wavenumber", "wavelength"}


def test_select_series_coord_no_fallbacks(power_spectrum_cube):
    """Raise error when no valid coordinates exist."""
    power_spectrum_cube.remove_coord("frequency")
    with pytest.raises(iris.exceptions.CoordinateNotFoundError):
        plot._select_series_coord(power_spectrum_cube, "frequency")


def test_plot_line_series_too_many_dimensions(cube, tmp_working_dir):
    """Error when cube has more than one dimension."""
    with pytest.raises(ValueError):
        plot.plot_line_series(cube)


def test_plot_line_series_different_coord_lengths(tmp_working_dir):
    """Save a line series plot with specific filename and series coordinate."""
    ens_coord = iris.coords.DimCoord(0, standard_name="realization", units="1")
    coord1 = iris.coords.DimCoord(
        [0, 1, 2, 3], standard_name="time", units="hours since 1970-01-01"
    )
    cube1 = iris.cube.Cube(
        [0, 1, 2, 3],
        long_name="my_var",
        dim_coords_and_dims=[(coord1, 0)],
        aux_coords_and_dims=[(ens_coord, None)],
        attributes={"model_name": "m1"},
    )
    coord2 = iris.coords.DimCoord(
        [1, 2, 3], standard_name="time", units="hours since 1970-01-01"
    )
    cube2 = iris.cube.Cube(
        [3, 2, 1],
        long_name="my_var",
        dim_coords_and_dims=[(coord2, 0)],
        aux_coords_and_dims=[(ens_coord, None)],
        attributes={"model_name": "m2"},
    )
    cubes = iris.cube.CubeList([cube1, cube2])

    plot.plot_line_series(cubes, filename="plot.png")
    assert Path("plot.png").is_file()


def test_plot_line_series_ensemble(ensemble_cube, tmp_working_dir):
    """Save an ensemble line series plot."""
    ensemble_cube = collapse.collapse(
        ensemble_cube, ["grid_latitude", "grid_longitude"], "MEAN"
    )
    plot.plot_line_series(ensemble_cube, filename="ensemble_series.ext")
    assert Path("ensemble_series.png").is_file()


def test_plot_and_save_postage_stamp_power_spectrum_series_single_member(
    tmp_working_dir,
):
    """Test plotting a postage stamp power_spectrum for single ensemble member."""
    # Create single member 1D PSD cube

    freq = iris.coords.DimCoord(np.arange(420), long_name="physical_wavenumber")
    real = iris.coords.DimCoord([0], long_name="realization")
    data = np.random.rand(1, 420)
    cube = iris.cube.Cube(
        data, dim_coords_and_dims=[(real, 0), (freq, 1)], long_name="power_spectra"
    )

    coords = cube.coords()

    plot._plot_and_save_postage_stamp_power_spectrum_series(
        cubes=cube,
        coords=coords,
        stamp_coordinate="realization",
        filename="test.png",
        title="Test",
        series_coordinate="physical_wavenumber",
    )
    assert Path("test.png").is_file()


def test_plot_and_save_postage_stamp_power_spectrum_series_multi_member(
    tmp_working_dir,
):
    """Test plotting a postage stamp power_spectrum for multiple ensemble members."""
    # Create two-realization 1D PSD cube
    freq = iris.coords.DimCoord(np.arange(420), long_name="physical_wavenumber")
    real = iris.coords.DimCoord([0, 1], long_name="realization")
    data = np.random.rand(2, 420)
    cube = iris.cube.Cube(
        data, dim_coords_and_dims=[(real, 0), (freq, 1)], long_name="power_spectra"
    )

    coords = cube.coords()

    plot._plot_and_save_postage_stamp_power_spectrum_series(
        cubes=cube,
        coords=coords,
        stamp_coordinate="realization",
        filename="test.png",
        title="Test",
        series_coordinate="physical_wavenumber",
    )
    assert Path("test.png").is_file()


def test_plot_and_save_postage_stamps_in_single_plot_power_spectrum_series_single_member(
    tmp_working_dir,
):
    """Test plotting a multiline power_spectrum for multiple ensemble members."""
    # Create two-realization 1D PSD cube
    freq = iris.coords.DimCoord(np.arange(420), long_name="physical_wavenumber")
    real = iris.coords.DimCoord([0], long_name="realization")
    data = np.random.rand(1, 420)
    cube = iris.cube.Cube(
        data, dim_coords_and_dims=[(real, 0), (freq, 1)], long_name="power_spectra"
    )

    cube.attributes["model_name"] = "UM"

    coords = cube.coords()

    plot._plot_and_save_postage_stamps_in_single_plot_power_spectrum_series(
        cubes=cube,
        coords=coords,
        stamp_coordinate="realization",
        filename="test.png",
        title="Test",
        series_coordinate="physical_wavenumber",
    )
    assert Path("test.png").is_file()


def test_plot_and_save_postage_stamps_in_single_plot_power_spectrum_series_multi_member(
    tmp_working_dir,
):
    """Test plotting a multiline power_spectrum for multiple ensemble members."""
    # Create two-realization 1D PSD cube
    freq = iris.coords.DimCoord(np.arange(420), long_name="physical_wavenumber")
    real = iris.coords.DimCoord([0, 1], long_name="realization")
    data = np.random.rand(2, 420)
    cube = iris.cube.Cube(
        data, dim_coords_and_dims=[(real, 0), (freq, 1)], long_name="power_spectra"
    )

    cube.attributes["model_name"] = "UM"

    coords = cube.coords()

    plot._plot_and_save_postage_stamps_in_single_plot_power_spectrum_series(
        cubes=cube,
        coords=coords,
        stamp_coordinate="realization",
        filename="test.png",
        title="Test",
        series_coordinate="physical_wavenumber",
    )
    assert Path("test.png").is_file()


def test_plot_vertical_line_series(vertical_profile_cube, tmp_working_dir):
    """Save a vertical line series plot."""
    plot.plot_vertical_line_series(
        vertical_profile_cube, series_coordinate="pressure", sequence_coordinate="time"
    )
    assert Path("air_temperature_20240116060000.png").is_file()
    assert Path("air_temperature_20240116090000.png").is_file()


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
    assert Path("Test_20240116060000.png").is_file()
    assert Path("Test_20240116090000.png").is_file()


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


def test_plot_vertical_line_series_ensemble(vertical_profile_cube, tmp_working_dir):
    """Save a vertical line series plot with ensemble data."""
    # Copy cube to create extra ensemble member.
    cube2 = vertical_profile_cube.copy()
    # Remove original realization coordinate.
    cube2.remove_coord("realization")
    # Create new realization coordinate and add to cube.
    ens_coord = iris.coords.DimCoord(1, standard_name="realization", units="1")
    cube2.add_aux_coord(ens_coord)
    # Repeat process for original cube so realization coordinates identical.
    vertical_profile_cube.remove_coord("realization")
    ens_coord = iris.coords.DimCoord(0, standard_name="realization", units="1")
    vertical_profile_cube.add_aux_coord(ens_coord)
    # Create an ensemble cube.
    cubes = iris.cube.CubeList([vertical_profile_cube, cube2]).merge_cube()
    plot.plot_vertical_line_series(
        cubes, series_coordinate="pressure", sequence_coordinate="time"
    )
    assert Path("air_temperature_20240116060000.png").is_file()
    assert Path("air_temperature_20240116090000.png").is_file()


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
    assert Path("test_20240116060000.png").is_file()
    assert Path("test_20240116090000.png").is_file()


def test_plot_histogram_update_vmin_vmax(histogram_cube, tmp_working_dir, caplog):
    """Plot sequence of contour plots and check levels."""
    histogram_cube.rename("surface_microphysical_rainfall_rate")
    plot.plot_histogram_series(
        histogram_cube, filename="test", sequence_coordinate="time"
    )
    with caplog.at_level(logging.DEBUG):
        plot.plot_histogram_series(
            histogram_cube, filename="test", sequence_coordinate="time"
        )
        message_matchA = False
        message_matchB = False
        for _, _, message in caplog.record_tuples:
            if (
                message
                == "levels: [0, 0.125, 0.25, 0.5, 1, 2, 4, 8, 16, 32, 64, 128, 256]"
            ):
                message_matchA = True
            if message == "Updated vmin, vmax: 0, 256":
                message_matchB = True
        assert message_matchA
        assert message_matchB


def test_plot_histogram_single_plot(histogram_cube, tmp_working_dir):
    """Plot sequence of contour plots."""
    plot.plot_histogram_series(
        histogram_cube, filename="test", sequence_coordinate="time", single_plot=True
    )
    assert Path("test_20240116060000.png").is_file()


def test_plot_histogram_series_multi_model(histogram_cube, tmp_working_dir):
    """Test histogram plotting with multiple model inputs."""
    c1 = histogram_cube.copy()
    c1.attributes["model_name"] = "model_1"
    c2 = histogram_cube.copy()
    c2.attributes["model_name"] = "model_2"
    plot.plot_histogram_series([c1, c2], filename="test", sequence_coordinate="time")
    assert Path("test_20240116060000.png").is_file()
    assert Path("test_20240116090000.png").is_file()


def test_plot_and_save_histogram_series_bins(histogram_cube, tmp_working_dir, caplog):
    """Test plotting a postage stamp histogram."""
    with caplog.at_level(logging.DEBUG):
        plot._plot_and_save_histogram_series(
            cubes=histogram_cube,
            filename="test.png",
            title="Test",
            vmin=0,
            vmax=0,
            histtype="step",
        )
        message_match = False
        for _, _, message in caplog.record_tuples:
            if message == "Plotting histogram with 51 bins 0.0 - 0.0.":
                message_match = True
        assert message_match
    assert Path("test.png").is_file()


def test_plot_and_save_histogram_series_bins_precip(
    histogram_cube, tmp_working_dir, caplog
):
    """Test plotting a rainfall rate histogram."""
    histogram_cube.rename("surface_microphysical_rainfall_flux")
    histogram_cube.units = "kg m-2 s-1"
    with caplog.at_level(logging.DEBUG):
        plot._plot_and_save_histogram_series(
            cubes=histogram_cube,
            filename="test.png",
            title="Test surface_microphysical",
            vmin=0,
            vmax=0,
            histtype="step",
        )
        message_match = False
        for _, _, message in caplog.record_tuples:
            if message == "Plotting histogram with 38 bins 0.0 - 398.1071705534973.":
                message_match = True
        assert message_match
    assert Path("test.png").is_file()


def test_plot_and_save_histogram_series_bins_precip_amount(
    histogram_cube, tmp_working_dir, caplog
):
    """Test plotting a rainfall amount histogram."""
    histogram_cube.rename("surface_microphysical_rainfall_amount")
    histogram_cube.units = "kg m-2 s-1"
    with caplog.at_level(logging.DEBUG):
        plot._plot_and_save_histogram_series(
            cubes=histogram_cube,
            filename="test.png",
            title="Test surface_microphysical",
            vmin=0,
            vmax=0,
            histtype="step",
        )
        message_match = False
        for _, _, message in caplog.record_tuples:
            if message == "Plotting histogram with 38 bins 0.0 - 398.1071705534973.":
                message_match = True
        assert message_match
    assert Path("test.png").is_file()


def test_plot_and_save_histogram_series_bins_lightning(
    histogram_cube, tmp_working_dir, caplog
):
    """Test plotting a lightning histogram."""
    with caplog.at_level(logging.DEBUG):
        plot._plot_and_save_histogram_series(
            cubes=histogram_cube,
            filename="test.png",
            title="Test lightning",
            vmin=0,
            vmax=0,
            histtype="step",
        )
        message_match = False
        for _, _, message in caplog.record_tuples:
            if message == "Plotting histogram with 6 bins 0 - 5.":
                message_match = True
        assert message_match
    assert Path("test.png").is_file()


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
    assert Path("scatter_plot.png").is_file()


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
    assert Path("scatter_plot.png").is_file()


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


def test_get_start_end_strings_nobounds(cube):
    """Test setting (startstring, endstring) from coord points."""
    title, fname = plot._get_start_end_strings(cube.coord("time"), use_bounds=False)
    assert title == "\n [2022-09-21 03:00:00 to 2022-09-21 05:00:00]"
    assert fname == "_20220921030000_20220921050000"


def test_get_start_end_strings_bounds(cubes):
    """Test setting (startstring, endstring) from coord bounds."""
    # Get a field with time bounds
    cube = filters.filter_cubes(
        cubes,
        constraints.generate_cell_methods_constraint(
            ["minimum"], coord="time", interval="1 hour"
        ),
    )

    title, fname = plot._get_start_end_strings(cube.coord("time"), use_bounds=True)
    assert title == "\n [2022-09-21 03:00:00 to 2022-09-21 05:00:00]"
    assert fname == "_20220921030000_20220921050000"


def test_get_start_end_strings_remove_bounds(cube):
    """Test setting (startstring, endstring) from coord with no bounds."""
    title, fname = plot._get_start_end_strings(cube.coord("time"), use_bounds=True)
    assert title == "\n [2022-09-21 03:00:00 to 2022-09-21 05:00:00]"
    assert fname == "_20220921030000_20220921050000"


def test_set_ensemble_title_realization():
    """Test setting postage stamp title for different coord inputs."""
    stamp_coord = iris.coords.DimCoord([1], var_name="realization")
    assert plot._set_postage_stamp_title(stamp_coord) == "Member #1"

    stamp_coord = iris.coords.DimCoord([1], var_name="member")
    assert plot._set_postage_stamp_title(stamp_coord) == "Member #1"

    stamp_coord = iris.coords.DimCoord([1], var_name="sample")
    assert plot._set_postage_stamp_title(stamp_coord) == "Sample #1"

    stamp_coord = iris.coords.DimCoord([1], var_name="pseudo_level")
    assert plot._set_postage_stamp_title(stamp_coord) == "Pseudo_level #1"


def test_set_ensemble_title_time(cube):
    """Test setting postage stamp title for time stamp_coord input."""
    stamp_coord = cube.coord("time")
    assert plot._set_postage_stamp_title(stamp_coord) == "2022-09-21 03:00:00"


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


def test_levels_postage_stamp_spatial_plot(ensemble_cube, tmp_working_dir):
    """Test no levels raises TypeError for pcolormesh with no levels."""
    with pytest.raises(TypeError, match="Unknown vmin and vmax range."):
        ensemble_cube.rename("unknown")
        plot._plot_and_save_postage_stamp_spatial_plot(
            ensemble_cube[0], "filename", "realization", "title", "pcolormesh"
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


def test_append_to_plot_index_aggregation(monkeypatch, tmp_working_dir):
    """Ensure the datetime is not written for aggregation plots."""
    # Setup environment and required file.
    monkeypatch.setenv("CYLC_TASK_CYCLE_POINT", "20000101T0000Z")
    monkeypatch.setenv("DO_CASE_AGGREGATION", "True")
    with open("meta.json", "wt") as fp:
        fp.write("{}\n")

    plot._append_to_plot_index(["plot_1"])

    with open("meta.json", "rt") as fp:
        meta = json.load(fp)
    assert "case_date" not in meta


def test_qq_plot(cube, tmp_working_dir):
    """Test that qq plot creates an untitled image."""
    # Data preparation.
    other_cube = cube.copy()
    del other_cube.attributes["cset_comparison_base"]
    cubes = iris.cube.CubeList([cube, other_cube])
    plot.qq_plot(
        cubes,
        coordinates=["time", "grid_latitude", "grid_longitude"],
        percentiles=[0, 50, 100],
        model_names=["a", "b"],
    )
    assert Path("qq_plot.png").is_file()


def test_qq_plot_named(cube, tmp_working_dir):
    """Test that qq plot creates a named image."""
    # Data preparation.
    other_cube = cube.copy()
    del other_cube.attributes["cset_comparison_base"]
    cubes = iris.cube.CubeList([cube, other_cube])
    plot.qq_plot(
        cubes,
        coordinates=["time", "grid_latitude", "grid_longitude"],
        percentiles=[0, 50, 100],
        model_names=["a", "b"],
        filename="qq_plot.ext",
        one_to_one=True,
    )
    assert Path("qq_plot.png").is_file()


def test_qq_plot_incorrect_number_of_cubes(cube, tmp_working_dir):
    """Test exception when incorrect number of cubes provided."""
    no_cubes = iris.cube.CubeList([])
    with pytest.raises(ValueError, match="cubes should contain exactly 2 cubes."):
        plot.qq_plot(
            no_cubes,
            coordinates=["time", "grid_latitude", "grid_longitude"],
            percentiles=[0, 50, 100],
            model_names=["a", "b"],
        )

    one_cube = iris.cube.CubeList([cube])
    with pytest.raises(ValueError, match="cubes should contain exactly 2 cubes."):
        plot.qq_plot(
            one_cube,
            coordinates=["time", "grid_latitude", "grid_longitude"],
            percentiles=[0, 50, 100],
            model_names=["a", "b"],
        )

    three_cubes = iris.cube.CubeList([cube, cube, cube])
    with pytest.raises(ValueError, match="cubes should contain exactly 2 cubes."):
        plot.qq_plot(
            three_cubes,
            coordinates=["time", "grid_latitude", "grid_longitude"],
            percentiles=[0, 50, 100],
            model_names=["a", "b"],
        )


def test_qq_plot_different_data_shape_regrid(cube, tmp_working_dir):
    """Test when data shape differs, but gets regridded.

    For any cube shapes differ.
    """
    rearranged_cube = cube.copy()
    rearranged_cube = rearranged_cube[:, :, 1:]
    del cube.attributes["cset_comparison_base"]
    cubes = iris.cube.CubeList([rearranged_cube, cube])
    plot.qq_plot(
        cubes,
        coordinates=["time", "grid_latitude", "grid_longitude"],
        percentiles=[0, 50, 100],
        model_names=["a", "b"],
    )
    assert Path("qq_plot.png").is_file()


def test_qq_plot_grid_staggering_regrid(cube, tmp_working_dir):
    """Test when data considered on staggered grid, so gets regridded."""
    rearranged_cube = cube.copy()
    rearranged_cube.rename("eastward_wind_at_10m")
    del cube.attributes["cset_comparison_base"]
    cubes = iris.cube.CubeList([rearranged_cube, cube])
    plot.qq_plot(
        cubes,
        coordinates=["time", "grid_latitude", "grid_longitude"],
        percentiles=[0, 50, 100],
        model_names=["a", "b"],
    )
    assert Path("qq_plot.png").is_file()


def test_hinton_returns_figure_and_axes():
    """Test that hinton plot returns valid fig and ax objects."""
    change = np.array([[0.5, -0.5]])
    signif = np.array([[1, 0]])

    fig, ax = plot.hinton_plot(
        change,
        signif,
        xaxis_labels=["A", "B"],
        yaxis_labels=["Metric"],
    )
    assert fig is not None
    assert ax is not None
