"""Tests for ODB2 reading."""

import subprocess
from pathlib import Path
from shutil import which
from textwrap import dedent

import pandas
import pytest

from .obs import obs_dataframe_columns, obs_station_columns
from .odb2 import odb2_to_obs_dataframe


@pytest.fixture
def odc() -> str:
    """Make sure ODC is available."""
    odc = which("odc")
    if odc is None:
        pytest.skip("ODC is not installed")
    return odc


@pytest.fixture
def sample_odb(tmp_path: Path, odc: str) -> Path:
    """Generate a sample odb file."""
    sample_file = tmp_path / "sample.txt"
    sample_file.write_text(
        dedent("""\
    date@hdr:INTEGER, time@hdr:INTEGER, statid@hdr:STRING, lat@hdr:REAL, lon@hdr:REAL, stalt@hdr:REAL, reportype@hdr:INTEGER, varno@body:INTEGER, obsvalue@body:REAL,vertco_type@body:INTEGER,vertco_reference_1@body:REAL,report_status@hdr:INTEGER, datum_status@body:INTEGER
    20260701,             0,'94827   ',    -36.309200,    141.648605,    140.000000,         16001,           107,  99030.000000,               5,               1.000000,                1,                1
    20260701,             0,'94827   ',    -36.309200,    141.648605,    140.000000,         16001,            39,    285.556610,               5,               1.000000,                1,                1
    20260701,             0,'94827   ',    -36.309200,    141.648605,    140.000000,         16001,           111,     30.000000,               5,               1.000000,                1,                1
    """)
    )

    odb_file = tmp_path / "sample.odb2"
    subprocess.run([odc, "import", str(sample_file), str(odb_file)], check=True)
    return odb_file


def test_odb_to_obs_dataframe(sample_odb: Path):
    """Test the conversion of an ODB2 file to our observation dataframe."""
    df = odb2_to_obs_dataframe([sample_odb])
    assert len(df) == 3
    for c in obs_dataframe_columns:
        assert c in df.columns
    for c in obs_station_columns:
        assert c in df.columns

    assert df.iloc[0]["valid"] == pandas.to_datetime("20260701T0000Z")
    assert df.iloc[0]["station_id"] == "94827"
