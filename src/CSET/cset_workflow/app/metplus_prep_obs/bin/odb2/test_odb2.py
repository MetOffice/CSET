"""Tests for ODB2 to MET ASCII conversion."""

import io

import numpy
import pandas

from .odb2 import (
    ASCII_COLUMNS,
    get_height,
    get_level,
    get_type,
    odb2ascii_dataframe,
    write_ascii,
)


def test_get_level():
    """Test get_level."""
    obs = pandas.DataFrame(
        [
            {
                "name@varno": "t",
                "vertco_type@body": 1,
                "vertco_reference_1@body": 250,
            },
            {
                "name@varno": "t",
                "vertco_type@body": 5,
                "vertco_reference_1@body": 1,
            },
        ]
    )
    print(obs)
    levels = get_level(obs)
    # Pressure level
    assert levels.iloc[0] == 250
    # Surface level
    assert numpy.isnan(levels.iloc[1])


def test_get_height():
    """Test get_height."""
    obs = pandas.DataFrame(
        [
            {
                "name@varno": "t",
                "vertco_type@body": 1,
                "vertco_reference_1@body": 250,
            },
            {
                "name@varno": "t",
                "vertco_type@body": 5,
                "vertco_reference_1@body": 1,
            },
        ]
    )
    print(obs)
    levels = get_height(obs)
    # Pressure level
    assert numpy.isnan(levels.iloc[0])
    # Surface level
    assert levels.iloc[1] == 0


def test_get_type():
    """Test get_type."""
    obs = pandas.DataFrame(
        [
            {
                "reportype@hdr": 9999,
                "bufrtype@reporttype": "Land Surface",
            },
            {
                "reportype@hdr": 9999,
                "bufrtype@reporttype": None,
            },
        ]
    )
    types = get_type(obs)
    assert types.iloc[0] == "ADPSFC"
    assert types.iloc[1] == 9999


def test_odb2ascii_dataframe():
    """Test odb2ascii_dataframe."""
    obs = pandas.DataFrame(
        [
            {
                "reportype@hdr": 16001,
                "report_status@hdr": 1,
                "date@hdr": 20010101,
                "time@hdr": 10000,
                "datum_status@body": 1,
                "varno@body": 39,
                "statid@hdr": "DUMMY",
                "lat@hdr": 10,
                "lon@hdr": 20,
                "stalt@hdr": 30,
                "obsvalue@body": 40,
                "vertco_type@body": 5,
                "vertco_reference_1@body": 1,
            }
        ]
    )
    ascii = odb2ascii_dataframe(obs)
    row = ascii.iloc[0]
    assert row["Message_Type"] == "ADPSFC"
    assert row["Station_ID"] == "DUMMY"
    assert row["Valid_Time"] == pandas.Timestamp("20010101T0100Z")
    assert row["Elevation"] == 30
    assert row["Variable_Name"] == "t2m"


def test_write_ascii():
    """Test write_ascii."""
    output = io.StringIO()
    ascii = pandas.DataFrame(
        [
            [
                "ADPSFC",
                "DUMMY",
                pandas.Timestamp("20010101T0100Z"),
                10,
                20,
                30,
                "t2m",
                numpy.nan,
                0,
                "NA",
                40,
            ]
        ],
        columns=ASCII_COLUMNS,
    )
    write_ascii(ascii, output)
    expect = "ADPSFC\tDUMMY\t20010101_0100\t10\t20\t30\tt2m\tNA\t0\tNA\t40\n"
    assert output.getvalue() == expect
