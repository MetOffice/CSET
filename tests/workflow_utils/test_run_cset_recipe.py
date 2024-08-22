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

import json
import os
import subprocess
import zipfile
from pathlib import Path

import pytest

from CSET._workflow_utils import run_cset_recipe


def test_combine_dicts():
    """Test combine_dicts function."""
    d1 = {"a": 1, "b": 2, "c": {"d": 3, "e": 4}}
    d2 = {"b": 3, "c": {"d": 5, "f": 6}}
    expected = {"a": 1, "b": 3, "c": {"d": 5, "e": 4, "f": 6}}
    assert run_cset_recipe.combine_dicts(d1, d2) == expected


def test_append_to_index(monkeypatch, tmp_path):
    """Test appending to index."""
    index_path = tmp_path / "web/plots/index.json"
    index_path.parent.mkdir(parents=True)
    monkeypatch.setenv("CYLC_WORKFLOW_SHARE_DIR", str(tmp_path))
    with open(index_path, "wt", encoding="UTF-8") as fp:
        json.dump(
            {
                "Category Name": {"recipe_id_a": "Title A"},
                "Other Category": {"recipe_id_b": "Title B"},
            },
            fp,
        )
    record = {"Category Name": {"recipe_id": "Plot Name"}}
    run_cset_recipe.append_to_index(record)
    expected = {
        "Category Name": {"recipe_id": "Plot Name", "recipe_id_a": "Title A"},
        "Other Category": {"recipe_id_b": "Title B"},
    }
    with open(index_path, "rt", encoding="UTF-8") as fp:
        assert json.load(fp) == expected


def test_append_to_index_missing(monkeypatch, tmp_path):
    """Test appending to index when index does not yet exist."""
    index_path = tmp_path / "web/plots/index.json"
    index_path.parent.mkdir(parents=True)
    monkeypatch.setenv("CYLC_WORKFLOW_SHARE_DIR", str(tmp_path))
    record = {"Category Name": {"recipe_id": "Plot Name"}}
    run_cset_recipe.append_to_index(record)
    with open(index_path, "rt", encoding="UTF-8") as fp:
        assert json.load(fp) == record


def test_append_to_index_invalid(monkeypatch, tmp_path):
    """Test appending to index when existing content is invalid."""
    index_path = tmp_path / "web/plots/index.json"
    index_path.parent.mkdir(parents=True)
    monkeypatch.setenv("CYLC_WORKFLOW_SHARE_DIR", str(tmp_path))
    with open(index_path, "wt", encoding="UTF-8") as fp:
        fp.write("Not JSON!")
    record = {"Category Name": {"recipe_id": "Plot Name"}}
    run_cset_recipe.append_to_index(record)
    with open(index_path, "rt", encoding="UTF-8") as fp:
        assert json.load(fp) == record


def test_subprocess_env(monkeypatch):
    """Test subprocess_env function."""
    monkeypatch.setenv("CYLC_TASK_CYCLE_POINT", "2000-01-01T00:00:00Z")
    monkeypatch.setenv("CSET_ADDOPTS", "--other-opts")
    expected = {
        "CYLC_TASK_CYCLE_POINT": "2000-01-01T00:00:00Z",
        "CSET_ADDOPTS": "--other-opts --VALIDITY_TIME=2000-01-01T00:00:00Z",
    }
    actual = run_cset_recipe.subprocess_env()
    for expected_item in expected.items():
        assert expected_item in actual.items()


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
            fp.write("title: Recipe Title\nparallel: [{operator: misc.noop}]")
        return "recipe.yaml"

    def mock_subprocess_env():
        return os.environ

    monkeypatch.setattr(run_cset_recipe, "recipe_file", mock_recipe_file)
    monkeypatch.setattr(run_cset_recipe, "subprocess_env", mock_subprocess_env)
    expected = "recipe_title"
    actual = run_cset_recipe.recipe_id()
    assert actual == expected


def test_recipe_id_invalid_recipe(monkeypatch, tmp_working_dir):
    """Invalid recipe file raises exception."""

    def mock_recipe_file():
        with open("recipe.yaml", "wt", encoding="UTF-8") as fp:
            fp.write("Not a recipe!")
        return "recipe.yaml"

    def mock_subprocess_env():
        return os.environ

    monkeypatch.setattr(run_cset_recipe, "recipe_file", mock_recipe_file)
    monkeypatch.setattr(run_cset_recipe, "subprocess_env", mock_subprocess_env)
    with pytest.raises(subprocess.CalledProcessError):
        run_cset_recipe.recipe_id()


def test_output_directory(monkeypatch):
    """Output directory correctly interpreted."""

    def mock_recipe_id():
        return "recipe_id"

    monkeypatch.setattr(run_cset_recipe, "recipe_id", mock_recipe_id)
    monkeypatch.setenv("CYLC_WORKFLOW_SHARE_DIR", "/share")
    actual = run_cset_recipe.output_directory()
    expected = "/share/web/plots/recipe_id"
    assert actual == expected


def test_data_directory(monkeypatch):
    """Data directory correctly interpreted."""
    monkeypatch.setenv("CYLC_WORKFLOW_SHARE_DIR", "/share")
    monkeypatch.setenv("CYLC_TASK_CYCLE_POINT", "20000101T0000Z")
    expected = "/share/cycle/20000101T0000Z/data"
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


def test_entrypoint_parallel(monkeypatch):
    """Check entrypoint for parallel job."""

    def assert_true():
        assert True

    def assert_false():
        assert False, "collate() during parallel job."  # noqa: B011

    monkeypatch.setenv("CSET_BAKE_MODE", "parallel")
    monkeypatch.setattr(run_cset_recipe, "parallel", assert_true)
    monkeypatch.setattr(run_cset_recipe, "collate", assert_false)

    run_cset_recipe.run()


def test_entrypoint_collate(monkeypatch):
    """Check entrypoint for collate job."""

    def assert_true():
        assert True

    def assert_false():
        assert False, "parallel() during collate job."  # noqa: B011

    monkeypatch.setenv("CSET_BAKE_MODE", "collate")
    monkeypatch.setattr(run_cset_recipe, "parallel", assert_false)
    monkeypatch.setattr(run_cset_recipe, "collate", assert_true)

    run_cset_recipe.run()


def test_entrypoint_neither(monkeypatch):
    """Entrypoint does nothing for a noop job."""

    def assert_false():
        assert False, "unwanted processing."  # noqa: B011

    monkeypatch.setenv("CSET_BAKE_MODE", "")
    monkeypatch.setattr(run_cset_recipe, "parallel", assert_false)
    monkeypatch.setattr(run_cset_recipe, "collate", assert_false)

    run_cset_recipe.run()
