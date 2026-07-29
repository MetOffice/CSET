"""Tests for ODB2 to MET ASCII conversion."""

import io
from unittest.mock import patch

import numpy
import pandas

from .odb2 import (
    ASCII_COLUMNS,
    PrepODB2Pattern,
    get_height,
    get_level,
    get_type,
    odb2ascii_dataframe,
    read_odb_sql,
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
            },
            # Report with no station id, should get na value
            {
                "reportype@hdr": 16029,
                "report_status@hdr": 1,
                "date@hdr": 20010101,
                "time@hdr": 10000,
                "datum_status@body": 1,
                "varno@body": 111,
                "statid@hdr": "      ",
                "lat@hdr": 10,
                "lon@hdr": 20,
                "stalt@hdr": 10000,
                "obsvalue@body": 40,
                "vertco_type@body": 11,
                "vertco_reference_1@body": 20000,
            },
        ]
    )
    ascii = odb2ascii_dataframe(obs)
    row = ascii.iloc[0]
    assert row["Message_Type"] == "ADPSFC"
    assert row["Station_ID"] == "DUMMY"
    assert row["Valid_Time"] == pandas.Timestamp("20010101T0100Z")
    assert row["Elevation"] == 30
    assert row["Variable_Name"] == "t2m"

    row = ascii.iloc[1]
    assert row["Message_Type"] == "AIRCFT"
    assert row["Station_ID"] == "NA"
    assert row["Variable_Name"] == "dd"


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


def test_read_odb():
    """Test read_odb."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = (
            "name@varno\tvertco_type@body\tvertco_reference_1@body\n"
        )
        mock_run.return_value.returncode = 0
        df = read_odb_sql(
            io.BytesIO(), ["name@varno", "vertco_type@body", "vertco_reference_1@body"]
        )
        assert isinstance(df, pandas.DataFrame)
        assert list(df.columns) == [
            "name@varno",
            "vertco_type@body",
            "vertco_reference_1@body",
        ]


def test_PrepODB_read(tmp_path):
    """Check the prepODB2 read_odb method returns a DataFrame with the expected columns."""
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
            },
        ]
    )

    (tmp_path / "test.odb2").write_text("")
    pattern = str(tmp_path / "test.odb2")

    with patch("odb2.odb2.read_odb_sql") as mock_read_odb_sql:
        mock_read_odb_sql.return_value = obs

        prep = PrepODB2Pattern(pattern)
        df = next(prep.read_odb(pandas.Timestamp("20010101T0100Z")))
        assert isinstance(df, pandas.DataFrame)

        assert df["reportype@hdr"].iloc[0] == 16001
