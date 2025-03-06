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

"""Tests for finish_website workflow utility."""

import json
import logging

from CSET._workflow_utils import finish_website


def test_write_workflow_status(monkeypatch, tmp_path):
    """Workflow  finish status gets written to status file."""
    web_dir = tmp_path / "web"
    web_dir.mkdir()
    monkeypatch.setenv("CYLC_WORKFLOW_SHARE_DIR", str(tmp_path))
    finish_website.update_workflow_status()
    with open(web_dir / "status.html", "rt", encoding="UTF-8") as fp:
        assert fp.read() == "<p>Finished</p>\n"


def test_construct_index(monkeypatch, tmp_path):
    """Test putting the index together."""
    monkeypatch.setenv("CYLC_WORKFLOW_SHARE_DIR", str(tmp_path))
    plots_dir = tmp_path / "web/plots"
    plots_dir.mkdir(parents=True)

    # Plot directories.
    plot1 = plots_dir / "p1/meta.json"
    plot1.parent.mkdir()
    plot1.write_text('{"category": "Category", "title": "P1", "case_date": "20250101"}')
    plot2 = plots_dir / "p2/meta.json"
    plot2.parent.mkdir()
    plot2.write_text('{"category": "Category", "title": "P2", "case_date": "20250101"}')

    # Non-plot directory also present.
    static_resource = plots_dir / "static/style.css"
    static_resource.parent.mkdir()
    static_resource.touch()

    # Construct index.
    finish_website.construct_index()

    # Check index.
    index_file = plots_dir / "index.json"
    assert index_file.is_file()
    with open(index_file, "rt", encoding="UTF-8") as fp:
        index = json.load(fp)
    expected = {"Category": {"20250101": {"p1": "P1", "p2": "P2"}}}
    assert index == expected


def test_construct_index_aggregation_case(monkeypatch, tmp_path):
    """Construct the index from a diagnostics without a case date."""
    monkeypatch.setenv("CYLC_WORKFLOW_SHARE_DIR", str(tmp_path))
    plots_dir = tmp_path / "web/plots"
    plots_dir.mkdir(parents=True)

    # Plot directories.
    plot1 = plots_dir / "p1/meta.json"
    plot1.parent.mkdir()
    plot1.write_text('{"category": "Category", "title": "P1"}')

    # Construct index.
    finish_website.construct_index()

    # Check index.
    index_file = plots_dir / "index.json"
    assert index_file.is_file()
    with open(index_file, "rt", encoding="UTF-8") as fp:
        index = json.load(fp)
    expected = {"Category": {"Aggregation": {"p1": "P1"}}}
    assert index == expected


def test_construct_index_invalid(monkeypatch, tmp_path, caplog):
    """Test constructing index when metadata is invalid."""
    monkeypatch.setenv("CYLC_WORKFLOW_SHARE_DIR", str(tmp_path))
    plots_dir = tmp_path / "web/plots"
    plots_dir.mkdir(parents=True)

    # Plot directories.
    plot = plots_dir / "p1/meta.json"
    plot.parent.mkdir()
    plot.write_text('"Not JSON!"')

    # Construct index.
    finish_website.construct_index()

    # Check log message.
    _, level, message = caplog.record_tuples[0]
    assert level == logging.ERROR
    assert "p1/meta.json is invalid, skipping." in message

    index_file = plots_dir / "index.json"
    assert index_file.is_file()
    with open(index_file, "rt", encoding="UTF-8") as fp:
        index = json.load(fp)
    expected = {}
    assert index == expected


def test_entrypoint(monkeypatch):
    """Test running the finish_website module."""
    # Count the number of times the other functions are run, to ensure they
    # are both run.
    counter = 0

    def increment_counter():
        nonlocal counter
        counter += 1

    monkeypatch.setattr(finish_website, "construct_index", increment_counter)
    monkeypatch.setattr(finish_website, "update_workflow_status", increment_counter)

    # Just check that it runs all the needed subfunctions.
    finish_website.run()
    assert counter == 2
