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

import logging
import subprocess
from pathlib import Path
from uuid import uuid4

import pytest

import CSET
import CSET.operators


def test_command_line_invocation():
    """Check invocation via different entrypoints.

    Uses subprocess to validate the external interface.
    """
    # Invoke via cset command
    subprocess.run(["cset", "--version"], check=True)
    # Invoke via __main__.py
    subprocess.run(["python3", "-m", "CSET", "--version"], check=True)


# Every other test should not use the command line interface, but rather stay
# within python to ensure coverage measurement.
def test_argument_parser():
    """Tests the argument parser behaves appropriately."""
    parser = CSET.setup_argument_parser()
    # Test verbose flag.
    args = parser.parse_args(["recipe-id", "-r", "recipe.yaml"])
    assert args.verbose == 0
    args = parser.parse_args(["-v", "recipe-id", "-r", "recipe.yaml"])
    assert args.verbose == 1
    args = parser.parse_args(["-vv", "recipe-id", "-r", "recipe.yaml"])
    assert args.verbose == 2


def test_setup_logging():
    """Tests the logging setup at various verbosity levels."""
    root_logger = logging.getLogger()
    # Log level gets pinned at a minimum of INFO for file output.
    CSET.setup_logging(0)
    assert root_logger.level == logging.INFO
    # -v
    CSET.setup_logging(1)
    assert root_logger.level == logging.INFO
    # -vv
    CSET.setup_logging(2)
    assert root_logger.level == logging.DEBUG


def test_main_no_subparser(capsys):
    """Appropriate error when no subparser is given."""
    with pytest.raises(SystemExit) as sysexit:
        CSET.main(["cset"])
    assert sysexit.value.code == 127
    assert capsys.readouterr().err == "Please choose a command.\n"


def test_main_unhandled_exception_normal(capsys):
    """Appropriate error when an unhandled exception occurs."""
    with pytest.raises(SystemExit) as sysexit:
        CSET.main(
            [
                "cset",
                "bake",
                "--recipe=/non-existent/recipe.yaml",
                "--input-dir=/dev/null",
                "--output-dir=/dev/null",
            ]
        )
    assert sysexit.value.code == 1
    assert (
        capsys.readouterr().err
        == "[Errno 2] No such file or directory: '/non-existent/recipe.yaml'\n"
    )


def test_main_unhandled_exception_debug(caplog, capsys):
    """Appropriate error when an unhandled exception occurs under debug mode."""
    with pytest.raises(FileNotFoundError):
        CSET.main(
            [
                "cset",
                "-vv",
                "bake",
                "--recipe=/non-existent/recipe.yaml",
                "--input-dir=/dev/null",
                "--output-dir=/dev/null",
            ]
        )
    assert (
        "[Errno 2] No such file or directory: '/non-existent/recipe.yaml'\n"
        in capsys.readouterr().err
    )
    log_record = caplog.records[-1]
    assert log_record.message == "An unhandled exception occurred."
    assert log_record.levelno == logging.DEBUG


def test_bake_recipe_execution(monkeypatch):
    """Test running CSET recipe from the command line."""
    bake_ran = False

    def _bake_test(args, unparsed_args):
        nonlocal bake_ran
        bake_ran = True
        assert args.input_dir == ["/dev/null"]
        assert args.output_dir == Path("/dev/null")
        assert args.recipe == Path("tests/test_data/noop_recipe.yaml")

    monkeypatch.setattr(CSET, "_bake_command", _bake_test)
    CSET.main(
        [
            "cset",
            "bake",
            "--input-dir=/dev/null",
            "--output-dir=/dev/null",
            "--recipe=tests/test_data/noop_recipe.yaml",
        ]
    )


def test_bake_invalid_args(capsys):
    """Invalid arguments give non-zero exit code."""
    with pytest.raises(SystemExit) as sysexit:
        CSET.main(
            [
                "cset",
                "bake",
                "--recipe=foo",
                "--input-dir=/tmp",
                "--output-dir=/tmp",
                "--not-a-real-option",
            ]
        )
    assert sysexit.value.code == 127
    assert capsys.readouterr().err == "Unknown argument: --not-a-real-option\n"


def test_bake_invalid_args_input_dir(capsys):
    """Missing required input-dir argument for bake."""
    with pytest.raises(SystemExit) as sysexit:
        CSET.main(["cset", "bake", "--recipe=foo", "--output-dir=/tmp"])
    assert sysexit.value.code == 2
    assert capsys.readouterr().err.endswith(
        "cset bake: error: the following arguments are required: -i/--input-dir\n"
    )


def test_graph_creation(tmp_path: Path):
    """Generates a graph with the command line interface."""
    # We can't easily test running without the output specified from the CLI, as
    # the call to xdg-open breaks in CI, due to it not being a graphical
    # environment.

    # Run with output path specified
    output_file = tmp_path / f"{uuid4()}.svg"
    CSET.main(
        [
            "cset",
            "graph",
            "-o",
            str(output_file),
            "--recipe=tests/test_data/noop_recipe.yaml",
        ]
    )
    assert output_file.is_file()
    output_file.unlink()


def test_graph_details(tmp_path: Path):
    """Generate a graph with details."""
    output_file = tmp_path / f"{uuid4()}.svg"
    CSET.main(
        [
            "cset",
            "graph",
            "--details",
            "-o",
            str(output_file),
            "--recipe=tests/test_data/noop_recipe.yaml",
        ]
    )
    assert output_file.is_file()


def test_cookbook_cwd(tmp_working_dir):
    """Unpacking the recipes into the current working directory."""
    CSET.main(["cset", "cookbook", "CAPE_ratio_plot.yaml"])
    assert Path("CAPE_ratio_plot.yaml").is_file()


def test_cookbook_path(tmp_path: Path):
    """Unpacking the recipes into a specified directory."""
    CSET.main(
        ["cset", "cookbook", "--output-dir", str(tmp_path), "CAPE_ratio_plot.yaml"]
    )
    assert (tmp_path / "CAPE_ratio_plot.yaml").is_file()


def test_cookbook_list_available_recipes(capsys):
    """List all available recipes."""
    CSET.main(["cset", "cookbook", "--details"])
    stdout = capsys.readouterr().out
    # Check start.
    assert stdout.startswith("Available recipes:\n")
    # Check has some recipes.
    assert len(stdout.splitlines()) > 3


def test_cookbook_detail_recipe(capsys):
    """Show detail of a recipe."""
    CSET.main(["cset", "cookbook", "--details", "CAPE_ratio_plot.yaml"])
    assert capsys.readouterr().out.startswith("\n\tCAPE_ratio_plot.yaml\n")


def test_cookbook_non_existent_recipe(tmp_path):
    """Non-existent recipe give non-zero exit code."""
    with pytest.raises(SystemExit) as sysexit:
        CSET.main(
            ["cset", "cookbook", "--output-dir", str(tmp_path), "non-existent.yaml"]
        )
    assert sysexit.value.code == 1


def test_recipe_id(capsys):
    """Get recipe ID for a recipe."""
    CSET.main(["cset", "recipe-id", "-r", "tests/test_data/noop_recipe.yaml"])
    assert capsys.readouterr().out == "noop\n"


def test_recipe_id_no_title(capsys):
    """Get recipe id for recipe without a title."""
    CSET.main(["cset", "recipe-id", "-r", "tests/test_data/ensemble_air_temp.yaml"])
    # UUID output + newline.
    assert len(capsys.readouterr().out) == 37


def test_cset_addopts(capsys, monkeypatch):
    """Lists in CSET_ADDOPTS environment variable don't crash the parser."""
    monkeypatch.setenv("CSET_ADDOPTS", "--LIST='[1, 2, 3]'")
    CSET.main(["cset", "recipe-id", "-r", "tests/test_data/addopts_test_recipe.yaml"])
    assert capsys.readouterr().out == "list_1_2_3\n"
