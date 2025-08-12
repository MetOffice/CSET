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

"""Recipe tests."""

import logging
from pathlib import Path

import pytest

from CSET import recipes


def test_recipe_files_in_tree():
    """Get recipes in directory containing sub-directories."""
    files = recipes._recipe_files_in_tree(input_dir=Path("tests"))
    assert Path("tests/test_data/noop_recipe.yaml") in files


def test_recipe_files_in_tree_from_package():
    """Get a recipe from inside the CSET package."""
    files = recipes._recipe_files_in_tree()
    assert any("CAPE_ratio_plot.yaml" == path.name for path in files)


def test_unpack_recipes(tmp_path: Path, caplog):
    """Unpack a recipe and check a log message is produced when files collide."""
    recipes.unpack_recipe(tmp_path, "CAPE_ratio_plot.yaml")
    assert (tmp_path / "CAPE_ratio_plot.yaml").is_file()
    with caplog.at_level("INFO"):
        recipes.unpack_recipe(tmp_path, "CAPE_ratio_plot.yaml")
    # Filter out unrelated log messages in case we are testing in parallel.
    _, level, message = next(
        filter(lambda r: "already exists" in r[2], caplog.record_tuples)
    )
    assert level == logging.INFO
    assert (
        message == "CAPE_ratio_plot.yaml already exists in target directory, skipping."
    )


def test_unpack_recipes_exception_collision(tmp_path: Path):
    """Output path already exists and is not a directory."""
    file_path = tmp_path / "regular_file"
    file_path.touch()
    with pytest.raises(FileExistsError):
        recipes.unpack_recipe(file_path, "CAPE_ratio_plot.yaml")


def test_unpack_recipes_exception_permission():
    """Insufficient permission to create output directory.

    Will fail if tests are run as root, but no one should do that, right?
    """
    with pytest.raises(OSError):
        recipes.unpack_recipe(Path("/usr/bin/cset"), "extract_instant_air_temp.yaml")


def test_get_recipe_file():
    """Get a recipe file from a specific location."""
    file = recipes._get_recipe_file("noop_recipe.yaml", Path("tests/test_data"))
    assert file.is_file()


def test_get_recipe_file_missing():
    """Exception raised when recipe file not in location."""
    with pytest.raises(FileNotFoundError):
        recipes._get_recipe_file("non-existent", Path("tests/test_data"))


def test_get_recipe_file_in_package():
    """Get a recipe file from the default location inside the package."""
    file = recipes._get_recipe_file("CAPE_ratio_plot.yaml")
    assert file.is_file()


def test_list_available_recipes(capsys):
    """Display available recipes."""
    recipes.list_available_recipes()
    # Read stdout and stderr.
    captured_output = capsys.readouterr()
    # Check start.
    assert captured_output.out.startswith("Available recipes:\n")
    # Check has some recipes.
    assert len(captured_output.out.splitlines()) > 3


def test_detail_recipe(capsys):
    """Show detail of a recipe."""
    recipes.detail_recipe("CAPE_ratio_plot.yaml")
    # Read stdout and stderr.
    captured_output = capsys.readouterr()
    assert captured_output.out.startswith("\n\tCAPE_ratio_plot.yaml\n")
