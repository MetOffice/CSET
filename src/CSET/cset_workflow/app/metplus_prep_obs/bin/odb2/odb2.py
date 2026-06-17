"""
Basic ODB2 reading class and functions.

Sites can extend the classes with their own templates.
"""

import functools
import json
import logging
from abc import ABC, abstractmethod
from glob import glob
from pathlib import Path
from typing import Iterable, TextIO
import sys
from contextlib import nullcontext

import metomi.isodatetime.parsers
import numpy
import pandas
import pyodc as odc
from metomi.isodatetime.data import TimePoint
from pandas import DataFrame

try:
    from compression import bz2, gzip, tarfile, zstd
except ImportError:
    import bz2
    import gzip

    from backports import zstd
    from backports.zstd import tarfile

log = logging.getLogger(__name__)

# Marker MET uses for unavailable values
na_value = "NA"

# Columns to output
ASCII_COLUMNS = [
    "Message_Type",
    "Station_ID",
    "Valid_Time",
    "Lat",
    "Lon",
    "Elevation",
    "Variable_Name",
    "Level",
    "Height",
    "QC_String",
    "Observation_Value",
]

# Local report types defined in OBS in case we want to map them to PrepBUFR types
# https://code.metoffice.gov.uk/trac/ops/browser/main/trunk/src/code/ODB/sql/report_types.hh
LOCAL_REPORT_TYPE = {
    98001: {"name": "modes", "description": "MODE-S"},
    98002: {"name": "radar_scan", "description": "Radar scan data"},
    98016: {"name": "osseaice", "description": "Ocean and Sea Ice SAF"},
    98031: {"name": "oceancolour", "description": "Ocean colour data"},
    98032: {"name": "ocean_wave", "description": "WAVENET ocean wave data"},
    98036: {"name": "insat_3d_imager", "description": "INSAT 3D imager"},
    98037: {"name": "insat_3d_sounder", "description": "INSAT 3D sounder"},
    98038: {"name": "oceanwinds", "description": "Satellite ccean surface wind speeds"},
    98039: {"name": "gmi_rad_low", "description": "GPM GMI radiances (all-sky, low)"},
    98040: {"name": "gmi_rad_high", "description": "GPM GMI radiances (all-sky, high)"},
    98041: {"name": "aladin_hloswind", "description": "HLOSWINDS from Aeolus(aladin)"},
    98042: {"name": "metop_c_satsst", "description": "SatSST METOP-C"},
    98043: {"name": "metop_c_gpsro", "description": "METOP-C GPSRO"},
    98044: {"name": "metop_c_amv", "description": "METOP-C AMV"},
    98045: {"name": "metop_c_ascat", "description": "METOP-C ASCAT"},
    98046: {"name": "metop_c_iasi_rad", "description": "METOP-C IASI radiances"},
    98047: {"name": "metop_c_mhs_rad", "description": '"AMSUB" (MHS really) MetOp C'},
    98048: {"name": "atovs_metop_c", "description": "UKMO ATOVS data (Metop C)"},
    98049: {"name": "goes_17_geos_rad", "description": "GOES-17 GEOS Radiances"},
    98050: {"name": "fy3d_cris", "description": "FY-3D CriS"},
    98051: {"name": "fy3_d_hiras_rad", "description": "HIRAS FY-3D"},
    98052: {"name": "moored_buoy", "description": "Moored buoys (non BUFR)"},
    98053: {"name": "emaddc", "description": "EMADDC"},
    98054: {"name": "giirs_fy4a", "description": "GIIRS FY-4A"},
    98055: {"name": "goes_18_amv", "description": "GOES 18 AMV"},
    98056: {"name": "goes_19_amv", "description": "GOES 19 AMV"},
    98057: {"name": "noaa_21_amv", "description": "NOAA 21 AVHRR IR AMV"},
    98058: {"name": "fy2h_amv", "description": "FY-2H IR AMV"},
    98059: {"name": "fy4a_amv", "description": "FY-2H IR AMV"},
    98060: {"name": "fy4b_amv", "description": "FY-2H IR AMV"},
    98061: {"name": "oceansat_3a_ascat", "description": "OCEANSAT-3A ASCAT"},
    98062: {"name": "hy2c_ascat", "description": "HY2C ASCAT"},
    98063: {"name": "fy3e_ascat", "description": "FY3E ASCAT"},
    98064: {"name": "insat_3dr_amv", "description": "INSAT-3DR AMV"},
    98065: {"name": "insat_3ds_amv", "description": "INSAT-3DS AMV"},
    98066: {"name": "geokompsat_2a_amv", "description": "GEOKOMPSAT-2A AMV"},
    98067: {"name": "meteosat_13_mtgirs", "description": "MTG-S1 IRS radiances"},
    98068: {"name": "giirs_fy4b", "description": "GIIRS FY-4B"},
}


def read_odb_table(table: str, index: str) -> DataFrame:
    """
    Read ECMWF ODB tables as a dataframe.

    Table info comes from https://codes.ecmwf.int/odb
    """
    path = Path(__file__).parent / f"{table}.json.gz"

    with gzip.open(path) as f:
        j = json.load(f)
    df = DataFrame(j["data"], columns=[f + f"@{table}" for f in j["fields"]])

    return df.set_index(f"{index}@{table}")


@functools.cache
def varno_table() -> DataFrame:
    """ODB variable information as a dataframe."""
    return read_odb_table("varno", index="code")


@functools.cache
def reporttype_table() -> DataFrame:
    """ODB report_type information as a dataframe."""
    return read_odb_table("reporttype", index="id")


def get_level(obs: DataFrame) -> pandas.Series:
    """
    Get the level parameter for each observation.

    Normally this is a pressure level in hPa (for fields with vertco_type in
    [1, 11, 15]. In the metplus config find matching values with

        OBS_VAR<N>_LEVELS = P750, P250

    to match against pressure levels at 750 and 250 hPa.

    For an accumulated value (names 'PRATE', 'TSTM', 'APCP', 'NCPCP', 'ACPCP')
    this is an accumulation interval in HHMMSS or HH format.

    ODB vertical coordinate types are enumerated at
    https://code.metoffice.gov.uk/trac/ops/browser/main/trunk/src/code/ODB/sql/vertco_type.hh
    """
    plevel = obs["vertco_reference_1@body"].where(
        obs["vertco_type@body"].isin([1, 11, 15]), numpy.nan
    )

    accumulated_fields = ["PRATE", "TSTM", "APCP", "NCPCP", "ACPCP"]
    if obs["name@varno"].isin(accumulated_fields).any():
        raise NotImplementedError("Accumulated fields not implemented")
    return plevel


def get_height(obs: DataFrame) -> pandas.Series:
    """
    Get the height parameter for each observation.

    This is matched against Z levels so for surface values we set it to 0 so
    they can be found with 'Z0'.

    In the metplus config find matching values with

        OBS_VAR<N>_LEVELS = Z0

    to match against surface fields

    ODB vertical coordinate types are enumerated at
    https://code.metoffice.gov.uk/trac/ops/browser/main/trunk/src/code/ODB/sql/vertco_type.hh
    """
    surface_fields = (obs["vertco_type@body"] == 5) & (
        obs["vertco_reference_1@body"] == 1
    )

    hlevel = (obs["vertco_reference_1@body"] * 0).where(surface_fields, numpy.nan)
    return hlevel


def get_type(obs: DataFrame) -> pandas.Series:
    """
    Get the message type for each observation.

    Where possible a PrepBUFR type is returned, otherwise it will be the ODB
    reportype@hdr value.

    Valid PrepBUFR message types are listed at
    https://www.emc.ncep.noaa.gov/mmb/data_processing/prepbufr.doc/table_1.htm

    ODB message types are listed at
    https://codes.ecmwf.int/odb/unionall/

    There are also some custom OPS report types enumerated at
    https://code.metoffice.gov.uk/trac/ops/browser/main/trunk/src/code/ODB/sql/report_types.hh
    """
    odb_prepbufr_map = {
        "AIREP": "AIRCFT",
        "Land Surface": "ADPSFC",
        "Sea Surface": "SFCSHP",
        "Upper Air Sounding": "ADPUPA",
    }

    types = obs["bufrtype@reporttype"].map(lambda t: odb_prepbufr_map.get(t, na_value))
    types = types.where(types != na_value, obs["reportype@hdr"])
    return types


def odb2ascii_dataframe(obs: DataFrame) -> DataFrame:
    """
    Convert a DataFrame from pyodc to MET ASCII format.

    args:
        obs: ODB2 data loaded with pyodb

    Output format is described at
    https://metplus.readthedocs.io/projects/met/en/latest/Users_Guide/reformat_point.html#id9
    """
    # QC filter for only active values
    obs = obs.loc[(obs["report_status@hdr"] | obs["datum_status@body"]) == 1]

    # Join in extra info
    obs = obs.join(varno_table(), on="varno@body")
    obs = obs.join(reporttype_table(), on="reportype@hdr")

    ascii = DataFrame(columns=ASCII_COLUMNS)

    ascii["Message_Type"] = get_type(obs)
    ascii["Station_ID"] = obs["statid@hdr"].where(
        obs["statid@hdr"].str.strip() != "", na_value
    )
    ascii["Valid_Time"] = pandas.to_datetime(
        obs["date@hdr"].astype(str) + "_" + obs["time@hdr"].astype(str).str.zfill(6),
        format="%Y%m%d_%H%M%S",
        utc=True,
    )
    ascii["Lat"] = obs["lat@hdr"]
    ascii["Lon"] = obs["lon@hdr"]
    ascii["Elevation"] = obs["stalt@hdr"]
    ascii["Variable_Name"] = obs["name@varno"]

    ascii["Level"] = get_level(obs)
    ascii["Height"] = get_height(obs)

    ascii["QC_String"] = na_value

    ascii["Observation_Value"] = obs["obsvalue@body"]

    return ascii


def write_ascii(dataframe: DataFrame, output: TextIO):
    """Write the ASCII dataframe to output."""
    dataframe.to_csv(
        output,
        sep="\t",
        date_format="%Y%m%d_%H%M",
        na_rep=na_value,
        index=False,
        header=False,
    )


def read_tarfile(tarpath: str, path: str, valid_time: TimePoint) -> Iterable[DataFrame]:
    """
    Read ODB2 data from a tarfile.

    Paths can use strftime templates which will be replaced by valid_time

    Args:
        tarpath: path of the tarfile
        path: path inside the tarfile
        valid_time: used for pattern replacement
    """
    tarpath = valid_time.strftime(tarpath)
    path = valid_time.strftime(path)
    log.info("Reading %s:%s", tarpath, path)

    with tarfile.open(tarpath, "r") as t:
        f = t.extractfile(path)
        yield from odc.read_odb(f)


def read_file(pattern: str, valid_time: TimePoint) -> Iterable[DataFrame]:
    """
    Read ODB2 data from a file, decompressing if required.

    Paths can use strftime templates which will be replaced by valid_time
    Paths can use shell globs
    Recognised extensions for decompression are .gz, .bz2, .zst

    Args:
        path: path to open
        valid_time: used for pattern replacement
    """
    path = valid_time.strftime(pattern)
    log.info("Reading %s", path)

    for p in glob(path):
        if p.endswith(".gz"):
            with gzip.open(p) as f:
                yield from odc.read_odb(f)
        elif p.endswith(".bz2"):
            with bz2.open(p) as f:
                yield from odc.read_odb(f)
        elif p.endswith(".zst"):
            with zstd.open(p) as f:
                yield from odc.read_odb(f)
        else:
            with open(p, "rb") as f:
                yield from odc.read_odb(f)


def valid_times_iterator(
    valid_times: list[str],
) -> Iterable[TimePoint]:
    """Convert a list of TimePoints or TimeRecurrences into an iterable of TimePoints."""
    # Make sure times are in UTC unless specified
    TPP = metomi.isodatetime.parsers.TimePointParser(assumed_time_zone=(0, 0))
    TRP = metomi.isodatetime.parsers.TimeRecurrenceParser(timepoint_parser=TPP)

    if valid_times is None:
        yield None
        return

    for vt in valid_times:
        if vt.startswith("R"):
            yield from TRP.parse(vt)
        else:
            yield TPP.parse(vt)


class PrepODB2(ABC):
    """
    Abstract base class for converting ODB2 data for MET.

    Subclasses can replace the read_odb function to set up patterns for their
    site.

    Usage:
    >>> converter = PrepODB2()
    >>> with open('obs.ascii', 'wt') as f:
    ...    converter.odb2ascii(f, valid_times)
    """

    @abstractmethod
    def read_odb(self, valid_time: TimePoint) -> Iterable[DataFrame]:
        """Read ODB2 data."""
        raise NotImplementedError

    def odb2ascii(self, output_pattern: str, valid_times: Iterable[TimePoint]):
        """
        Write all the observations to a MET ASCII file.
        
        If output_pattern contains a strftime-style pattern then the valid time
        will be used to replace the pattern.
        """
        for t in valid_times:
            output = t.strftime(output_pattern)

            if output == '-':
                out_context = nullcontext(sys.stdout)
            else:
                out_context = open(output, "wt")

            log.info("Processing %s", t)
            with out_context as f:
                for obs in self.read_odb(t):
                    ascii = odb2ascii_dataframe(obs)
                    write_ascii(ascii, f)


class PrepODB2Pattern(PrepODB2):
    """Prepare ODB2 data for MET, reading data using a file pattern."""

    def __init__(self, pattern: str):
        """
        Construct the converter.

        Pattern can use strftime templates which will be replaced by valid_time.
        Pattern can use shell globs.
        Recognised extensions for decompression are .gz, .bz2, .xz, .zst.

        Args:
            pattern: Pattern to use when opening files

        Usage:
        >>> converter = PrepODB2Pattern('/path/%Y/%m/%d/*.odb2')
        >>> with open('obs.ascii', 'wt') as f:
        ...    converter.odb2ascii(f, valid_times)
        """
        self.pattern = pattern

    def read_odb(self, valid_time: TimePoint) -> Iterable[DataFrame]:
        """
        Read in the ODB2 files.

        Args:
            valid_time: Time to use in file patterns
        """
        return read_file(self.pattern, valid_time)
