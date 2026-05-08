#!/usr/bin/env python3

"""
Convert ODB2 data to MET ASCII format.

Paths can use strftime formatting and shell globs - all matching ODB2 files \
will be loaded into the same ASCII file.
Valid times can be either ISO timepoints or recurrences, and are used to \
replace any strftime patterns.

    ./prepODB2.py /path/to/%Y/%m/%Y%m%dT%H%MZ/*.odb \\
            --valid-time 20010101T0000Z \\
            --valid-time R4/20010102T0000Z/PT6H \\
            --output obs.ascii
"""

epilog="""
ASCII Column Info:
 0 - Message_Type: uses PrepBUFR names where known, otherwise the ODB \
reportype@hdr value
 1 - Station_ID: statid@hdr
 2 - Valid_Time: date@hdr_time@hdr
 3 - Lat: lat@hdr
 4 - Lon: lon@hdr
 5 - Elevation: stalt@hdr
 6 - Variable_Name: uses ODB variable names from \
https://codes.ecmwf.int/odb/varno/
 7 - Level: is the observation pressure level (where available)
 8 - Height: is 0 for surface observations
 9 - QC_String: unused
10 - Observation_Value: obsvalue@body

https://metplus.readthedocs.io/projects/met/en/latest/Users_Guide/reformat_point.html#table-reformat-point-ascii2nc-format
"""

import pandas
import numpy
import functools
import json
from typing import TextIO, Iterable
import sys
from contextlib import nullcontext
import argparse
from pathlib import Path
import gzip
import metomi.isodatetime.data, metomi.isodatetime.parsers
import logging
import glob

log = logging.getLogger(__name__)

try:
    import codc as odc
except ImportError:
    import pyodc as odc

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

# Local report types defined in OBS
local_report_type = {
    98001: {'name': 'modes', 'description': 'MODE-S'},
    98002: {'name': 'radar_scan', 'description': 'Radar scan data'},
    98016: {'name': 'osseaice', 'description': 'Ocean and Sea Ice SAF'},
    98031: {'name': 'oceancolour', 'description': 'Ocean colour data'},
    98032: {'name': 'ocean_wave', 'description': 'WAVENET ocean wave data'},
    98036: {'name': 'insat_3d_imager', 'description': 'INSAT 3D imager'},
    98037: {'name': 'insat_3d_sounder', 'description': 'INSAT 3D sounder'},
    98038: {'name': 'oceanwinds', 'description': 'Satellite ccean surface wind speeds'},
    98039: {'name': 'gmi_rad_low', 'description': 'GPM GMI radiances (all-sky, low)'},
    98040: {'name': 'gmi_rad_high', 'description': 'GPM GMI radiances (all-sky, high)'},
    98041: {'name': 'aladin_hloswind', 'description': 'HLOSWINDS from Aeolus(aladin)'},
    98042: {'name': 'metop_c_satsst', 'description': 'SatSST METOP-C'},
    98043: {'name': 'metop_c_gpsro', 'description': 'METOP-C GPSRO'},
    98044: {'name': 'metop_c_amv', 'description': 'METOP-C AMV'},
    98045: {'name': 'metop_c_ascat', 'description': 'METOP-C ASCAT'},
    98046: {'name': 'metop_c_iasi_rad', 'description': 'METOP-C IASI radiances'},
    98047: {'name': 'metop_c_mhs_rad', 'description': '"AMSUB" (MHS really) MetOp C'},
    98048: {'name': 'atovs_metop_c', 'description': 'UKMO ATOVS data (Metop C)'},
    98049: {'name': 'goes_17_geos_rad', 'description': 'GOES-17 GEOS Radiances'},
    98050: {'name': 'fy3d_cris', 'description': 'FY-3D CriS'},
    98051: {'name': 'fy3_d_hiras_rad', 'description': 'HIRAS FY-3D'},
    98052: {'name': 'moored_buoy', 'description': 'Moored buoys (non BUFR)'},
    98053: {'name': 'emaddc', 'description': 'EMADDC'},
    98054: {'name': 'giirs_fy4a', 'description': 'GIIRS FY-4A'},
    98055: {'name': 'goes_18_amv', 'description': 'GOES 18 AMV'},
    98056: {'name': 'goes_19_amv', 'description': 'GOES 19 AMV'},
    98057: {'name': 'noaa_21_amv', 'description': 'NOAA 21 AVHRR IR AMV'},
    98058: {'name': 'fy2h_amv', 'description': 'FY-2H IR AMV'},
    98059: {'name': 'fy4a_amv', 'description': 'FY-2H IR AMV'},
    98060: {'name': 'fy4b_amv', 'description': 'FY-2H IR AMV'},
    98061: {'name': 'oceansat_3a_ascat', 'description': 'OCEANSAT-3A ASCAT'},
    98062: {'name': 'hy2c_ascat', 'description': 'HY2C ASCAT'},
    98063: {'name': 'fy3e_ascat', 'description': 'FY3E ASCAT'},
    98064: {'name': 'insat_3dr_amv', 'description': 'INSAT-3DR AMV'},
    98065: {'name': 'insat_3ds_amv', 'description': 'INSAT-3DS AMV'},
    98066: {'name': 'geokompsat_2a_amv', 'description': 'GEOKOMPSAT-2A AMV'},
    98067: {'name': 'meteosat_13_mtgirs', 'description': 'MTG-S1 IRS radiances'},
    98068: {'name': 'giirs_fy4b', 'description': 'GIIRS FY-4B'},
}

def read_odb_table(table: str, index: str) -> pandas.DataFrame:
    """
    Read ECMWF ODB tables as a dataframe.

    Table info comes from https://codes.ecmwf.int/odb
    """
    path = Path(__file__).parent.parent/f'file/odb2/{table}.json.gz'

    with gzip.open(path) as f:
        j = json.load(f)
    df = pandas.DataFrame(
        j["data"], columns=[f + f"@{table}" for f in j["fields"]]
    )
    
    return df.set_index(f"{index}@{table}")


@functools.cache
def varno_table() -> pandas.DataFrame:
    """ODB variable information as a dataframe."""
    return read_odb_table("varno", index="code")

@functools.cache
def reporttype_table() -> pandas.DataFrame:
    """ODB report_type information as a dataframe."""
    return read_odb_table("reporttype", index="id")

def get_level(obs: pandas.DataFrame) -> pandas.Series:
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

    plevel = obs['vertco_reference_1@body'].where(obs['vertco_type@body'].isin([1,11,15]), numpy.nan)

    accumulated_fields = ['PRATE','TSTM','APCP','NCPCP','ACPCP']
    if obs['name@varno'].isin(accumulated_fields).any():
        raise NotImplementedError("Accumulated fields not implemented")
    return plevel


def get_height(obs: pandas.DataFrame) -> pandas.Series:
    """
    Get the height parameter for each observation.
    
    This is defined as height ASL, but this is matched against Z levels so for
    surface values we set it to 0 so they can be found with 'Z0'.

    In the metplus config find matching values with

        OBS_VAR<N>_LEVELS = Z0

    to match against surface fields

    ODB vertical coordinate types are enumerated at
    https://code.metoffice.gov.uk/trac/ops/browser/main/trunk/src/code/ODB/sql/vertco_type.hh
    """

    surface_fields = (obs['vertco_type@body'] == 5) & (obs['vertco_reference_1@body'] == 1)

    hlevel = (obs['vertco_reference_1@body']*0).where(surface_fields, numpy.nan)
    return hlevel

def get_type(obs: pandas.DataFrame) -> pandas.Series:
    """
    Get the PrepBUFR message type for each observation.

    Valid PrepBUFR message types are listed at
    https://www.emc.ncep.noaa.gov/mmb/data_processing/prepbufr.doc/table_1.htm

    ODB message types are listed at
    https://codes.ecmwf.int/odb/unionall/

    There are also some custom OPS report types enumerated at
    https://code.metoffice.gov.uk/trac/ops/browser/main/trunk/src/code/ODB/sql/report_types.hh
    """
    odb_prepbufr_map = {
        'AIREP': 'AIRCFT', 
        'Land Surface': 'ADPSFC',
        'Sea Surface': 'SFCSHP',
        'Upper Air Sounding': 'ADPUPA',
    }

    types = obs['bufrtype@reporttype'].map(lambda t: odb_prepbufr_map.get(t, 'NA'))
    types = types.where(types != 'NA', obs['reportype@hdr'])
    return types


def odb2ascii_dataframe(obs: pandas.DataFrame) -> pandas.DataFrame:
    """
    Convert a pandas.DataFrame from pyodc to MET ASCII format.

    args:
        obs: ODB2 data loaded with pyodb
    
    Output format is described at
    https://metplus.readthedocs.io/projects/met/en/latest/Users_Guide/reformat_point.html#id9
    """

    # QC filter for only active values
    obs = obs[(obs['report_status@hdr'] | obs['datum_status@body']) == 1]

    # Join in extra info
    obs = obs.join(varno_table(), on="varno@body")
    obs = obs.join(reporttype_table(), on="reportype@hdr")

    ascii = pandas.DataFrame(columns=ASCII_COLUMNS)

    ascii["Message_Type"] = get_type(obs)
    ascii["Station_ID"] = obs["statid@hdr"]
    ascii["Valid_Time"] = pandas.to_datetime(
        obs["date@hdr"].astype(str) + "_" + obs["time@hdr"].astype(str).str.zfill(6)
    , format="%Y%m%d_%H%M%S")
    ascii["Lat"] = obs["lat@hdr"]
    ascii["Lon"] = obs["lon@hdr"]
    ascii["Elevation"] = obs["stalt@hdr"]
    ascii["Variable_Name"] = obs["name@varno"]

    ascii["Level"] = get_level(obs)
    ascii["Height"] = get_height(obs)

    ascii["QC_String"] = 'NA'

    ascii["Observation_Value"] = obs["obsvalue@body"]

    return ascii


def odb2ascii(input_pattern: Path, output: TextIO, valid_times: Iterable[metomi.isodatetime.data.TimePoint | None]):
    """
    Read in an ODB2 file, output MET format ASCII data.

    input paths can have strftime-style patterns, which will be replaced by
    values from valid_times, and shell globbing.

    Args:
        input: Input file path pattern
        output: Output stream
        valid_times: Times to fill the input pattern with
    """
    for time in valid_times:
        log.info('Valid time %s', time)
        for path in glob.glob(str(fill_pattern(input_pattern, time))):
            log.info('Loading %s', path)
            with open(path, 'rb') as input:
                for obs in odc.read_odb(input):
                    df = odb2ascii_dataframe(obs)
                    df.to_csv(output, sep='\t', date_format='%Y%m%d_%H%M', na_rep='NA', index=False, header=False)


def fill_pattern(pattern: Path, time: metomi.isodatetime.data.TimePoint | None) -> Path:
    """
    Fill in time placeholders in a path, replacing date components like strftime
    """
    if time is None:
        return pattern

    return Path(time.strftime(str(pattern)))

def valid_times_iterator(valid_times: list[str]) -> Iterable[metomi.isodatetime.data.TimePoint | None]:
    """
    Convert a list of TimePoints or TimeRecurrences into an iterable of TimePoints
    """
    # Make sure times are in UTC unless specified
    TPP = metomi.isodatetime.parsers.TimePointParser(assumed_time_zone=(0,0))
    TRparse = metomi.isodatetime.parsers.TimeRecurrenceParser(timepoint_parser=TPP).parse
    TPparse = TPP.parse

    if valid_times is None:
        yield None
        return

    for vt in valid_times:
        if vt.startswith('R'):
            yield from TRparse(vt)
        else:
            yield TPparse(vt)

def main():
    parser = argparse.ArgumentParser(description=__doc__, epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("file", nargs="+", help="ODB2 files to load (can be strftime-formatted with values replaced using the list from --valid-times)")
    parser.add_argument("--output", "-o", help="output path", default="-")
    parser.add_argument("--valid-time", "-t", help="valid times to load (ISO format, e.g. '20100512T1200', 'R4/20010101T0000Z/PT6H')", action='append')
    parser.add_argument("--verbose", "-v", help="verbose", action='store_true')
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig()

    if args.output == "-":
        out_context = nullcontext(sys.stdout)
    else:
        out_context = open(args.output, "wt")

    with out_context as output:
        for pattern in args.file:
            odb2ascii(pattern, output, valid_times_iterator(args.valid_time))

if __name__ == '__main__':
    main()
