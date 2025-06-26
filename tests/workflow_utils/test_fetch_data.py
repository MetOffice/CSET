# © Crown copyright, Met Office (2022-2024) and CSET contributors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for fetch_data workflow utility."""

import datetime
import hashlib
from pathlib import Path

import pytest

from CSET._workflow_utils import fetch_data


def mock_get_needed_environment_variables():
    """Minimal set of environment variables for running a mock fetch_data."""
    return {
        "data_period": None,
        "data_time": None,
        "date_type": None,
        "forecast_length": None,
        "forecast_offset": None,
        "model_identifier": "1",
        "raw_path": None,
        "rose_datac": "/tmp/cycle/20000101T0000Z",
    }


def mock_template_file_path(*args, **kwargs):
    """List of paths for testing with."""
    return [f"path_{n}" for n in range(5)]


def test_get_needed_environment_variables(monkeypatch):
    """Needed environment variables are loaded."""
    duration_raw = "PT1H"
    duration = datetime.timedelta(hours=1)
    date_raw = "20000101T0000Z"
    date = datetime.datetime(2000, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)
    path = "/path/to/data"
    number_raw = "1"

    monkeypatch.setenv("ANALYSIS_OFFSET", duration_raw)
    monkeypatch.setenv("ANALYSIS_LENGTH", duration_raw)
    monkeypatch.setenv("CYLC_TASK_CYCLE_POINT", date_raw)
    monkeypatch.setenv("DATA_PATH", path)
    monkeypatch.setenv("DATA_PERIOD", duration_raw)
    monkeypatch.setenv("MODEL_IDENTIFIER", number_raw)
    monkeypatch.setenv("ROSE_DATAC", path)
    monkeypatch.setenv("DATE_TYPE", "validity")

    expected = {
        "data_period": duration,
        "data_time": date,
        "date_type": "validity",
        "forecast_length": duration,
        "forecast_offset": duration,
        "model_identifier": number_raw,
        "raw_path": path,
        "rose_datac": path,
    }
    actual = fetch_data._get_needed_environment_variables()
    assert actual == expected, "Unexpected values from reading environment variables"


def test_get_needed_environment_variables_data_period_handling(monkeypatch):
    """Handle data_period dependent on date type."""
    duration_raw = "PT1H"
    date_raw = "20000101T0000Z"
    path = "/path/to/data"
    number_raw = "1"

    monkeypatch.setenv("ANALYSIS_OFFSET", duration_raw)
    monkeypatch.setenv("ANALYSIS_LENGTH", duration_raw)
    monkeypatch.setenv("CYLC_TASK_CYCLE_POINT", date_raw)
    monkeypatch.setenv("DATA_PATH", path)
    monkeypatch.setenv("MODEL_IDENTIFIER", number_raw)
    monkeypatch.setenv("ROSE_DATAC", path)

    # Check DATA_PERIOD is not there for initiation.
    monkeypatch.setenv("DATE_TYPE", "initiation")
    initiation_actual = fetch_data._get_needed_environment_variables()
    assert initiation_actual["data_period"] is None, (
        "data_period should not be set for initiation time"
    )

    # Check exception when data period is not specified for validity time.
    monkeypatch.setenv("DATE_TYPE", "validity")
    with pytest.raises(KeyError):
        fetch_data._get_needed_environment_variables()


def test_fetch_data(monkeypatch):
    """Check get_file is called appropriately when fetching data."""
    actually_called = False

    class MockFileRetriever(fetch_data.FileRetrieverABC):
        def get_file(self, file_path: str, output_dir: str) -> None:
            nonlocal actually_called
            actually_called = True
            return True

    monkeypatch.setattr(
        fetch_data,
        "_get_needed_environment_variables",
        mock_get_needed_environment_variables,
    )
    monkeypatch.setattr(fetch_data, "_template_file_path", mock_template_file_path)
    fetch_data.fetch_data(MockFileRetriever)
    assert actually_called


def test_fetch_data_no_files_found(monkeypatch):
    """Check exception is raised when no files found."""
    actually_called = False

    class MockFileRetrieverNoFiles(fetch_data.FileRetrieverABC):
        def get_file(self, file_path: str, output_dir: str) -> None:
            nonlocal actually_called
            actually_called = True
            return False

    monkeypatch.setattr(
        fetch_data,
        "_get_needed_environment_variables",
        mock_get_needed_environment_variables,
    )
    monkeypatch.setattr(fetch_data, "_template_file_path", mock_template_file_path)
    with pytest.raises(FileNotFoundError, match="No files found for model!"):
        fetch_data.fetch_data(MockFileRetrieverNoFiles)

    assert actually_called


def test_template_file_path_validity_time():
    """Test filling path placeholders for validity time."""
    actual = fetch_data._template_file_path(
        "/path/%Y-%m-%d.nc",
        "validity",
        datetime.datetime(2000, 1, 1, tzinfo=datetime.timezone.utc),
        datetime.timedelta(days=5),
        datetime.timedelta(),
        datetime.timedelta(days=1),
    )
    expected = [
        "/path/2000-01-01.nc",
        "/path/2000-01-02.nc",
        "/path/2000-01-03.nc",
        "/path/2000-01-04.nc",
        "/path/2000-01-05.nc",
    ]
    assert actual == expected


def test_template_file_path_initiation_time():
    """Test filling path placeholders for initiation time."""
    actual = fetch_data._template_file_path(
        "/path/%Y-%m-%d.nc",
        "initiation",
        datetime.datetime(2000, 1, 1, tzinfo=datetime.timezone.utc),
        datetime.timedelta(days=5),
        datetime.timedelta(),
        datetime.timedelta(days=1),
    )
    expected = ["/path/2000-01-01.nc"]
    assert actual == expected


def test_template_file_path_lead_time():
    """Test filling path placeholders for lead time."""
    actual = fetch_data._template_file_path(
        "/path/%N.nc",
        "initiation",
        datetime.datetime(2000, 1, 1, tzinfo=datetime.timezone.utc),
        datetime.timedelta(hours=5, seconds=1),
        datetime.timedelta(hours=1),
        datetime.timedelta(hours=1),
    )
    expected = [
        "/path/001.nc",
        "/path/002.nc",
        "/path/003.nc",
        "/path/004.nc",
        "/path/005.nc",
    ]
    assert actual == expected


def test_template_file_path_invalid_date_type():
    """Test error on invalid date type."""
    with pytest.raises(ValueError, match="Invalid date type:"):
        fetch_data._template_file_path(None, "Other", None, None, None, None)


def test_FilesystemFileRetriever(tmp_path):
    """Test retrieving a file from the filesystem."""
    with fetch_data.FilesystemFileRetriever() as ffr:
        files_found = ffr.get_file("tests/test_data/exeter_em*.nc", str(tmp_path))
    # Correct return value.
    assert files_found
    # Symlinks created. Technically this checks that the files the symlink
    # points to exists, but that is good enough here, and the follow_symlinks
    # argument requires python 3.12.
    assert (tmp_path / "exeter_em01.nc").exists()
    assert (tmp_path / "exeter_em02.nc").exists()
    # Check symlink points to correct file.
    with open((tmp_path / "exeter_em01.nc"), "rb") as fp:
        digest = hashlib.file_digest(fp, "sha256").hexdigest()
    assert digest == "67899970eeca75b9378f0275ce86db3d1d613f2bc7a178540912848dc8a69ca7"


def test_FilesystemFileRetriever_no_files(tmp_path, caplog):
    """Test warning when no files match the requested path."""
    with fetch_data.FilesystemFileRetriever() as ffr:
        # Should warn, but not error.
        files_found = ffr.get_file("/non-existent/file.nc", str(tmp_path))
    log_record = next(
        filter(
            lambda record: record.message.startswith(
                "file_path does not match any files:"
            ),
            caplog.records,
        ),
        None,
    )
    assert log_record
    assert log_record.levelname == "WARNING"
    assert not files_found


def test_FilesystemFileRetriever_copy_error(caplog):
    """Test warning when file copy errors."""
    with fetch_data.FilesystemFileRetriever() as ffr:
        # Please don't run as root.
        files_found = ffr.get_file("tests/test_data/air_temp.nc", "/usr/bin")
    assert not Path("/usr/bin/air_temp.nc").is_file()
    log_record = next(
        filter(
            lambda record: record.message.startswith("Failed to copy"), caplog.records
        ),
        None,
    )
    assert log_record
    assert log_record.levelname == "WARNING"
    assert not files_found


@pytest.mark.network
def test_HTTPFileRetriever(tmp_path):
    """Test retrieving a file via HTTP."""
    url = "https://github.com/MetOffice/CSET/raw/48dc1d29846604aacb8d370b82bca31405931c87/tests/test_data/exeter_em01.nc"
    with fetch_data.HTTPFileRetriever() as hfr:
        files_found = hfr.get_file(url, str(tmp_path))
    file = tmp_path / "exeter_em01.nc"
    assert file.is_file()
    # Check file hash is correct, indicating a non-corrupt download.
    expected_hash = "67899970eeca75b9378f0275ce86db3d1d613f2bc7a178540912848dc8a69ca7"
    actual_hash = hashlib.sha256(file.read_bytes()).hexdigest()
    assert actual_hash == expected_hash
    assert files_found


@pytest.mark.network
def test_HTTPFileRetriever_no_files(tmp_path, caplog):
    """Test warning rather than error when requested URL does not exist."""
    with fetch_data.HTTPFileRetriever() as hfr:
        # Should warn, but not error.
        files_found = hfr.get_file("http://httpbin.org/status/404", str(tmp_path))
    log_record = next(
        filter(
            lambda record: record.message.startswith(
                "Failed to retrieve http://httpbin.org/status/404, error:"
            ),
            caplog.records,
        ),
        None,
    )
    assert log_record
    assert log_record.levelname == "WARNING"
    assert not files_found
