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

from datetime import UTC, datetime, timedelta

import pytest

from CSET._workflow_utils import fetch_data


def test_get_needed_environment_variables(monkeypatch):
    """Needed environment variables are loaded."""
    duration_raw = "PT1H"
    duration = timedelta(hours=1)
    date_raw = "20000101T0000Z"
    date = datetime(2000, 1, 1, 0, 0, tzinfo=UTC)
    path = "/path/to/data"
    number_raw = "1"

    monkeypatch.setenv("CSET_ANALYSIS_OFFSET", duration_raw)
    monkeypatch.setenv("CSET_ANALYSIS_PERIOD", duration_raw)
    monkeypatch.setenv("CYLC_TASK_CYCLE_POINT", date_raw)
    monkeypatch.setenv("CYLC_WORKFLOW_SHARE_DIR", path)
    monkeypatch.setenv("DATA_PATH", path)
    monkeypatch.setenv("DATA_PERIOD", duration_raw)
    monkeypatch.setenv("MODEL_NUMBER", number_raw)
    monkeypatch.setenv("DATE_TYPE", "validity")

    expected = {
        "cycle_point": date_raw,
        "data_period": duration,
        "data_time": date,
        "date_type": "validity",
        "forecast_length": duration,
        "forecast_offset": duration,
        "model_number": number_raw,
        "raw_path": path,
        "share_dir": path,
    }
    actual = fetch_data._get_needed_environment_variables()
    assert actual == expected

    # Check DATA_PERIOD is not there for initiation.
    monkeypatch.setenv("DATE_TYPE", "initiation")
    initiation_actual = fetch_data._get_needed_environment_variables()
    assert "data_period" not in initiation_actual


def test_fetch_data(monkeypatch, tmp_path):
    """Test top-level fetch_data function with other calls mocked out."""

    def mock_get_needed_environment_variables():
        return {
            "share_dir": str(tmp_path),
            "cycle_point": "20000101T0000Z",
            "model_number": "1",
            "raw_path": None,
            "date_type": None,
            "data_time": None,
            "forecast_length": None,
            "forecast_offset": None,
            "data_period": None,
        }

    def mock_template_file_path(*args, **kwargs):
        return [f"path_{n}" for n in range(5)]

    files_gotten = False

    class MockFileRetriever(fetch_data.FileRetriever):
        def get_file(self, file_path: str, output_dir: str) -> None:
            nonlocal files_gotten
            files_gotten = True

    monkeypatch.setattr(
        fetch_data,
        "_get_needed_environment_variables",
        mock_get_needed_environment_variables,
    )
    monkeypatch.setattr(fetch_data, "_template_file_path", mock_template_file_path)
    fetch_data.fetch_data(MockFileRetriever)
    assert files_gotten


def test_template_file_path_validity_time():
    """Test filling path placeholders for validity time."""
    actual = fetch_data._template_file_path(
        "/path/%Y-%m-%d.nc",
        "validity",
        datetime(2000, 1, 1, tzinfo=UTC),
        timedelta(days=5),
        timedelta(),
        timedelta(days=1),
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
        datetime(2000, 1, 1, tzinfo=UTC),
        timedelta(days=5),
        timedelta(),
        None,
    )
    expected = ["/path/2000-01-01.nc"]
    assert actual == expected


def test_template_file_path_lead_time():
    """Test filling path placeholders for lead time."""
    actual = fetch_data._template_file_path(
        "/path/%N.nc",
        "lead",
        datetime(2000, 1, 1, tzinfo=UTC),
        timedelta(hours=5, seconds=1),
        timedelta(hours=1),
        timedelta(hours=1),
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
        ffr.get_file("tests/test_data/exeter_em*.nc", str(tmp_path))
    assert (tmp_path / "exeter_em01.nc").is_file()
    assert (tmp_path / "exeter_em02.nc").is_file()
