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
import CSET.extract_workflow
import CSET.workflow


def test_command_line_invocation():
    """Check invocation via different entrypoints.

    Uses subprocess to validate the external interface. Every other test should
    not use the command line interface, but rather stay within python to ensure
    coverage measurement.
    """
    # Invoke via cset command
    subprocess.run(["cset", "--version"], check=True)
    # Invoke via __main__.py
    subprocess.run(["python3", "-m", "CSET", "--version"], check=True)


def test_argument_parser_graph(tmp_path):
    """Tests the cset graph argument parser behaves appropriately."""
    parser = CSET.setup_argument_parser()
    args = parser.parse_args(["graph", "-r", "recipe.yaml", "-o", str(tmp_path)])
    assert args.recipe == Path("recipe.yaml")
    assert args.output_path == tmp_path
    assert args.verbose == 0
    # Test verbose flag.
    args = parser.parse_args(["-v", "graph", "-r", "recipe.yaml", "-o", str(tmp_path)])
    assert args.verbose == 1
    args = parser.parse_args(["-vv", "graph", "-r", "recipe.yaml", "-o", str(tmp_path)])
    assert args.verbose == 2


def test_argument_parser_bake(tmp_path):
    """Tests the cset bake argument parser behaves appropriately."""
    parser = CSET.setup_argument_parser()
    # Check required arguments.
    args = parser.parse_args(
        ["bake", "--recipe", "recipe.yaml", "--output-dir", str(tmp_path)]
    )
    assert args.recipe == Path("recipe.yaml")
    assert args.output_dir == tmp_path
    # Check optional arguments.
    args = parser.parse_args(
        [
            "bake",
            "-r",
            "recipe.yaml",
            "-o",
            str(tmp_path),
            "-i",
            str(tmp_path),
            "-s",
            str(tmp_path / "style.json"),
            "--plot-resolution",
            "72",
            "--skip-write",
        ]
    )
    assert args.input_dir == [str(tmp_path)]
    assert args.style_file == tmp_path / "style.json"
    assert args.plot_resolution == 72
    assert args.skip_write is True


def test_argument_parser_cookbook(tmp_path):
    """Tests the cset cookbook argument parser behaves appropriately."""
    parser = CSET.setup_argument_parser()
    # Check default values.
    args = parser.parse_args(["cookbook"])
    assert args.recipe == ""
    assert args.output_dir == Path.cwd()
    # Check optional arguments.
    args = parser.parse_args(["cookbook", "-d", "-o", str(tmp_path), "recipe.yaml"])
    assert args.details is True
    assert args.output_dir == tmp_path
    assert args.recipe == "recipe.yaml"


def test_argument_parser_extract_workflow(tmp_path):
    """Tests the cset extract-workflow argument parser behaves appropriately."""
    parser = CSET.setup_argument_parser()
    # Check required argument.
    args = parser.parse_args(["extract-workflow", str(tmp_path)])
    assert args.location == tmp_path


def test_setup_logging():
    """Tests the logging setup at various verbosity levels."""
    root_logger = logging.getLogger()
    # Log has a minimum of WARNING.
    CSET.setup_logging(0)
    assert root_logger.level == logging.WARNING
    # -v
    CSET.setup_logging(1)
    assert root_logger.level == logging.INFO
    # -vv
    CSET.setup_logging(2)
    assert root_logger.level == logging.DEBUG


def test_setup_logging_mpl_font_logs_filtered(caplog):
    """Test matplotlib log messages about fonts are filtered out."""
    CSET.setup_logging(2)
    logger = logging.getLogger("matplotlib.font_manager")
    logger.debug("findfont: message")
    logger.debug("other message")
    assert len(caplog.records) == 1
    assert caplog.records[0].getMessage() == "other message"


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


def test_bake_INPUT_PATHS_conversion(monkeypatch):
    """--input-dir argument is converted to --INPUT_PATHS recipe variable."""

    def check_vars(*args, **kwargs):
        assert "INPUT_PATHS" in args[2]
        p = str(Path("foo").absolute())
        assert args[2]["INPUT_PATHS"] in (p, [p])

    monkeypatch.setattr(CSET.operators, "execute_recipe", check_vars)

    class args:
        recipe = "recipe.yaml"
        input_dir = "foo"
        output_dir = Path("/dev/null")
        style_file = None
        plot_resolution = None
        skip_write = None

    # Check --input-dir is converted.
    unparsed_args = []
    CSET._bake_command(args, unparsed_args)
    # Check --INPUT_PATHS is directly used.
    args.input_dir = None
    unparsed_args = ["--INPUT_PATHS", str(Path("foo").absolute())]
    CSET._bake_command(args, unparsed_args)


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


def test_extract_workflow_command(monkeypatch, tmp_path):
    """Extract workflow command correctly calls install_workflow function."""
    ran = False

    def dummy_install_workflow(location: Path):
        nonlocal ran
        ran = True
        assert location == tmp_path

    monkeypatch.setattr(
        CSET.extract_workflow, "install_workflow", dummy_install_workflow
    )
    CSET.main(["cset", "extract-workflow", str(tmp_path)])
    assert ran
