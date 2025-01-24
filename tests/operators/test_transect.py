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

"""Tests transect operator."""

from pathlib import Path

import iris
import iris.coord_systems
import iris.cube
import numpy as np
import pytest

from CSET.operators import plot, read, transect


# Session scope fixtures, so the test data only has to be loaded once.
@pytest.fixture(scope="session")
def transect_source_cube_out() -> iris.cube.Cube:
    """Load cube containing UM pressure level data transect."""
    return read.read_cube("tests/test_data/transect_out_umpl.nc")


@pytest.fixture(scope="session")
def load_cube_ml() -> iris.cube.Cube:
    """Load cube containing UM model level data."""
    return read.read_cube("tests/test_data/transect_test_umml.nc")


@pytest.fixture(scope="session")
def load_cube_ml_out() -> iris.cube.Cube:
    """Load cube containing UM model level data transect."""
    return read.read_cube("tests/test_data/transect_out_umml.nc")


@pytest.fixture(scope="session")
def test_transect_pl(transect_source_cube, transect_source_cube_out):
    """Test case of computing transect on UM pressure level data."""
    assert np.allclose(
        transect.calc_transect(
            transect_source_cube, startcoords=(-10.94, 19.06), endcoords=(-10.82, 19.18)
        ).data,
        transect_source_cube_out.data,
        rtol=1e-06,
        atol=1e-02,
    )


@pytest.fixture(scope="session")
def test_transect_ml(load_cube_ml, load_cube_ml_out):
    """Test case of computing transect on UM model level data."""
    assert np.allclose(
        transect.calc_transect(
            load_cube_ml, startcoords=(-0.94, 29.06), endcoords=(-0.78, 29.3)
        ).data,
        load_cube_ml_out.data,
        rtol=1e-06,
        atol=1e-02,
    )


def test_transect_45deg(transect_source_cube, transect_source_cube_out):
    """Test case of 45 degree angle where map coordinate should be longitude."""
    with pytest.raises(iris.exceptions.CoordinateNotFoundError):
        transect.calc_transect(
            transect_source_cube, startcoords=(-10.94, 19.06), endcoords=(-10.86, 19.14)
        ).coord("latitude")


def test_transect_coord_outofboundsLLat(transect_source_cube):
    """Test case of computing transect on coords out of range (low start lat)."""
    with pytest.raises(IndexError):
        transect.calc_transect(
            transect_source_cube, startcoords=(-11.94, 19.06), endcoords=(-10.82, 19.18)
        )


def test_transect_coord_outofboundsLLon(transect_source_cube):
    """Test case of computing transect on coords out of range (low start lon)."""
    with pytest.raises(IndexError):
        transect.calc_transect(
            transect_source_cube, startcoords=(-10.94, 10.06), endcoords=(-10.82, 19.18)
        )


def test_transect_coord_outofboundsHLat(transect_source_cube):
    """Test case of computing transect on coords out of range (high end lat)."""
    with pytest.raises(IndexError):
        transect.calc_transect(
            transect_source_cube, startcoords=(-10.94, 19.06), endcoords=(-5.82, 19.18)
        )


def test_transect_coord_outofboundsHLon(transect_source_cube):
    """Test case of computing transect on coords out of range (high end lon)."""
    with pytest.raises(IndexError):
        transect.calc_transect(
            transect_source_cube, startcoords=(-10.94, 19.06), endcoords=(-10.82, 25.18)
        )


def test_transect_90degangle(transect_source_cube):
    """Test case of computing transect on 90 degree angle (no delta lon)."""
    with pytest.raises(iris.exceptions.CoordinateNotFoundError):
        transect.calc_transect(
            transect_source_cube, startcoords=(-10.94, 19.18), endcoords=(-10.82, 19.18)
        ).coord("longitude")


def test_transect_180degangle(transect_source_cube):
    """Test case of computing transect on 180 degree angle (no delta lat)."""
    with pytest.raises(iris.exceptions.CoordinateNotFoundError):
        transect.calc_transect(
            transect_source_cube, startcoords=(-10.94, 19.06), endcoords=(-10.94, 19.18)
        ).coord("latitude")


def test_transect_plotasfuncoflatitude(transect_source_cube):
    """Test case of computing transect where it should return as function of latitude."""
    with pytest.raises(iris.exceptions.CoordinateNotFoundError):
        transect.calc_transect(
            transect_source_cube, startcoords=(-10.94, 19.06), endcoords=(-10.82, 19.14)
        ).coord("longitude")


def test_transect_plotasfuncoflongitude(transect_source_cube):
    """Test case of computing transect where it should return as function of longitude."""
    with pytest.raises(iris.exceptions.CoordinateNotFoundError):
        transect.calc_transect(
            transect_source_cube, startcoords=(-10.94, 19.06), endcoords=(-10.86, 19.18)
        ).coord("latitude")


def test_transect_model_level_spatial_contour_plot(load_cube_ml_out, tmp_working_dir):
    """Plot a contour plot of the transect model level data."""
    plot.spatial_contour_plot(load_cube_ml_out, filename="plot")
    assert Path("plot_449743.0.png").is_file()
    assert Path("plot_449744.0.png").is_file()


def test_transect_model_level_spatial_pcolormesh_plot(
    load_cube_ml_out, tmp_working_dir
):
    """Plot a pcolormesh plot of the transect model level data."""
    plot.spatial_pcolormesh_plot(load_cube_ml_out, filename="plot")
    assert Path("plot_449743.0.png").is_file()
    assert Path("plot_449744.0.png").is_file()


def test_transect_pressure_spatial_contour_plot(
    transect_source_cube_out, tmp_working_dir
):
    """Plot a contour plot of the transect pressure data."""
    plot.spatial_contour_plot(transect_source_cube_out, filename="plot")
    assert Path("plot_449469.0.png").is_file()
    assert Path("plot_449472.0.png").is_file()


def test_transect_pressure_spatial_pcolormesh_plot(
    transect_source_cube_out, tmp_working_dir
):
    """Plot a pcolormesh plot of the transect pressure data."""
    plot.spatial_pcolormesh_plot(transect_source_cube_out, filename="plot")
    assert Path("plot_449469.0.png").is_file()
    assert Path("plot_449472.0.png").is_file()
