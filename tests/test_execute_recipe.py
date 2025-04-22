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

"""Tests for running CSET operator recipes."""

import json
import zipfile
from pathlib import Path

import pytest

import CSET.operators


def test_get_operator():
    """Happy case."""
    read_operator = CSET.operators.get_operator("read.read_cubes")
    assert callable(read_operator)


def test_get_operator_exception_missing():
    """Test exception for non-existent operators."""
    with pytest.raises(ValueError):
        CSET.operators.get_operator("non-existent.operator")


def test_get_operator_exception_type():
    """Test exception if wrong type provided."""
    with pytest.raises(ValueError):
        CSET.operators.get_operator(["Not", b"a", "string", 1])


def test_get_operator_exception_not_callable():
    """Test exception if operator isn't a function."""
    with pytest.raises(ValueError):
        CSET.operators.get_operator("misc.__doc__")


def test_execute_recipe(tmp_path: Path):
    """Execute recipe to test happy case (this is really an integration test)."""
    variables = {"INPUT_PATHS": str(Path.cwd() / "tests/test_data/air_temp.nc")}
    recipe = Path("tests/test_data/plot_instant_air_temp.yaml")
    CSET.operators.execute_recipe(recipe, tmp_path, recipe_variables=variables)


def test_execute_recipe_edge_cases(tmp_path: Path):
    """Test weird edge cases. Also tests data paths not being pathlib Paths."""
    variables = {"INPUT_PATHS": str(Path.cwd() / "tests/test_data/air_temp.nc")}
    recipe = Path("tests/test_data/noop_recipe.yaml")
    CSET.operators.execute_recipe(recipe, tmp_path, recipe_variables=variables)


def test_execute_recipe_invalid_output_dir(tmp_path: Path):
    """Exception raised if output directory can't be created."""
    variables = {"INPUT_PATHS": str(Path.cwd() / "tests/test_data/air_temp.nc")}
    recipe = '{"steps":[{"operator": misc.noop}]}'
    output_dir = tmp_path / "actually_a_file"
    output_dir.touch()
    with pytest.raises((FileExistsError, NotADirectoryError)):
        CSET.operators.execute_recipe(recipe, output_dir, recipe_variables=variables)


def test_execute_recipe_style_file_metadata_written(tmp_path: Path):
    """Style file path metadata written out."""
    style_file_path = "/test/style_file_path.json"
    CSET.operators.execute_recipe(
        '{"steps":[{"operator": misc.noop}]}',
        tmp_path,
        style_file=Path(style_file_path),
    )
    with open(tmp_path / "meta.json", "rb") as fp:
        metadata = json.load(fp)
    assert metadata["style_file_path"] == style_file_path


def test_execute_recipe_plot_resolution_metadata_written(tmp_path: Path):
    """Style file path metadata written out."""
    CSET.operators.execute_recipe(
        '{"steps":[{"operator": misc.noop}]}', tmp_path, plot_resolution=72
    )
    with open(tmp_path / "meta.json", "rb") as fp:
        metadata = json.load(fp)
    assert metadata["plot_resolution"] == 72


def test_execute_recipe_skip_write_metadata_written(tmp_path: Path):
    """Skip write metadata written out."""
    CSET.operators.execute_recipe(
        '{"steps":[{"operator": misc.noop}]}', tmp_path, skip_write=True
    )
    with open(tmp_path / "meta.json", "rb") as fp:
        metadata = json.load(fp)
    assert metadata["skip_write"]


def test_create_diagnostic_archive(tmp_path):
    """Create ZIP archive of output."""
    # Create dummy output files.
    files = {"one", "two", "three"}
    for filename in files:
        (tmp_path / filename).touch()

    CSET.operators.create_diagnostic_archive(tmp_path)
    archive_path = tmp_path / "diagnostic.zip"
    assert archive_path.is_file()
    with zipfile.ZipFile(archive_path, "r") as archive:
        # Check all files are now in archive.
        assert set(archive.namelist()) == files
