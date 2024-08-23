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

"""Tests for the command line interface.

In many ways these are integration tests.
"""

import os
import subprocess
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


def test_bake_recipe_execution(tmp_path):
    """Test running CSET recipe from the command line."""
    subprocess.run(
        [
            "cset",
            "bake",
            f"--input-dir={os.devnull}",
            f"--output-dir={tmp_path}",
            "--recipe=tests/test_data/noop_recipe.yaml",
        ],
        check=True,
    )


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


def test_bake_invalid_args_input_dir():
    """Missing required input-dir argument for parallel."""
    with pytest.raises(subprocess.CalledProcessError):
        subprocess.run(
            ["cset", "bake", "--recipe=foo", "--output-dir=/tmp"], check=True
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
    subprocess.run(["cset", "cookbook", "CAPE_ratio_plot.yaml"], check=True)
    assert Path("CAPE_ratio_plot.yaml").is_file()


def test_cookbook_path(tmp_path: Path):
    """Unpacking the recipes into a specified directory."""
    subprocess.run(
        ["cset", "cookbook", "--output-dir", tmp_path, "CAPE_ratio_plot.yaml"],
        check=True,
    )
    assert (tmp_path / "CAPE_ratio_plot.yaml").is_file()


def test_cookbook_list_available_recipes():
    """List all available recipes."""
    proc = subprocess.run(
        ["cset", "cookbook", "--details"], capture_output=True, check=True
    )
    # Check start.
    assert proc.stdout.startswith(b"Available recipes:\n")
    # Check has some recipes.
    assert len(proc.stdout.splitlines()) > 3


def test_cookbook_detail_recipe():
    """Show detail of a recipe."""
    proc = subprocess.run(
        [
            "cset",
            "cookbook",
            "--details",
            "CAPE_ratio_plot.yaml",
        ],
        capture_output=True,
        check=True,
    )
    assert proc.stdout.startswith(b"\n\tCAPE_ratio_plot.yaml\n")


def test_cookbook_non_existent_recipe(tmp_path):
    """Non-existent recipe give non-zero exit code."""
    with pytest.raises(subprocess.CalledProcessError):
        subprocess.run(
            ["cset", "cookbook", "--output-dir", tmp_path, "non-existent.yaml"],
            check=True,
        )


def test_recipe_id():
    """Get recipe ID for a recipe."""
    p = subprocess.run(
        ["cset", "recipe-id", "-r", "tests/test_data/noop_recipe.yaml"],
        check=True,
        capture_output=True,
    )
    assert p.stdout == b"noop\n"


def test_recipe_id_no_title():
    """Get recipe id for recipe without a title."""
    p = subprocess.run(
        ["cset", "recipe-id", "-r", "tests/test_data/ensemble_air_temp.yaml"],
        check=True,
        capture_output=True,
    )
    # UUID output + newline.
    assert len(p.stdout) == 37


def test_cset_addopts():
    """Lists in CSET_ADDOPTS environment variable don't crash the parser."""
    environment = dict(os.environ)
    environment["CSET_ADDOPTS"] = "--LIST='[1, 2, 3]'"
    p = subprocess.run(
        ["cset", "recipe-id", "-r", "tests/test_data/addopts_test_recipe.yaml"],
        check=True,
        capture_output=True,
        env=environment,
    )
    assert p.stdout == b"list_1_2_3\n"
