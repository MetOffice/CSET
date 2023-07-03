# Copyright 2022 Met Office and contributors.
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

from pathlib import Path
import subprocess
import tempfile
from uuid import uuid4

import CSET.graph


def test_save_graph():
    """Directly tests generating a graph from a recipe file."""
    CSET.graph.save_graph(Path("tests/test_data/plot_instant_air_temp.yaml"))


def test_cli_interface():
    """Generates a graph with the command line interface"""
    # Run with output path specified
    output_file = Path(tempfile.gettempdir(), f"{uuid4()}.svg")
    subprocess.run(
        ("cset", "graph", "-o", str(output_file), "tests/test_data/noop_recipe.yaml"),
        check=True,
    )
    assert output_file.exists()
    output_file.unlink()

    # Run with details and no output specified
    subprocess.run(
        ("cset", "graph", "--detailed", "tests/test_data/noop_recipe.yaml"), check=True
    )
