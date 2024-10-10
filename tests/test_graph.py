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

"""Graph tests."""

import os
import stat
from pathlib import Path

import pytest

from CSET import graph


def test_save_graph():
    """Generate a graph from a recipe file without the output specified."""
    graph.save_graph(Path("tests/test_data/plot_instant_air_temp.yaml"))


def test_save_graph_detailed(tmp_path: Path):
    """Generate a graph from a recipe file with the output specified."""
    graph.save_graph(
        Path("tests/test_data/plot_instant_air_temp.yaml"),
        tmp_path / "graph.svg",
        detailed=True,
    )


def test_save_graph_no_operators_exception():
    """Exception raised from recipe with no operators in its steps."""
    with pytest.raises(ValueError):
        # Inline YAML form used.
        graph.save_graph('{"steps": [{"argument": "no_operators"}]}')


def test_save_graph_no_steps_exception():
    """Exception raised from recipe with no steps."""
    with pytest.raises(ValueError):
        graph.save_graph("title: Recipe with no steps")


def test_save_graph_auto_open_xdg_open(tmp_path: Path, monkeypatch):
    """Test the auto-opening of the graph with (a mocked) xdg-open."""
    xdg_open = tmp_path / "xdg-open"
    with open(xdg_open, "wt", encoding="UTF-8") as fp:
        fp.write("#!/bin/bash\ntrue")
    xdg_open.chmod(stat.S_IRUSR | stat.S_IXUSR)
    monkeypatch.setenv("PATH", str(tmp_path), prepend=os.pathsep)
    graph.save_graph(Path("tests/test_data/plot_instant_air_temp.yaml"), auto_open=True)


def test_save_graph_auto_open_no_xdg_open(tmp_path: Path, monkeypatch):
    """Test the auto-opening of the graph errors without xdg-open.

    Strictly speaking this tests xdg-open failing, but it is equivalent to it
    missing.
    """
    xdg_open = tmp_path / "xdg-open"
    with open(xdg_open, "wt", encoding="UTF-8") as fp:
        fp.write("#!/bin/bash\nfalse")
    xdg_open.chmod(stat.S_IRUSR | stat.S_IXUSR)
    monkeypatch.setenv("PATH", str(tmp_path), prepend=os.pathsep)
    graph.save_graph(Path("tests/test_data/plot_instant_air_temp.yaml"), auto_open=True)
