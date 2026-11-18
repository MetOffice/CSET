"""ODB2 format reading."""

import argparse
import io
import logging
import subprocess
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import NotRequired, TypedDict

import numpy
import pandas
from pandas import DataFrame

try:
    from compression import bz2, gzip, tarfile, zstd
except ImportError:
    import bz2
    import gzip

    from backports import zstd
    from backports.zstd import tarfile

log = logging.getLogger("met_read_odb2")


class VarNoMap(TypedDict):
    """Type class for ODB2 variable number mapping."""

    var_name: str
    var_desc: str
    units: str
    height: NotRequired[float]
    level: NotRequired[float]


# Mapping from ODB2 columns to obs dataframe columns
odb2_mapping = {
    "date@hdr": "valid_date",
    "time@hdr": "valid_time",
    "statid@hdr": "station_id",
    "lat@hdr": "latitude",
    "lon@hdr": "longitude",
    "stalt@hdr": "elevation_asl",
    "reportype@hdr": "report_type",
    "varno@body": "varno",
    "obsvalue@body": "value",
    "vertco_type@body": "vertco_type",
    "vertco_reference_1@body": "vertco_value",
}

filters = {
    "report_status@hdr": 1,
    "datum_status@body": 1,
}

# Mapping from https://codes.ecmwf.int/odb/reporttype/ to https://www.emc.ncep.noaa.gov/mmb/data_processing/prepbufr.doc/table_1.htm
report_type_mapping = {
    16001: {"prepbufr_type": "ADPSFC", "report_desc": "Auto land SYNOP"},
    16002: {"prepbufr_type": "ADPSFC", "report_desc": "Manual land SYNOP"},
    16004: {"prepbufr_type": "ADPSFC", "report_desc": "METAR"},
    16005: {"prepbufr_type": "SFCSHP", "report_desc": "DRIBU"},
    16008: {"prepbufr_type": "SFCSHP", "report_desc": "SHIP"},
    16015: {"prepbufr_type": "PROFLR", "report_desc": "American wind profiler"},
    16026: {"prepbufr_type": "AIRCFT", "report_desc": "AIREP"},
    16029: {"prepbufr_type": "AIRCFT", "report_desc": "AMDAR"},
    16045: {"prepbufr_type": "ADPSFC", "report_desc": "BUFR land temp"},
    16083: {"prepbufr_type": "SFCSHP", "report_desc": "BUFR moored buoys"},
    16084: {"prepbufr_type": "SFCSHP", "report_desc": "BUFR drifting buoys"},
}

# Mapping from https://codes.ecmwf.int/odb/varno/ to https://github.com/dtcenter/MET/blob/main_v12.2/data/table_files/grib2_all.txt
varno_mapping: dict[int, VarNoMap] = {
    1: {"var_name": "GP", "var_desc": "Geopotential", "units": "m/s"},
    2: {"var_name": "TMP", "var_desc": "Upper air temperature (K)", "units": "K"},
    3: {"var_name": "UGRD", "var_desc": "Upper air u component", "units": "m/s"},
    4: {"var_name": "VGRD", "var_desc": "Upper air v component", "units": "m/s"},
    7: {"var_name": "SPFH", "var_desc": "Specific humidity", "units": "kg/kg"},
    29: {"var_name": "RH", "var_desc": "Upper air rel. humidity", "units": "%"},
    30: {"var_name": "PTEND", "var_desc": "Pressure tendency", "units": "Pa/s"},
    39: {
        "var_name": "TMP",
        "var_desc": "2m temperature (K)",
        "units": "K",
        "height": 2,
    },
    40: {"var_name": "DPT", "var_desc": "2m dew point (K)", "units": "K", "height": 2},
    41: {
        "var_name": "UGRD",
        "var_desc": "10m u component (m/s)",
        "units": "m/s",
        "height": 10,
    },
    42: {
        "var_name": "VGRD",
        "var_desc": "10m v component (m/s)",
        "units": "m/s",
        "height": 10,
    },
    58: {"var_name": "RH", "var_desc": "2m rel. humidity", "units": "%", "height": 2},
    59: {"var_name": "DPT", "var_desc": "Upper air dew point (K)", "units": "K"},
    62: {"var_name": "VIS", "var_desc": "Visibility", "units": "m"},
    91: {
        "var_name": "TCDC",
        "var_desc": "Total amount of clouds",
        "units": "%",
        "height": 0,
    },
    107: {"var_name": "PRES", "var_desc": "Station pressure (Pa)", "units": "Pa"},
    108: {
        "var_name": "PRMSL",
        "var_desc": "Mean sea-level pressure (Pa)",
        "units": "Pa",
        "height": 0,
    },
    109: {
        "var_name": "PRES",
        "var_desc": "Standard level pressure (Pa)",
        "units": "Pa",
        "height": 0,
    },
    110: {
        "var_name": "PRES",
        "var_desc": "Surface pressure",
        "units": "Pa",
        "height": 0,
    },
    111: {
        "var_name": "WDIR",
        "var_desc": "Wind direction",
        "units": "degrees",
        "height": 10,
    },
    112: {
        "var_name": "WIND",
        "var_desc": "Wind force",
        "units": "m/s",
        "height": 10,
    },
    130: {
        "var_name": "PTEND",
        "var_desc": "Characteristic of pressure tendency",
        "units": "Pa/s",
    },
    218: {"var_name": "VIS", "var_desc": "Vertical visibility (m)", "units": "m"},
    226: {
        "var_name": "MIXR",
        "var_desc": "Humidity mixing ratio (kg/kg)",
        "units": "kg/kg",
    },
}


@contextmanager
def decompress_file(input_file: Path | str) -> Path:
    """
    Return a temporary decompressed copy of input_file.

    If input_file has the following formats it will be decompressed:

     * `*.tar@**/*`: Tar file, part after '!' is the internal path
     * `*.gz`, `*.bz2`, `*.zst`: Compressed files

    Otherwise input_file is returned unchanged.
    """
    input_file = str(input_file)

    with tempfile.NamedTemporaryFile(delete_on_close=False) as tmp:
        # Holds the decompressed file object
        data = None

        parts = str(input_file).split("@")
        if len(parts) == 2:
            # Tar file
            log.info("untar %s", parts[0])
            with tarfile.open(parts[0], "r") as tf:
                log.info("member %s", parts[1])
                data = tf.extractfile(parts[1]).read()

        if input_file.endswith(".gz"):
            log.info("gzip %s", input_file)
            with gzip.open(input_file) as f:
                data = f.read()
        elif input_file.endswith(".bz2"):
            log.info("bzip2 %s", input_file)
            with bz2.open(input_file) as f:
                data = f.read()
        elif input_file.endswith(".zst"):
            log.info("zst %s", input_file)
            with zstd.open(input_file) as f:
                data = f.read()

        if data is None:
            log.info("raw %s", input_file)
            yield input_file
        else:
            tmp.write(data)
            tmp.close()
            yield tmp.name


def odc_sql(input_file: Path, query: str) -> DataFrame:
    """Convert a single ODB2 input file into a pandas DataFrame."""
    with decompress_file(input_file) as f:
        r = subprocess.run(
            ["odc", "sql", "-i", str(f), query],
            check=True,
            capture_output=True,
            text=True,
        )
    df = pandas.read_csv(
        io.StringIO(r.stdout), sep=r"\s+", quotechar="'", dtype={"station_id": str}
    )
    df["station_id"] = df[
        "station_id"
    ].str.strip()  # station ids are fixed-width, remove trailing space
    return df


def odb2_to_met_dataframe(
    input_files: list[Path], valid_time: datetime | None = None
) -> DataFrame:
    """Convert the ODB2 data in input_files into an observation DataFrame."""
    query = "SELECT " + ", ".join([f"{k} AS {v}" for k, v in odb2_mapping.items()])
    query += " WHERE " + " AND ".join([f"{k} = {v!s}" for k, v in filters.items()])

    if valid_time is not None:
        input_files = [valid_time.strftime(str(f)) for f in input_files]

    dfs = [odc_sql(f, query) for f in input_files]
    combined_df = pandas.concat(dfs, ignore_index=True)
    log.info("Extracted odb2:\n%s", combined_df)

    # Set levels
    pressure_level_types = [1, 11, 13, 15]
    combined_df["level"] = combined_df["vertco_value"].where(
        combined_df["vertco_type"].isin(pressure_level_types)
    )
    combined_df["height"] = numpy.nan
    combined_df["QC"] = numpy.nan

    combined_df["valid"] = pandas.to_datetime(
        combined_df["valid_date"].astype(str)
        + combined_df["valid_time"].astype(str).str.zfill(6),
        format="%Y%m%d%H%M%S",
        utc=True,
    )

    # Filter on valid time
    if valid_time is not None:
        combined_df = combined_df[combined_df["valid"] == valid_time]

    # Merge in the mapping from ODB2 to MET values
    combined_df = combined_df.join(
        DataFrame.from_dict(report_type_mapping, orient="index"),
        on="report_type",
        lsuffix="orig_type",
    )
    combined_df = combined_df.join(
        DataFrame.from_dict(varno_mapping, orient="index"),
        on="varno",
        lsuffix="orig_varno",
    )

    # Convert to MET's dataframe format
    # https://metplus.readthedocs.io/projects/met/en/latest/Users_Guide/appendixF.html#python-script-requirements-for-point-observations
    met_df = pandas.DataFrame(
        columns=[
            "typ",
            "sid",
            "vld",
            "lat",
            "lon",
            "elv",
            "var",
            "lvl",
            "hgt",
            "qc",
            "obs",
        ]
    )
    met_df["typ"] = combined_df["prepbufr_type"].fillna("NA").astype(str)
    met_df["sid"] = combined_df["station_id"].fillna("NA").astype(str)
    met_df["vld"] = (
        combined_df["valid"].dt.strftime("%Y%m%d_%H%M%S").fillna("NA").astype(str)
    )
    met_df["lat"] = combined_df["latitude"].astype(float)
    met_df["lon"] = combined_df["longitude"].astype(float)
    met_df["elv"] = combined_df["elevation_asl"].astype(float)
    met_df["var"] = combined_df["var_name"].fillna("NA").astype(str)
    met_df["lvl"] = combined_df["level"].astype(float)
    met_df["hgt"] = combined_df["height"].astype(float)
    met_df["qc"] = combined_df["QC"].fillna("NA").astype(str)
    met_df["obs"] = combined_df["value"].astype(float)

    log.info("Observations:\n%s", met_df)

    return met_df


def main() -> DataFrame:
    """
    Handle arguments set in the METplus config file.

    Use like:

        OBS_POINT_STAT_INPUT_DIR =
        OBS_POINT_STAT_INPUT_TEMPLATE = PYTHON_NUMPY=met_read_odb2.py --valid {valid?fmt=%Y%m%dT%H%M} {ODB2_TEMPLATE}
    """
    parser = argparse.ArgumentParser(description="Read ODB2 data into MET")
    parser.add_argument(
        "PATH",
        type=str,
        nargs="+",
        help="Input data paths. Can contain strftime-style placeholders to replace with the valid time",
    )
    parser.add_argument("--valid", type=str, help="Time constraint")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    return odb2_to_met_dataframe(args.PATH, pandas.to_datetime(args.valid, utc=True))


# MET reads from this global variable
start = time.perf_counter()
point_data = main().values.tolist()
log.info("point_data length: %s", len(point_data))
end = time.perf_counter()
log.info("met_read_odb2 ran in %s s", end - start)
