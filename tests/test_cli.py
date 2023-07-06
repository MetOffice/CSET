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

"""
Tests for the command line interface. In many ways these are integration tests.
"""

from pathlib import Path
from uuid import uuid4
import os
import subprocess
import tempfile


def test_command_line_help():
    subprocess.run(["cset", "--help"])
    # test verbose options. This is really just to up the coverage number.
    subprocess.run(["cset", "-v"])
    subprocess.run(["cset", "-vv"])
    # Gain coverage of __main__.py
    subprocess.run(["python3", "-m", "CSET", "-h"])


def test_recipe_execution():
    subprocess.run(
        [
            "cset",
            "run",
            os.devnull,
            os.devnull,
            "test/test_data/noop_recipe.yaml",
        ]
    )


def test_environ_var_recipe():
    """Test recipe coming from environment variable."""
    os.environ[
        "CSET_RECIPE"
    ] = """
        steps:
          - operator: misc.noop
        """
    subprocess.run(
        [
            "cset",
            "run",
            os.devnull,
            os.devnull,
        ]
    )


def test_graph_creation():
    """Generates a graph with the command line interface."""

    # We can't easily test running without the output specified from the CLI, as
    # the call to xdg-open breaks in CI, due to it not being a graphical
    # environment.

    # Run with output path specified
    output_file = Path(tempfile.gettempdir(), f"{uuid4()}.svg")
    subprocess.run(
        ("cset", "graph", "-o", str(output_file), "tests/test_data/noop_recipe.yaml"),
        check=True,
    )
    assert output_file.exists()
    output_file.unlink()


def test_graph_details():
    """Generate a graph with details with details."""
    output_file = Path(tempfile.gettempdir(), f"{uuid4()}.svg")
    subprocess.run(
        (
            "cset",
            "graph",
            "--detailed",
            "-o",
            str(output_file),
            "tests/test_data/noop_recipe.yaml",
        ),
        check=True,
    )
    assert output_file.exists()
    output_file.unlink()


# def test_cookbook_cwd():
#     """Unpacking the recipes into the current working directory."""
#     old_cwd = Path.cwd()
#     with tempfile.TemporaryDirectory() as tmpdir:
#         os.chdir(tmpdir)
#         subprocess.run(["cset", "cookbook"], check=True)
#         assert Path.cwd().joinpath("recipes/extract_instant_air_temp.yaml").exists()
#         os.chdir(old_cwd)


def test_cookbook_path():
    """Unpacking the recipes into a specified directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        subprocess.run(["cset", "cookbook", tmpdir], check=True)
        assert Path(tmpdir, "extract_instant_air_temp.yaml").exists()
