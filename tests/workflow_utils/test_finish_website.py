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
import re
from pathlib import Path

from CSET.cset_workflow.app.finish_website.bin import finish_website


def test_install_website_skeleton(monkeypatch, tmp_path):
    """Check static files are copied correctly."""
    www_content = tmp_path / "web"
    www_root_link = tmp_path / "www/CSET"
    monkeypatch.chdir("src/CSET/cset_workflow/app/finish_website/file")
    finish_website.install_website_skeleton(www_root_link, www_content)
    assert www_content.is_dir()
    assert (www_content / "index.html").is_file()
    assert (www_content / "script.js").is_file()
    assert (www_content / "plots").is_dir()
    assert www_root_link.is_symlink()
    assert www_root_link.resolve() == www_content.resolve()


def test_copy_rose_config(monkeypatch, tmp_path):
    """Copy rose-suite.conf to web dir."""
    rose_suite_conf = tmp_path / "rose-suite.conf"
    with open(rose_suite_conf, "wt") as fp:
        fp.write("Test rose-suite.conf file\n")
    web_dir = tmp_path / "web"
    web_dir.mkdir()
    monkeypatch.setenv("CYLC_WORKFLOW_RUN_DIR", str(tmp_path))
    finish_website.copy_rose_config(web_dir)
    with open(web_dir / "rose-suite.conf", "rt", encoding="UTF-8") as fp:
        assert fp.read() == "Test rose-suite.conf file\n"


def test_bust_cache(tmp_path):
    """Cache busting query string is added where requested."""
    with open(tmp_path / "index.html", "wt") as fp:
        fp.write('<img href="image.jpg?v=CACHEBUSTER" />\n')
    (tmp_path / "plots").mkdir()
    finish_website.bust_cache(tmp_path)
    # Check cache busting query has been added.
    with open(tmp_path / "index.html", "rt") as fp:
        content = fp.read()
    assert "CACHEBUSTER" not in content
    assert re.search(r"\?v=\d+", content)
    renamed_plot_dir = list(tmp_path.glob("plots-*"))
    assert len(renamed_plot_dir) == 1
    assert renamed_plot_dir[0].is_dir()


def test_write_workflow_status(tmp_path):
    """Workflow finish status gets written to placeholder file."""
    web_dir = tmp_path / "web"
    web_dir.mkdir()
    with open(web_dir / "placeholder.html", "wt") as fp:
        fp.write('<h3>Workflow status</h3>\n<p id="workflow-status">Unknown</p>\n')
    finish_website.update_workflow_status(web_dir)
    # Check status is written correctly.
    pattern = r"Completed at \d{4}-\d\d-\d\d \d\d:\d\d using CSET v\d+"
    with open(web_dir / "placeholder.html", "rt", encoding="UTF-8") as fp:
        content = fp.read()
    assert re.search(pattern, content)


def test_construct_index(tmp_path):
    """Test putting the index together."""
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
    finish_website.construct_index(plots_dir.parent)

    # Check index.
    index_file = plots_dir / "index.jsonl"
    assert index_file.is_file()
    with open(index_file, "rt", encoding="UTF-8") as fp:
        index = fp.read()
    expected = (
        '{"case_date":"20250101","category":"Category","path":"p1","title":"P1"}\n'
        '{"case_date":"20250101","category":"Category","path":"p2","title":"P2"}\n'
    )
    assert index == expected


def test_construct_index_aggregation_case(tmp_path):
    """Construct the index from a diagnostics without a case date."""
    plots_dir = tmp_path / "web/plots"
    plots_dir.mkdir(parents=True)

    # Plot directories.
    plot1 = plots_dir / "p1/meta.json"
    plot1.parent.mkdir()
    plot1.write_text('{"category": "Category", "title": "P1"}')

    # Construct index.
    finish_website.construct_index(plots_dir.parent)

    # Check index.
    index_file = plots_dir / "index.jsonl"
    assert index_file.is_file()
    with open(index_file, "rt", encoding="UTF-8") as fp:
        index = json.load(fp)
    expected = {"category": "Category", "path": "p1", "title": "P1"}
    assert index == expected


def test_construct_index_remove_keys(tmp_path):
    """Unneeded keys are removed from the index."""
    plots_dir = tmp_path / "web/plots"
    plots_dir.mkdir(parents=True)

    # Plot directories.
    plot1 = plots_dir / "p1/meta.json"
    plot1.parent.mkdir()
    plot1.write_text(
        '{"category": "Category", "title": "P1", "case_date": "20250101", "plots": ["a.png"], "description": "Foo"}'
    )

    # Construct index.
    finish_website.construct_index(plots_dir.parent)

    # Check index.
    index_file = plots_dir / "index.jsonl"
    assert index_file.is_file()
    with open(index_file, "rt", encoding="UTF-8") as fp:
        index = json.loads(fp.readline())
    assert "plots" not in index
    assert "description" not in index


def test_construct_index_invalid(tmp_path, caplog):
    """Test constructing index when metadata is invalid."""
    plots_dir = tmp_path / "web/plots"
    plots_dir.mkdir(parents=True)

    # Plot directories.
    plot = plots_dir / "p1/meta.json"
    plot.parent.mkdir()
    plot.write_text('"Not JSON!"')

    # Construct index.
    finish_website.construct_index(plots_dir.parent)

    # Check log message.
    _, level, message = caplog.record_tuples[0]
    assert level == logging.ERROR
    assert "p1/meta.json is invalid, skipping." in message

    index_file = plots_dir / "index.jsonl"
    assert index_file.is_file()
    assert index_file.stat().st_size == 0


def test_entrypoint(monkeypatch):
    """Test running the finish_website module."""
    # Count the number of times the other functions are run, to ensure they
    # are all run.
    counter = 0

    def increment_counter(*args, **kwargs):
        nonlocal counter
        counter += 1

    def check_single_arg(www_content: Path):
        assert www_content == Path("/share/web")
        increment_counter()

    def check_args(www_root_link: Path, www_content: Path):
        assert www_root_link == Path("/var/www/cset")
        assert www_content == Path("/share/web")
        increment_counter()

    monkeypatch.setattr(finish_website, "install_website_skeleton", check_args)
    monkeypatch.setattr(finish_website, "copy_rose_config", check_single_arg)
    monkeypatch.setattr(finish_website, "construct_index", check_single_arg)
    monkeypatch.setattr(finish_website, "bust_cache", check_single_arg)
    monkeypatch.setattr(finish_website, "update_workflow_status", check_single_arg)
    monkeypatch.setenv("WEB_DIR", "/var/www/cset")
    monkeypatch.setenv("CYLC_WORKFLOW_SHARE_DIR", "/share")

    # Check that it runs all the needed subfunctions.
    finish_website.run()
    assert counter == 5
