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

"""Tests for run_cset_recipe workflow utility."""

import os
import subprocess
import zipfile
from pathlib import Path

import pytest

from CSET._workflow_utils import run_cset_recipe


def test_subprocess_env():
    """Test subprocess_env function."""
    expected = dict(os.environ)
    actual = run_cset_recipe.subprocess_env()
    assert actual == expected


def test_recipe_file(monkeypatch, tmp_working_dir):
    """Bundled recipe file is written to disk."""
    monkeypatch.setenv("CSET_RECIPE_NAME", "CAPE_ratio_plot.yaml")
    recipe_path = run_cset_recipe.recipe_file()
    assert recipe_path == "CAPE_ratio_plot.yaml"
    assert Path(recipe_path).is_file()


def test_recipe_id(monkeypatch, tmp_working_dir):
    """Extract recipe ID from recipe file."""

    def mock_recipe_file():
        with open("recipe.yaml", "wt", encoding="UTF-8") as fp:
            fp.write("title: Recipe Title\nsteps: [{operator: misc.noop}]")
        return "recipe.yaml"

    monkeypatch.setenv("MODEL_NUMBER", "1")
    monkeypatch.setattr(run_cset_recipe, "recipe_file", mock_recipe_file)
    expected = "m1_recipe_title"
    actual = run_cset_recipe.recipe_id()
    assert actual == expected


def test_recipe_id_invalid_recipe(monkeypatch, tmp_working_dir):
    """Invalid recipe file raises exception."""

    def mock_recipe_file():
        with open("recipe.yaml", "wt", encoding="UTF-8") as fp:
            fp.write("Not a recipe!")
        return "recipe.yaml"

    monkeypatch.setenv("MODEL_NUMBER", "1")
    monkeypatch.setattr(run_cset_recipe, "recipe_file", mock_recipe_file)
    with pytest.raises(subprocess.CalledProcessError):
        run_cset_recipe.recipe_id()


def test_output_directory(monkeypatch):
    """Output directory correctly interpreted."""

    def mock_recipe_id():
        return "recipe_id"

    monkeypatch.setattr(run_cset_recipe, "recipe_id", mock_recipe_id)
    monkeypatch.setenv("CYLC_WORKFLOW_SHARE_DIR", "/share")
    monkeypatch.setenv("CYLC_TASK_CYCLE_POINT", "20000101T0000Z")
    actual = run_cset_recipe.output_directory()
    expected = "/share/web/plots/recipe_id_20000101T0000Z"
    assert actual == expected


def test_data_directory(monkeypatch):
    """Data directory correctly interpreted."""
    monkeypatch.setenv("CYLC_WORKFLOW_SHARE_DIR", "/share")
    monkeypatch.setenv("CYLC_TASK_CYCLE_POINT", "20000101T0000Z")
    monkeypatch.setenv("MODEL_NUMBER", "1")
    expected = "/share/cycle/20000101T0000Z/data/1"
    actual = run_cset_recipe.data_directory()
    assert actual == expected


def test_create_diagnostic_archive(tmp_path):
    """Create ZIP archive of output."""
    # Create dummy output files.
    files = {"one", "two", "three"}
    for filename in files:
        (tmp_path / filename).touch()

    run_cset_recipe.create_diagnostic_archive(tmp_path)
    archive_path = tmp_path / "diagnostic.zip"
    assert archive_path.is_file()
    with zipfile.ZipFile(archive_path, "r") as archive:
        # Check all files are now in archive.
        assert set(archive.namelist()) == files


def test_entrypoint(monkeypatch):
    """Check that run_cset_recipe.run() calls the correct function."""
    function_ran = False

    def assert_true():
        nonlocal function_ran
        function_ran = True

    monkeypatch.setattr(run_cset_recipe, "run_recipe_steps", assert_true)
    run_cset_recipe.run()
    assert function_ran, "Function did not run!"
