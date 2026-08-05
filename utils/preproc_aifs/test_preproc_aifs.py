"""Tests for preproc_aifs.py."""

import numpy as np
import pytest
from iris.coords import AuxCoord, DimCoord
from iris.cube import Cube, CubeList
from preproc_aifs import (
    fix_ensemble_cubes,
    fix_name_and_units,
    fix_time_and_meta,
)


@pytest.fixture
def simple_time_coord():
    """Return a DimCoord object for time."""
    return DimCoord(
        [0, 6, 12],
        standard_name="time",
        units="hours since 2024-01-01 00:00:00",
    )


@pytest.fixture
def simple_cube(simple_time_coord):
    """Return a simple cube to test with."""
    cube = Cube(
        np.ones((3, 2)),
        long_name="2 metre temperature",
        units="K",
    )
    cube.add_dim_coord(simple_time_coord, 0)
    cube.add_dim_coord(
        DimCoord([0, 1], long_name="x", units="1"),
        1,
    )
    return cube


def test_fix_name_and_units_renames_cube():
    """Test that cube has 2 metre temperature name changes."""
    cube = Cube(
        np.ones((2,)),
        long_name="2 metre temperature",
        units="K",
    )

    result = fix_name_and_units(cube)

    assert result.long_name == "temperature_at_screen_level"
    assert result.name() == "temperature_at_screen_level"
    assert str(result.units) == "K"


def test_fix_name_and_units_geopotential_conversion():
    """Test that geopotential height fixed and units corrected."""
    cube = Cube(
        np.array([98.0665]),
        long_name="Geopotential",
        units="m**2 s**-2",
    )

    result = fix_name_and_units(cube)

    assert result.long_name == "geopotential_height_at_pressure_levels"
    assert str(result.units) == "m"
    np.allclose(result.data, [10.0], rtol=1e-5, atol=1e-2)


def test_fix_name_and_units_unmapped_cube_unchanged():
    """Test if match unknown, then cube is left unchanged."""
    cube = Cube(
        np.ones((2,)),
        long_name="foo_bar",
        units="K",
    )

    result = fix_name_and_units(cube)

    assert result.long_name == "foo_bar"
    assert str(result.units) == "K"


def test_fix_ensemble_cubes_adds_realization_to_control_member():
    """Test that realization coord added to cube without realization."""
    cube = Cube(
        np.ones((3,)),
        long_name="test",
    )

    cube.add_dim_coord(
        DimCoord(
            [0, 6, 12],
            standard_name="time",
            units="hours since 2024-01-01",
        ),
        0,
    )

    result = fix_ensemble_cubes(CubeList([cube]))

    assert len(result) == 1

    processed = result[0]

    realization = processed.coord("realization")

    assert list(realization.points) == [0]


def test_fix_ensemble_cubes_replaces_ensemble_member():
    """Test that ensemble_member renamed to realization."""
    cube = Cube(
        np.ones((3, 50)),
        long_name="test",
    )

    cube.add_dim_coord(
        DimCoord(
            [0, 6, 12],
            standard_name="time",
            units="hours since 2024-01-01",
        ),
        0,
    )

    cube.add_aux_coord(
        AuxCoord(
            np.arange(1, 51),
            long_name="ensemble_member",
            units="1",
        ),
        data_dims=(1,),
    )

    result = fix_ensemble_cubes(CubeList([cube]))
    processed = result[0]
    realization = processed.coord("realization")

    assert realization.points[0] == 1
    assert realization.points[-1] == 50
    assert not processed.coords("ensemble_member")


def test_fix_ensemble_cubes_converts_pressure_auxcoord_to_dimcoord():
    """Test that pressure coordinate converted to dimcoord."""
    data = np.random.rand(3, 2)

    cube = Cube(data)

    cube.add_dim_coord(
        DimCoord(
            [0, 6, 12],
            standard_name="time",
            units="hours since 2024-01-01",
        ),
        0,
    )

    pressure_aux = AuxCoord(
        [850, 500],
        long_name="pressure_level",
        units="hPa",
    )

    cube.add_aux_coord(pressure_aux, data_dims=(1,))
    result = fix_ensemble_cubes(CubeList([cube]))
    processed = result[0]
    pressure = processed.coord("pressure_level")

    assert isinstance(pressure, DimCoord)
    assert pressure.points.tolist() == [500, 850]


def test_fix_time_and_meta_creates_forecast_period(simple_cube):
    """Test that forecast_period created."""
    result = fix_time_and_meta(CubeList([simple_cube]))

    cube = result[0]

    fp = cube.coord("forecast_period")

    assert fp.points.tolist() == [0, 6, 12]
    assert str(fp.units) == "hours"


def test_fix_time_and_meta_adds_forecast_reference_time(simple_cube):
    """Test that forecast_reference_time created."""
    result = fix_time_and_meta(CubeList([simple_cube]))

    cube = result[0]
    frt = cube.coord("forecast_reference_time")

    assert frt.points == 0


def test_fix_time_and_meta_adds_aux_time(simple_cube):
    """Check that time is a coordinate."""
    result = fix_time_and_meta(CubeList([simple_cube]))

    cube = result[0]
    time_coord = cube.coord("time")

    assert list(time_coord.points) == [0, 6, 12]


def test_fix_time_and_meta_converts_minutes_to_hours():
    """Check minutes is translated properly in forecast_period."""
    cube = Cube(
        np.ones((3,)),
        long_name="2 metre temperature",
    )

    cube.add_dim_coord(
        DimCoord(
            [0, 60, 120],
            standard_name="time",
            units="minutes since 2024-01-01",
        ),
        0,
    )

    result = fix_time_and_meta(CubeList([cube]))

    fp = result[0].coord("forecast_period")

    np.allclose(fp.points, [0, 1, 2], rtol=1e-5, atol=1e-2)
    assert str(fp.units) == "hours"


def test_fix_time_and_meta_converts_seconds_to_hours():
    """Check that seconds is translated properly in forecast_period."""
    cube = Cube(
        np.ones((3,)),
        long_name="2 metre temperature",
    )

    cube.add_dim_coord(
        DimCoord(
            [0, 3600, 7200],
            standard_name="time",
            units="seconds since 2024-01-01",
        ),
        0,
    )

    result = fix_time_and_meta(CubeList([cube]))

    fp = result[0].coord("forecast_period")

    np.testing.assert_allclose(fp.points, [0, 1, 2])


def test_fix_time_and_meta_raises_for_unknown_units():
    """Check that ValueError is rased if time units not supported."""
    cube = Cube(
        np.ones((3,)),
        long_name="2 metre temperature",
    )

    cube.add_dim_coord(
        DimCoord(
            [0, 1, 2],
            standard_name="time",
            units="days",
        ),
        0,
    )

    with pytest.raises(ValueError, match="Unhandled time units"):
        fix_time_and_meta(CubeList([cube]))
