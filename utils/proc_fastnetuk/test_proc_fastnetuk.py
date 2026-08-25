"""Tests for the proc_fastnetuk.py script."""

import iris
import iris.coords as icoords
import iris.cube
import numpy as np
import pytest
from cf_units import Unit
from utils.proc_fastnetuk import proc_fastnetuk

# Setup standard mesh variables that will be reused in tests.
NY = 808
NX = 621
NMESH = NY * NX


@pytest.fixture
def grid_cube():
    """Create a minimal UKV shaped grid cube."""
    lat = icoords.DimCoord(
        np.arange(NY),
        long_name="grid_latitude",
        units="degrees",
    )

    lon = icoords.DimCoord(
        np.arange(NX),
        long_name="grid_longitude",
        units="degrees",
    )

    data = np.zeros((NY, NX))

    return iris.cube.Cube(
        data,
        dim_coords_and_dims=[
            (lat, 0),
            (lon, 1),
        ],
    )


@pytest.fixture
def time_coord():
    """Create a representative time coordinate."""
    return icoords.DimCoord(
        np.array([0, 21600]),  # 0h and +6h
        standard_name="time",
        units=Unit("seconds since 2024-01-01 00:00:00"),
    )


def make_cube(name, time_coord, value=1.0):
    """Build a FastNetUK cube."""
    # Create data array.
    data = np.full((2, NMESH), value)

    cube = iris.cube.Cube(
        data,
        long_name=name,
        dim_coords_and_dims=[(time_coord, 0)],
    )

    cube.rename(name)

    cube.attributes["fill_value"] = np.nan
    cube.attributes["source"] = "test"

    return cube


def test_unknown_variable_returns_none(grid_cube, time_coord):
    """Test that unknown variable returns None.

    If a variable is not matched in the meta lookup, return None.
    """
    cube = make_cube("foobar", time_coord)

    result = proc_fastnetuk.rebuild_metadata(cube, grid_cube)

    assert result is None


def test_invalid_name_returns_none(grid_cube, time_coord):
    """Test name that does not match pattern returns None."""
    cube = make_cube("foo-bar!", time_coord)

    result = proc_fastnetuk.rebuild_metadata(cube, grid_cube)

    assert result is None


def test_surface_variable_metadata(grid_cube, time_coord):
    """Test metadata is fixed for surface variable."""
    cube = make_cube("2t", time_coord)

    result = proc_fastnetuk.rebuild_metadata(cube, grid_cube)

    assert result is not None
    assert result.long_name == "temperature_at_screen_level"
    assert str(result.units) == "K"

    assert result.shape == (1, 2, NY, NX)

    assert result.coord("forecast_period").points.tolist() == [0.0, 6.0]


def test_pressure_variable_metadata(grid_cube, time_coord):
    """Test metadata fixed for pressure level variable."""
    cube = make_cube("t_850", time_coord)

    result = proc_fastnetuk.rebuild_metadata(cube, grid_cube)

    assert result.long_name == "temperature_at_pressure_levels"

    pressure = result.coord("pressure")

    assert pressure.points[0] == 850
    assert str(pressure.units) == "hPa"

    assert result.shape == (1, 2, 1, NY, NX)


def test_time_auxcoord_created(grid_cube, time_coord):
    """Test that corresponding time auxcoord created."""
    cube = make_cube("2t", time_coord)

    result = proc_fastnetuk.rebuild_metadata(cube, grid_cube)

    time_aux = result.coord("time")

    assert time_aux.shape == (1, 2)


def test_forecast_reference_time_created(grid_cube, time_coord):
    """Check that forecast reference time created."""
    cube = make_cube("2t", time_coord)

    result = proc_fastnetuk.rebuild_metadata(cube, grid_cube)

    frt = result.coord("forecast_reference_time")

    assert frt.shape == (1,)


def test_attributes_preserved(grid_cube, time_coord):
    """Check that additional attributes preserved."""
    cube = make_cube("2t", time_coord)

    result = proc_fastnetuk.rebuild_metadata(cube, grid_cube)

    assert result.attributes["source"] == "test"


def test_geopotential_conversion(grid_cube, time_coord):
    """Check that geopotential converted to height."""
    cube = make_cube("z_500", time_coord, value=9.81)

    result = proc_fastnetuk.rebuild_metadata(cube, grid_cube)

    assert np.allclose(result.data, 1.0)


def test_precipitation_conversion(grid_cube, time_coord):
    """Check that precipitation converted."""
    cube = make_cube("tp", time_coord, value=1.0)

    result = proc_fastnetuk.rebuild_metadata(cube, grid_cube)

    assert np.allclose(result.data, 1000.0)
