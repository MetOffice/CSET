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

"""Tests for running CSET operator recipes."""

import json
from pathlib import Path
from uuid import uuid4

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


def test_execute_recipe_parallel(tmp_path: Path):
    """Execute recipe to test happy case (this is really an integration test)."""
    input_file = Path("tests/test_data/air_temp.nc")
    output_dir = tmp_path / f"{uuid4()}"
    recipe_file = Path("tests/test_data/plot_instant_air_temp.yaml")
    CSET.operators.execute_recipe_parallel(recipe_file, input_file, output_dir)


def test_execute_recipe_parallel_edge_cases(tmp_path: Path):
    """Test weird edge cases. Also tests data paths not being pathlib Paths."""
    input_file = "tests/test_data/air_temp.nc"
    output_dir = tmp_path / f"{uuid4()}"
    recipe = Path("tests/test_data/noop_recipe.yaml")
    CSET.operators.execute_recipe_parallel(recipe, input_file, output_dir)


def test_execute_recipe_parallel_invalid_output_dir(tmp_path: Path):
    """Exception raised if output directory can't be created."""
    recipe = '{"parallel":[{"operator": misc.noop}]}'
    input_file = Path("tests/test_data/air_temp.nc")
    output_dir = tmp_path / "actually_a_file"
    output_dir.touch()
    with pytest.raises((FileExistsError, NotADirectoryError)):
        CSET.operators.execute_recipe_parallel(recipe, input_file, output_dir)


def test_execute_recipe_collate(tmp_path: Path):
    """Execute collate from a recipe."""
    output_dir = tmp_path
    recipe_file = Path("tests/test_data/noop_recipe.yaml")
    CSET.operators.execute_recipe_collate(recipe_file, output_dir)


def test_execute_recipe_collate_no_steps(tmp_path: Path):
    """Execute collate for a recipe without any collate steps."""
    recipe = '{"parallel":[{"operator": misc.noop}]}'
    output_dir = tmp_path
    CSET.operators.execute_recipe_collate(recipe, output_dir)


def test_run_steps_style_file_metadata_written(tmp_path: Path):
    """Style file path metadata written out."""
    style_file_path = "/test/style_file_path.json"
    CSET.operators._run_steps({}, [], None, tmp_path, Path(style_file_path))
    with open(tmp_path / "meta.json", "rb") as fp:
        metadata = json.load(fp)
    assert metadata["style_file_path"] == style_file_path
