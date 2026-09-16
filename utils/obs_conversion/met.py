"""Met point observation IO."""

import logging
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from typing import Any, NotRequired, TypedDict

import numpy
import xarray
from pandas import DataFrame

from .obs import obs_dataframe_columns, obs_station_columns

log = logging.getLogger(__name__)


class OutputVar(TypedDict):
    """Type for output variable dictionary with dimensions and values."""

    dims: tuple[str, ...]
    values: list[str] | list[float] | list[int]
    encoding: NotRequired[
        dict[str, Any]
    ]  # Optional encoding for xarray Dataset creation


def to_index_table[T: str | int | float | tuple[Any, ...]](
    data: Iterable[T],
) -> tuple[list[int], list[T]]:
    """Create a list of indices and a list of unique values from the input data."""
    log.debug("to_index_table")
    unique_values = sorted(set(data))
    value_to_index = {v: i for i, v in enumerate(unique_values)}
    index_table = [value_to_index[value] for value in data]
    return index_table, unique_values


def to_point_nc(obs: DataFrame, stations: DataFrame | None = None) -> xarray.Dataset:
    """
    Create a MET point NetCDF dataset from observation and station data.

    If stations is not provided those columns will be obtained from the obs DataFrame.

    Args:
        obs (DataFrame): Observation data with columns obs.obs_dataframe_columns
        stations (DataFrame): Station metadata with columns obs.obs_station_columns

    Returns
    -------
        xarray.Dataset: Dataset in MET point NetCDF format.
    """
    if stations is None:
        stations = obs[obs_station_columns].drop_duplicates().reset_index(drop=True)

    if set(obs_dataframe_columns) - set(obs.columns):
        raise ValueError(
            "Observation DataFrame is missing required columns: "
            f"{set(obs_dataframe_columns) - set(obs.columns)}"
        )
    if set(obs_station_columns) - set(stations.columns):
        raise ValueError(
            "Station DataFrame is missing required columns: "
            f"{set(obs_station_columns) - set(stations.columns)}"
        )

    # Encoding info for the different data types
    e_float: dict[str, Any] = {
        "dtype": "f4",
        "zlib": True,
        "shuffle": True,
        "complevel": 4,
    }
    e_int: dict[str, Any] = {
        "dtype": "i4",
        "zlib": True,
        "shuffle": True,
        "complevel": 4,
    }
    e_mxstr: dict[str, Any] = {"dtype": "S16", "char_dim_name": "mxstr"}
    e_mxstr2: dict[str, Any] = {"dtype": "S40", "char_dim_name": "mxstr2"}
    # e_mxstr3 = {"dtype": "S80", "char_dim_name": "mxstr3"}

    # The output dataset structure
    output: dict[str, OutputVar] = {
        "obs_qty": {
            "dims": ("nobs",),
            "values": [],
            "encoding": e_int,
        },  # Quality control string index
        "obs_hid": {"dims": ("nobs",), "values": [], "encoding": e_int},  # Header index
        "obs_vid": {
            "dims": ("nobs",),
            "values": [],
            "encoding": e_int,
        },  # Variable index
        "obs_lvl": {
            "dims": ("nobs",),
            "values": [],
            "encoding": e_float,
        },  # Pressure level in hPa
        "obs_hgt": {
            "dims": ("nobs",),
            "values": [],
            "encoding": e_float,
        },  # Height in meters above sea level
        "obs_val": {
            "dims": ("nobs",),
            "values": [],
            "encoding": e_float,
        },  # Observation value
        "hdr_typ": {
            "dims": ("nhdr",),
            "values": [],
            "encoding": e_int,
        },  # Message type index
        "hdr_sid": {
            "dims": ("nhdr",),
            "values": [],
            "encoding": e_int,
        },  # Station ID index
        "hdr_vld": {
            "dims": ("nhdr",),
            "values": [],
            "encoding": e_int,
        },  # Valid time index
        "hdr_lat": {
            "dims": ("nhdr",),
            "values": [],
            "encoding": e_float,
        },  # Latitude in degrees north
        "hdr_lon": {
            "dims": ("nhdr",),
            "values": [],
            "encoding": e_float,
        },  # Longitude in degrees east
        "hdr_elv": {
            "dims": ("nhdr",),
            "values": [],
            "encoding": e_float,
        },  # Elevation in meters above sea level
        # "hdr_prpt_typ": {"dims": ("npbhdr",), "values": []},  # PrepBUFR report type
        # "hdr_irpt_typ": {"dims": ("npbhdr",), "values": []},  # Input report type
        # "hdr_inst_typ": {"dims": ("npbhdr",), "values": []},  # Instrument type
        "hdr_typ_table": {
            "dims": ("nhdr_typ",),
            "values": [],
            "encoding": e_mxstr2,
        },  # Message type lookup table
        "hdr_sid_table": {
            "dims": ("nhdr_sid",),
            "values": [],
            "encoding": e_mxstr2,
        },  # Station ID lookup table
        "hdr_vld_table": {
            "dims": ("nhdr_vld",),
            "values": [],
            "encoding": e_mxstr,
        },  # Valid time lookup table
        "obs_qty_table": {
            "dims": ("nobs_qty",),
            "values": [],
            "encoding": e_mxstr,
        },  # Quality control lookup table
        "obs_var": {
            "dims": ("obs_var_num",),
            "values": [],
            "encoding": e_mxstr,
        },  # Variable names lookup table
        "obs_unit": {
            "dims": ("obs_var_num",),
            "values": [],
            "encoding": e_mxstr2,
        },  # Variable units lookup table
        # "obs_desc": {"dims": ("obs_var_num",), "values": [], "encoding": e_mxstr3},     # Variable descriptions lookup table
    }

    log.debug("Gathering obs")
    output["obs_val"]["values"] = obs["value"].values.astype(float).tolist()
    output["obs_lvl"]["values"] = obs["level"].values.astype(float).tolist()
    output["obs_hgt"]["values"] = obs["height"].values.astype(float).tolist()
    output["obs_qty"]["values"], output["obs_qty_table"]["values"] = to_index_table(
        obs["QC"].values.astype(str).tolist()
    )

    # Each variable has unique (var, units)
    log.debug("Gathering obs_var")
    obs_var: list[tuple[str, str]] = list(
        zip(
            obs["var_name"].values.astype(str).tolist(),
            obs["units"].values.astype(str).tolist(),
            strict=True,
        )
    )  # type: ignore
    output["obs_vid"]["values"], var_table = to_index_table(obs_var)
    output["obs_var"]["values"], output["obs_unit"]["values"] = [
        list(t) for t in zip(*var_table, strict=True)
    ]  # type: ignore

    log.debug("Gathering obs_header")
    # Each header has unique (station_id, valid_time, type)
    obs_header: list[tuple[str, datetime, str]] = list(
        zip(
            obs["station_id"].values.astype(str).tolist(),
            obs["valid"].dt.strftime("%Y%m%d_%H%M%S").values.tolist(),
            obs["prepbufr_type"].values.astype(str).tolist(),
            strict=True,
        )
    )  # type: ignore
    output["obs_hid"]["values"], header_table = to_index_table(obs_header)
    station_ids, valid_times, types = zip(*header_table, strict=True)
    output["hdr_sid"]["values"], output["hdr_sid_table"]["values"] = to_index_table(
        station_ids
    )
    output["hdr_vld"]["values"], output["hdr_vld_table"]["values"] = to_index_table(
        valid_times
    )
    output["hdr_typ"]["values"], output["hdr_typ_table"]["values"] = to_index_table(
        types
    )

    # Extra station information
    log.debug("Gathering station metadata")
    stations["station_id"] = stations["station_id"].astype(str)
    matching_stations = stations.set_index("station_id").reindex(list(station_ids))
    output["hdr_elv"]["values"] = (
        matching_stations["elevation_asl"].values.astype(float).tolist()
    )
    output["hdr_lat"]["values"] = (
        matching_stations["latitude"].values.astype(float).tolist()
    )
    output["hdr_lon"]["values"] = (
        matching_stations["longitude"].values.astype(float).tolist()
    )

    # Build the output dataset
    log.debug("Creating xarray Dataset")
    ds = xarray.Dataset(
        {
            k: (v["dims"], v["values"], v.get("attrs", {}), v.get("encoding", {}))
            for k, v in output.items()
        }
    )

    # Add metadata
    ds.attrs["MET_Obs_version"] = "1.02"
    ds.attrs["use_var_id"] = "true"
    ds.attrs["MET_version"] = "V12.2.1"
    ds.attrs["MET_tool"] = "ascii2nc"

    return ds


def to_ascii(obs: DataFrame, stations: DataFrame | None = None) -> DataFrame:
    """
    Convert observation and station data to an ASCII-compatible DataFrame.

    Args:
        obs (DataFrame): Observation data.
        stations (DataFrame): Station metadata.

    Returns
    -------
        DataFrame: ASCII-compatible observation data.
    """
    if stations is None:
        stations = obs[obs_station_columns].drop_duplicates().reset_index(drop=True)

    if set(obs_dataframe_columns) - set(obs.columns):
        raise ValueError(
            "Observation DataFrame is missing required columns: "
            f"{set(obs_dataframe_columns) - set(obs.columns)}"
        )
    if set(obs_station_columns) - set(stations.columns):
        raise ValueError(
            "Station DataFrame is missing required columns: "
            f"{set(obs_station_columns) - set(stations.columns)}"
        )

    # Merge observation and station data
    ascii_data = obs.merge(
        stations,
        how="left",
        left_on="station_id",
        right_on="station_id",
        suffixes=("", "_station"),
    )

    ascii_columns = [
        "prepbufr_type",
        "station_id",
        "valid",
        "latitude",
        "longitude",
        "elevation_asl",
        "var_name",
        "level",
        "height",
        "QC",
        "value",
    ]

    ascii_data = ascii_data[ascii_columns]
    ascii_data["valid"] = ascii_data["valid"].dt.strftime("%Y%m%d_%H%M")
    return ascii_data


def read_point_nc(file_path: Path) -> DataFrame:
    """
    Read a MET point NetCDF file into a pandas DataFrame.

    Args:
        file_path (Path): Path to the NetCDF file.

    Returns
    -------
        pandas.DataFrame: DataFrame containing the observation data.
    """
    ds = xarray.open_dataset(file_path)  # type: ignore

    tables: dict[str, DataFrame] = {}
    for dim in ds.dims:
        assert isinstance(dim, str)
        vars = {k: v for k, v in ds.variables.items() if v.dims == (dim,)}
        tables[dim] = xarray.Dataset(vars).to_dataframe()

    obs = tables["nobs"]

    obs = obs.join(tables["nhdr"], on="obs_hid")
    obs = obs.join(tables["nhdr_typ"], on="hdr_typ")
    obs = obs.join(tables["nhdr_sid"], on="hdr_sid")
    obs = obs.join(tables["nhdr_vld"], on="hdr_vld")
    obs = obs.join(tables["nobs_qty"], on="obs_qty")
    obs = obs.join(tables["obs_var_num"], on="obs_vid")

    # Mapping back to our obs dataframe
    mapping = {
        "prepbufr_type": "hdr_typ_table",
        "station_id": "hdr_sid_table",
        "valid": "hdr_vld_table",
        "var_name": "obs_var",
        "units": "obs_unit",
        "level": "obs_lvl",
        "height": "obs_hgt",
        "QC": "obs_qty_table",
        "value": "obs_val",
        "latitude": "hdr_lat",
        "longitude": "hdr_lon",
        "elevation_asl": "hdr_elv",
    }

    obs = obs.rename(columns={v: k for k, v in mapping.items()})
    if "units" not in obs:
        obs["units"] = numpy.nan
    obs = obs.filter(items=list(mapping.keys()))

    return obs
