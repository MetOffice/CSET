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

"""Tests for the command line interface.

In many ways these are integration tests.
"""

import os
import subprocess
import tempfile
from pathlib import Path
from uuid import uuid4

import pytest


def test_command_line_help():
    """Check that help commands work."""
    subprocess.run(["cset", "--help"], check=True)
    subprocess.run(["cset", "--version"], check=True)

    # Gain coverage of __main__.py
    subprocess.run(["python3", "-m", "CSET", "-h"], check=True)

    # Test verbose options. This is really just to up the coverage number.
    subprocess.run(["cset", "-v"])
    subprocess.run(["cset", "-vv"])


def test_recipe_execution():
    """Test running CSET recipe from the command line."""
    subprocess.run(
        [
            "cset",
            "bake",
            f"--input-dir={os.devnull}",
            f"--output-dir={tempfile.gettempdir()}",
            "--recipe=tests/test_data/noop_recipe.yaml",
        ],
        check=True,
    )


def test_graph_creation(tmp_path: Path):
    """Generates a graph with the command line interface."""
    # We can't easily test running without the output specified from the CLI, as
    # the call to xdg-open breaks in CI, due to it not being a graphical
    # environment.

    # Run with output path specified
    output_file = tmp_path / f"{uuid4()}.svg"
    subprocess.run(
        (
            "cset",
            "graph",
            "-o",
            str(output_file),
            "--recipe=tests/test_data/noop_recipe.yaml",
        ),
        check=True,
    )
    assert output_file.is_file()
    output_file.unlink()


def test_graph_details(tmp_path: Path):
    """Generate a graph with details with details."""
    output_file = tmp_path / f"{uuid4()}.svg"
    subprocess.run(
        (
            "cset",
            "graph",
            "--details",
            "-o",
            str(output_file),
            "--recipe=tests/test_data/noop_recipe.yaml",
        ),
        check=True,
    )
    assert output_file.is_file()


def test_cookbook_cwd(tmp_working_dir):
    """Unpacking the recipes into the current working directory."""
    subprocess.run(["cset", "cookbook"], check=True)
    assert Path("extract_instant_air_temp.yaml").is_file()


def test_cookbook_path(tmp_path: Path):
    """Unpacking the recipes into a specified directory."""
    subprocess.run(["cset", "cookbook", "--output-dir", tmp_path], check=True)
    assert (tmp_path / "extract_instant_air_temp.yaml").is_file()


def test_cookbook_list_available_recipes():
    """List all available recipes."""
    proc = subprocess.run(
        ["cset", "cookbook", "--list"], capture_output=True, check=True
    )
    assert proc.stdout.startswith(b"Available recipes:\n")


def test_cookbook_detail_recipe():
    """Show detail of a recipe."""
    proc = subprocess.run(
        ["cset", "cookbook", "--list", "extract_instant_air_temp"],
        capture_output=True,
        check=True,
    )
    assert proc.stdout.startswith(b"\n\textract_instant_air_temp\n")


def test_bake_invalid_args():
    """Invalid arguments give non-zero exit code."""
    with pytest.raises(subprocess.CalledProcessError):
        subprocess.run(
            [
                "cset",
                "bake",
                "--recipe=foo",
                "--input-dir=/tmp",
                "--output-dir=/tmp",
                "--not-a-real-option",
            ],
            check=True,
        )
