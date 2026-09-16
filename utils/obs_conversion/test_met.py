"""Tests for MET point observation IO."""

import subprocess
from pathlib import Path
from shutil import which
from typing import Any

import numpy
import pandas as pd
import pytest
import xarray as xr

from .met import read_point_nc, to_ascii, to_index_table, to_point_nc


def test_to_index_table():
    """Test the to_index_table function."""
    input_list = ["A", "B", "A", "C", "B"]
    indices, unique_values = to_index_table(input_list)

    assert indices == [0, 1, 0, 2, 1]
    assert unique_values == ["A", "B", "C"]


def test_to_point_nc():
    """Test the to_point_nc function with a small sample DataFrame."""
    # Sample observation data
    obs_data: dict[str, Any] = {
        "station_id": ["S1", "S2"],
        "valid": pd.to_datetime(["2023-01-01T00:00", "2023-01-01T01:00"]),
        "prepbufr_type": ["A", "B"],
        "var_name": ["TMP", "DPT"],
        "units": ["K", "K"],
        "height": [10, 20],
        "level": [1000, 900],
        "value": [273.15, 275.15],
        "QC": ["good", "bad"],
    }
    obs_df = pd.DataFrame(obs_data)

    # Sample station metadata
    stations_data: dict[str, Any] = {
        "station_id": ["S1", "S2"],
        "latitude": [40.0, 41.0],
        "longitude": [-75.0, -76.0],
        "elevation_asl": [100, 200],
    }
    stations_df = pd.DataFrame(stations_data)

    # Call the function
    ds = to_point_nc(obs_df, stations_df)

    # Check that the output is an xarray Dataset
    assert isinstance(ds, xr.Dataset)

    # Check that the dimensions are correct
    assert ds.dims["nobs"] == 2
    assert ds.dims["nhdr"] == 2


def test_to_point_missing_site():
    """Test the to_point_nc function with a missing station in the station metadata."""
    # Sample observation data
    obs_data: dict[str, Any] = {
        "station_id": ["S1", "S3"],  # S3 is not in the stations_df
        "valid": pd.to_datetime(["2023-01-01T00:00", "2023-01-01T01:00"]),
        "prepbufr_type": ["A", "B"],
        "var_name": ["TMP", "DPT"],
        "units": ["K", "K"],
        "height": [10, 20],
        "level": [1000, 900],
        "value": [273.15, 275.15],
        "QC": ["good", "bad"],
    }
    obs_df = pd.DataFrame(obs_data)

    # Sample station metadata
    stations_data: dict[str, Any] = {
        "station_id": ["S1", "S2"],
        "latitude": [40.0, 41.0],
        "longitude": [-75.0, -76.0],
        "elevation_asl": [100, 200],
    }
    stations_df = pd.DataFrame(stations_data)

    # Missing stations should be filled with missing data
    ds = to_point_nc(obs_df, stations_df)
    assert numpy.isnan(ds["hdr_lat"][1])  # S3 is missing, so latitude should be NaN


def test_to_point_nc_save(tmp_path: Path):
    """Test the to_point_nc function and saving the output to a NetCDF file results in a file readable by MET."""
    # Sample observation data
    obs_data: dict[str, Any] = {
        "station_id": ["S1", "S2"],
        "valid": pd.to_datetime(["2023-01-01T00:00", "2023-01-01T01:00"]),
        "prepbufr_type": ["A", "B"],
        "var_name": ["TMP", "DPT"],
        "units": ["K", "K"],
        "height": [10, 20],
        "level": [1000, 900],
        "value": [273.15, 275.15],
        "QC": ["good", "bad"],
    }
    obs_df = pd.DataFrame(obs_data)

    # Sample station metadata
    stations_data: dict[str, Any] = {
        "station_id": ["S1", "S2"],
        "latitude": [40.0, 41.0],
        "longitude": [-75.0, -76.0],
        "elevation_asl": [100, 200],
    }
    stations_df = pd.DataFrame(stations_data)

    processed = to_point_nc(obs_df, stations_df)
    output_file = tmp_path / "processed.nc"
    processed.to_netcdf(output_file)  # type: ignore

    subprocess.run(
        ["ncdump", "-h", str(output_file)], check=True
    )  # Check if the file can be read by ncdump

    # Load the saved file and check its contents
    point2grid = which("point2grid")
    if point2grid is None:
        pytest.skip("MET is not available")
    subprocess.run(
        [
            point2grid,
            str(output_file),
            "G001",
            str(tmp_path / "gridded.nc"),
            "-field",
            'name="TMP"; level="Z0";',
            "-v",
            "100",
        ],
        check=True,
    )


def test_round_trip(tmp_path: Path):
    """Test the point nc file we generate matches ascii2nc."""
    # Sample observation data
    obs_data: dict[str, Any] = {
        "station_id": ["S1", "S2"],
        "valid": pd.to_datetime(["2023-01-01T00:00", "2023-01-01T01:00"]),
        "prepbufr_type": ["A", "B"],
        "var_name": ["TMP", "DPT"],
        "units": ["K", "K"],
        "height": [10, 20],
        "level": [1000, 900],
        "value": [273.15, 275.15],
        "QC": ["good", "bad"],
    }
    obs_df = pd.DataFrame(obs_data)

    # Sample station metadata
    stations_data: dict[str, Any] = {
        "station_id": ["S1", "S2"],
        "latitude": [40.0, 41.0],
        "longitude": [-75.0, -76.0],
        "elevation_asl": [100, 200],
    }
    stations_df = pd.DataFrame(stations_data)

    ascii_file = tmp_path / "ascii.txt"
    ascii_data = to_ascii(obs_df, stations_df)
    ascii_data.to_csv(ascii_file, index=False, sep="\t", header=False)

    with open(ascii_file) as f:
        print(f.read())

    nc_file = tmp_path / "processed.nc"
    processed = to_point_nc(obs_df, stations_df)
    processed.to_netcdf(nc_file)  # type: ignore

    ascii2nc_file = tmp_path / "ascii_converted.nc"

    # Convert the ascii data using ascii2nc
    ascii2nc = which("ascii2nc")
    if ascii2nc is None:
        pytest.skip("MET is not available")
    subprocess.run(
        [ascii2nc, str(ascii_file), str(ascii2nc_file), "-format", "met_point"],
        check=True,
    )

    expect = read_point_nc(ascii2nc_file)
    output = read_point_nc(nc_file)

    # The ascii2nc version doesn't have units, so drop that column
    pd.testing.assert_frame_equal(
        expect.drop(columns=["units"]), output.drop(columns=["units"])
    )
