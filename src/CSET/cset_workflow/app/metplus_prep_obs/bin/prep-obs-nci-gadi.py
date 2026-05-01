#!/usr/bin/env python

"""Process Bureau observations data stored at NCI for use by METplus."""

import argparse
import functools
import json
import os
import sys
from datetime import datetime

import metomi.isodatetime.parsers
import pandas
import pyodc as odc

if sys.version_info >= (3, 14):
    import tarfile

    from compression import zstd
else:
    from backports import zstd
    from backports.zstd import tarfile

# Valid bureau forecast systems
BOM_SYSTEMS = ["access_g3", "access_g4"]
for dm in ["ad", "bn", "dn", "nq", "ph", "sy", "vt"]:
    BOM_SYSTEMS.extend(["access_c3_" + dm, "access_c4_" + dm])

# Columns to output
ASCII_COLUMNS = [
    "Message_Type",
    "Station_ID",
    "Valid_Time",
    "Lat",
    "Lon",
    "Elevation",
    "GRIB_Code",
    "Level",
    "Height",
    "QC_String",
    "Observation_Value",
]


def _get_c(obsdate: datetime, system: str, type: str) -> pandas.DataFrame:
    year = f"{obsdate.year}"
    month = f"{obsdate.month:02d}"
    timestamp = obsdate.strftime("%Y%m%dT%H%MZ")

    access, version, domain = system.split("_")
    if version == "c3":
        extension = "tar.zst"
    else:
        extension = "tgz"
    tarpath = f"/g/data/ig2/odb2/access_{version}/{year}/{month}/{timestamp}/{timestamp}_{domain}_odb2.{extension}"

    with tarfile.open(tarpath, "r") as t:
        if type in ["aircraft", "sonde", "surface"]:
            obsfile = "ukv_odb2/aircraftsondesurface.odb"
        else:
            obsfile = f"ukv_odb2/{type}.odb"

        file = t.extractfile(obsfile)
        obs = odc.read_odb(file, single=True)

    return obs


def _get_g(obsdate: datetime, system: str, type: str) -> pandas.DataFrame:
    year = f"{obsdate.year}"
    month = f"{obsdate.month:02d}"
    timestamp = obsdate.strftime("%Y%m%dT%H%MZ")

    access, version = system.split("_")
    zstdpath = f"/g/data/ig2/odb2/access_{version}/{year}/{month}/{timestamp}/glm_odb2/{type}.odb.zst"

    with zstd.open(zstdpath, "rb") as file:
        obs = odc.read_odb(file, single=True)

    return obs


@functools.cache
def varno_info() -> pandas.DataFrame:
    """Variable information as a dataframe."""
    with open("odb2varno.json", "rt") as f:
        j = json.load(f)
    return pandas.DataFrame(
        j["data"], columns=["varno_" + f for f in j["fields"]]
    ).set_index("varno_code")


def get_obs(obsdate: datetime, system: str, type: str) -> pandas.DataFrame:
    """Retrieve archived observations."""
    assert obsdate.minute == 0
    assert obsdate.second == 0

    if system.startswith("access_c"):
        obs = _get_c(obsdate, system, type)
    elif system.startswith("access_g"):
        obs = _get_g(obsdate, system, type)

    # Basic QC
    obs = obs[(obs["report_status@hdr"] == 1) & (obs["datum_status@body"] == 1)]

    # Add variable names
    obs = obs.join(varno_info(), on="varno@body")

    return obs


def odb2ascii(obs: pandas.DataFrame) -> pandas.DataFrame:
    """Convert data from pyodc to METplus ASCII format."""
    ascii = pandas.DataFrame(columns=ASCII_COLUMNS)
    ascii["Station_ID"] = obs["statid@hdr"]
    ascii["Valid_Time"] = (
        obs["date@hdr"].astype(str) + "_" + obs["time@hdr"].astype(str).str.zfill(6)
    )
    ascii["Lat"] = obs["lat@hdr"]
    ascii["Lon"] = obs["lon@hdr"]
    ascii["Elevation"] = obs["stalt@hdr"]
    ascii["GRIB_Code"] = obs["varno_name"]
    ascii["Level"] = obs["vertco_reference_1@body"] // 100  # in hPa
    ascii["Height"] = obs["stalt@hdr"]
    ascii["QC_String"] = "NA"
    ascii["Observation_Value"] = obs["obsvalue@body"]

    return ascii


def prep_surface_obs(obsdate: datetime, system: str) -> pandas.DataFrame:
    """Filter out surface obs and process them."""
    obs = get_obs(obsdate, system, "surface")
    sfc_obs = obs[obs["vertco_reference_1@body"] == 1.0]

    ascii = odb2ascii(sfc_obs)
    ascii["Message_Type"] = "ADPSFC"
    return ascii


def timepoint_to_datetime(tp) -> datetime:
    """Convert isodatetime to python datetime."""
    tp = tp.to_calendar_date()
    return datetime(
        tp.year,
        tp.month_of_year,
        tp.day_of_month,
        int(tp.hour_of_day),
        int(tp.minute_of_hour),
    )


def prep_obs(obsdate: datetime, system: str) -> pandas.DataFrame:
    """
    Get observations into a ascii table as required by METplus.

    args:
        obsdate: Observation date to load
        system: APS system to load obs from
    """
    obs = prep_surface_obs(obsdate, system)
    return obs


def main():
    """Script CLI."""
    parser = argparse.ArgumentParser("Process BOM observation data at NCI for METplus")
    parser.add_argument(
        "--system",
        required=True,
        choices=BOM_SYSTEMS,
        help="Forecast system to pull observations from",
    )
    parser.add_argument(
        "--start",
        help="Start date ($CYLC_TASK_CYCLE_POINT)",
        default=os.environ.get(
            "CYLC_TASK_CYCLE_POINT", datetime.now().strftime("%Y%m%dT0000Z")
        ),
        type=metomi.isodatetime.parsers.TimePointParser().parse,
    )
    parser.add_argument(
        "--length",
        help="Duration of observations to load",
        default="PT1H",
        type=metomi.isodatetime.parsers.DurationParser().parse,
    )
    parser.add_argument("--output", help="Output file")

    args = parser.parse_args()

    start = args.start.to_utc()
    end = start + args.length

    if args.output is None:
        args.output = f"{args.system}_{start.strftime('%Y%m%dT%H%MZ')}.ascii"

    with open(args.output, "wt") as f:
        for date in pandas.date_range(
            timepoint_to_datetime(start), timepoint_to_datetime(end), freq="1h"
        ):
            obs = prep_obs(date, args.system)

            obs.to_csv(f, sep="\t", header=False, index=False, na_rep="NA")


if __name__ == "__main__":
    main()
