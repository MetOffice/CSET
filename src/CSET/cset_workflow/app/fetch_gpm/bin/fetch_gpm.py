#! /usr/bin/env python3

"""Retrieve Global Precipitation Measurement (GPM) observations. Specific to the Met Office."""

import ast
import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal

import cf_units
import iris
import isodate
from iris.coords import AuxCoord
from iris.cube import Cube, CubeList

from CSET.cset_workflow.app.fetch_fcst.bin.fetch_data import (
    SubsettingFilesystemFileRetriever,
    _template_file_path,
)

logger = logging.getLogger(__name__)

iris.FUTURE.save_split_attrs = True
iris.FUTURE.date_microseconds = True

"""The local archive can be found at /data/users/gpm_imerg

There are two production versions of the data in the archive,
V06 and V07. The link current_version points to the V07 data.

As of November 2026 the archive holds GPM V07 data
from 1998-01-01 to 2025-09-30 inclusive.
"""

GPM_MET_OFFICE = (
    Path(__file__).parent.parent / "file" / "restricted_gpm_met_office.json"
)
with open(GPM_MET_OFFICE, "rt") as file:
    GPM_ARCHIVE_PATH = json.load(file)["GPM_ARCHIVE_PATH"]
GPM_DATA_PERIOD = timedelta(days=1)
GPM_PRESET_DOMAINS: dict[str, list[float]] = {
    "ukv": [48.0, 62.0, -14.0, 5.0],
}


def _get_needed_environment_variables_gpm() -> dict:
    """Load the needed variables from the environment."""
    variables = {
        "date_type": "initiation",
        "data_time": datetime.fromisoformat(os.environ["CYLC_TASK_CYCLE_POINT"]),
        "forecast_length": isodate.parse_duration(os.environ["ANALYSIS_LENGTH"]),
        "model_identifier": "GPM",
        "subarea_extent": ast.literal_eval(os.environ.get("SUBAREA_EXTENT"))
        if len(os.environ.get("SUBAREA_EXTENT")) > 0
        else None,
        "rose_datac": os.environ["ROSE_DATAC"],
        "preset_gpm_domain": os.environ["PRESET_GPM_DOMAIN"],
        "preset_gpm_domain_name": os.environ["PRESET_GPM_DOMAIN_NAME"],
    }
    logger.debug("Environment variables loaded for GPM: %s", variables)
    return variables


def fetch_gpm():
    """Fetch the GPM observations."""
    v = _get_needed_environment_variables_gpm()
    cycle_data_dir = f"{v['rose_datac']}/data/GPM"
    os.makedirs(cycle_data_dir, exist_ok=True)
    start = v["data_time"].replace(tzinfo=None)
    time_bounds = (start, start + v["forecast_length"])
    paths = _template_file_path(
        GPM_ARCHIVE_PATH,
        "validity",
        v["data_time"],
        v["forecast_length"],
        timedelta(0),
        GPM_DATA_PERIOD,
    )
    logger.info("Retrieving paths:\n%s", "\n".join(paths))

    if v["preset_gpm_domain"]:
        subarea_type = "realworld"
        subarea_extent = _get_preset_gpm_domain(v["preset_gpm_domain_name"])
    else:
        subarea_type = v["subarea_type"]
        subarea_extent = v["subarea_extent"]
    with SubsettingFilesystemFileRetriever(
        subarea_type, subarea_extent, time_bounds
    ) as retriever:
        any_files_found = any(retriever.get_file(p, cycle_data_dir) for p in paths)
    if not any_files_found:
        raise FileNotFoundError("No GPM files found!")

    daily_gpm_files = sorted(Path(cycle_data_dir).glob("*.nc"))
    gpm_var = "precipitation_flux"

    cubes = iris.load(f"{cycle_data_dir}/gpm_imerg_production*.nc", gpm_var)
    merge_gpm_cube = _combine_gpm_cubes(cubes, start)
    merge_gpm_cube.var_name = f"gpm_{gpm_var}"
    merge_gpm_cube.long_name = f"gpm_{gpm_var}"
    iris.save(merge_gpm_cube, Path(cycle_data_dir) / f"gpm_{start:%Y%m%dT%H%MZ}.nc")
    for f in daily_gpm_files:
        f.unlink()


def _get_preset_gpm_domain(domain: Literal["ukv"]) -> list[float]:
    """Get a preset domain for cutting out GPM data.

    Extents are [lower lat, upper lat, lower lon, upper lon], the same
    format CSET uses for SUBAREA_EXTENT.

    Parameters
    ----------
    domain: str
        Name of the preset domain.

    Returns
    -------
    list[float]
        The domain extent.

    Raises
    ------
    ValueError
        If the domain is not a known preset.
    """
    try:
        return list(GPM_PRESET_DOMAINS[domain.lower()])
    except KeyError:
        raise ValueError(
            f"Unsupported domain: {domain!r}. "
            f"Expected one of {sorted(GPM_PRESET_DOMAINS)}."
        ) from None


def _add_forecast_coords(cube: Cube, forecast_reference_time: datetime) -> None:
    """Add forecast_period and forecast_reference_time coords, in place."""
    # Work in hours so forecast_period comes out in hours directly.
    time = cube.coord("time").copy()
    time.convert_units(
        cf_units.Unit("hours since 1970-01-01 00:00:00", calendar=time.units.calendar)
    )
    frt_hours = time.units.date2num(forecast_reference_time)

    cube.add_aux_coord(
        AuxCoord(
            frt_hours,
            standard_name="forecast_reference_time",
            units=time.units,
        )
    )
    cube.add_aux_coord(
        AuxCoord(
            time.points - frt_hours,
            bounds=time.bounds - frt_hours if time.has_bounds() else None,
            standard_name="forecast_period",
            units="hours",
        ),
        cube.coord_dims("time"),
    )


def _combine_gpm_cubes(cubes: CubeList, forecast_reference_time: datetime) -> Cube:
    """Combine GPM cubes into a single cube with frt and forecast period as scaler and aux coords.

    Parameters
    ----------
    cubes: CubeList
        One cube per file, all the same variable.
    forecast_reference_time: datetime
        Naive UTC datetime to use as the forecast reference time,
        normally the cycle point.

    Returns
    -------
    Cube
        Cube with a time dimension, plus forecast_period on that dimension
        and a scalar forecast_reference_time.
    """
    # Single-time files can end up with time as a scalar coord (extracting one
    # time point drops the dimension) and so we need to  promote it back to a dimension.
    cubes = CubeList(
        cube if cube.coord_dims("time") else iris.util.new_axis(cube, "time")
        for cube in cubes
    )

    iris.util.equalise_attributes(cubes)
    cube = cubes.concatenate_cube()

    _add_forecast_coords(cube, forecast_reference_time)
    return cube


# Run the function that fetches the GPM obs.
if __name__ == "__main__":
    fetch_gpm()
