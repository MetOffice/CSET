"""Unit tests for process_reanalysis.py."""

from datetime import datetime

import iris
import numpy as np
import process_reanalysis as proc_reanalysis
import pytest
from iris.coords import DimCoord
from iris.cube import Cube


def test_single_cycle():
    """Assert single datetime returned if one initialisation."""
    result = proc_reanalysis.identify_number_of_cycles_required(
        "20240101T0000Z",
        "20240101T0000Z",
        6,
    )

    assert result == [datetime(2024, 1, 1, 0, 0)]


def test_multiple_cycles():
    """Test handling of multiple cycles identified."""
    result = proc_reanalysis.identify_number_of_cycles_required(
        "20240101T0000Z",
        "20240101T1200Z",
        6,
    )

    assert result == [
        datetime(2024, 1, 1, 0),
        datetime(2024, 1, 1, 6),
        datetime(2024, 1, 1, 12),
    ]


def test_non_divisible_interval():
    """Check end point is not exceeded."""
    result = proc_reanalysis.identify_number_of_cycles_required(
        "20240101T0000Z",
        "20240101T1000Z",
        6,
    )

    assert result == [
        datetime(2024, 1, 1, 0),
        datetime(2024, 1, 1, 6),
    ]


def test_invalid_date_format():
    """Raise problem with input."""
    with pytest.raises(ValueError):
        proc_reanalysis.identify_number_of_cycles_required(
            "2024-01-01",
            "20240101T1200Z",
            6,
        )


def make_cube(
    name="air_temperature",
    units="hours since 2024-01-01 00:00:00",
):
    """Create a minimal synthetic reanalysis cube."""
    time = DimCoord(
        np.arange(5),
        standard_name="time",
        units=units,
    )

    lat = DimCoord([50.0], standard_name="latitude", units="degrees")
    lon = DimCoord([0.0], standard_name="longitude", units="degrees")

    data = np.arange(5).reshape(5, 1, 1)

    cube = Cube(
        data,
        standard_name=name,
        dim_coords_and_dims=[
            (time, 0),
            (lat, 1),
            (lon, 2),
        ],
    )

    return cube


def test_forecast_period_created(tmp_path):
    """Check forecast period constructed correctly."""
    cube = make_cube()

    proc_reanalysis.create_forecasts(
        iris.cube.CubeList([cube]),
        [datetime(2024, 1, 1, 0)],
        forecastlength=4,
        outpath=str(tmp_path),
    )

    outfile = tmp_path / "reanalysis_20240101T0000Z.nc"

    cubes = iris.load(str(outfile))

    result = cubes[0]

    fp = result.coord("forecast_period")

    assert fp.points.tolist() == [0, 1, 2, 3, 4]
    assert str(fp.units) == "hours"


def test_seconds_converted_to_hours(tmp_path):
    """Check conversion from seconds to hours in forecast period."""
    cube = make_cube(units="seconds since 2024-01-01 00:00:00")

    cube.coord("time").points = [0, 3600, 7200, 10800, 14400]

    proc_reanalysis._create_forecasts(
        iris.cube.CubeList([cube]),
        [datetime(2024, 1, 1)],
        forecastlength=2,
        outpath=str(tmp_path),
    )

    cubes = iris.load(str(tmp_path / "reanalysis_20240101T0000Z.nc"))

    fp = cubes[0].coord("forecast_period")

    assert fp.points.tolist() == [0, 1, 2]


def test_minutes_converted_to_hours(tmp_path):
    """Check conversion from minutes to hours in forecast period."""
    cube = make_cube(units="minutes since 2024-01-01 00:00:00")

    cube.coord("time").points = [0, 60, 120, 180, 240]

    proc_reanalysis.create_forecasts(
        iris.cube.CubeList([cube]),
        [datetime(2024, 1, 1)],
        forecastlength=2,
        outpath=str(tmp_path),
    )

    cubes = iris.load(str(tmp_path / "reanalysis_20240101T0000Z.nc"))

    fp = cubes[0].coord("forecast_period")

    assert fp.points.tolist() == [0, 1, 2]


def test_unknown_time_units_raise(tmp_path):
    """Check that error raised if time units unhandled."""
    cube = make_cube(units="days since 2024-01-01 00:00:00")

    with pytest.raises(ValueError, match="Unhandled time units"):
        proc_reanalysis.create_forecasts(
            iris.cube.CubeList([cube]),
            [datetime(2024, 1, 1)],
            forecastlength=1,
            outpath=str(tmp_path),
        )


def test_forecast_reference_time_created(tmp_path):
    """Check that forecast reference time has been set correctly."""
    init_time = datetime(2024, 1, 1, 0)

    cube = make_cube()

    proc_reanalysis.create_forecasts(
        iris.cube.CubeList([cube]),
        [init_time],
        forecastlength=4,
        outpath=str(tmp_path),
    )

    cubes = iris.load(str(tmp_path / "reanalysis_20240101T0000Z.nc"))

    frt = cubes[0].coord("forecast_reference_time")

    recovered = frt.units.num2date(frt.points[0])

    assert str(recovered) == "2024-01-01 00:00:00"


def test_forecast_attributes_removed(tmp_path):
    """Check that common analysis attributes have been removed."""
    cube = make_cube()

    cube.attributes["source"] = "ERA5"
    cube.attributes["um_version"] = "13.0"

    proc_reanalysis.create_forecasts(
        iris.cube.CubeList([cube]),
        [datetime(2024, 1, 1)],
        forecastlength=4,
        outpath=str(tmp_path),
    )

    cubes = iris.load(str(tmp_path / "reanalysis_20240101T0000Z.nc"))

    attrs = cubes[0].attributes

    assert "source" not in attrs
    assert "um_version" not in attrs


def test_cube_skipped_if_insufficient_data(tmp_path):
    """Check that nothing save if analysis doesn't overlap with target forecast."""
    cube = make_cube()

    with pytest.raises(ValueError, match="No suitable cubes found for saving!"):
        proc_reanalysis.create_forecasts(
            iris.cube.CubeList([cube]),
            [datetime(2024, 1, 1)],
            forecastlength=10,
            outpath=str(tmp_path),
        )


def test_multiple_cubes_processed(tmp_path):
    """Check working with multiple cubes."""
    cube1 = make_cube("air_temperature")
    cube2 = make_cube("air_pressure")

    proc_reanalysis.create_forecasts(
        iris.cube.CubeList([cube1, cube2]),
        [datetime(2024, 1, 1)],
        forecastlength=4,
        outpath=str(tmp_path),
    )

    cubes = iris.load(str(tmp_path / "reanalysis_20240101T0000Z.nc"))

    assert len(cubes) == 2
