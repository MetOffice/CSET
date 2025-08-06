# © Crown copyright, Met Office (2022-2025) and CSET contributors.
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

"""Tests for parbake_recipe workflow utility."""

import subprocess
from pathlib import Path

import pytest


def test_recipe_file(monkeypatch, tmp_working_dir):
    """Bundled recipe file is written to disk."""
    monkeypatch.setenv("CSET_RECIPE_NAME", "CAPE_ratio_plot.yaml")
    recipe_path = parbake_recipe.recipe_file()
    assert recipe_path == "CAPE_ratio_plot.yaml"
    assert Path(recipe_path).is_file()


def test_data_directories(monkeypatch):
    """Data directory correctly interpreted."""
    monkeypatch.setenv("ROSE_DATAC", "/share/cycle/20000101T0000Z")
    monkeypatch.setenv("MODEL_IDENTIFIERS", "1")
    expected = ["/share/cycle/20000101T0000Z/data/1"]
    actual = parbake_recipe.data_directories(case_aggregation=False)
    assert actual == expected


def test_data_directories_multiple_cases(monkeypatch):
    """Data directory correctly interpreted for multiple cases."""
    monkeypatch.setenv("CYLC_WORKFLOW_SHARE_DIR", "/share")
    monkeypatch.setenv("MODEL_IDENTIFIERS", "1")
    expected = ["/share/cycle/*/data/1"]
    actual = parbake_recipe.data_directories(case_aggregation=True)
    assert actual == expected


def test_entrypoint(monkeypatch):
    """Check that parbake_recipe.run() calls the correct function."""
    function_ran = False

    def assert_true():
        nonlocal function_ran
        function_ran = True

    monkeypatch.setattr(parbake_recipe, "run_parbake", assert_true)
    parbake_recipe.run()
    assert function_ran, "Function did not run!"


def test_entrypoint_exit_on_subprocess_exception(monkeypatch):
    """Check that parbake_recipe.run() exits non-zero."""

    def subprocess_error():
        raise subprocess.CalledProcessError(1, "foo")

    monkeypatch.setattr(parbake_recipe, "run_parbake", subprocess_error)
    with pytest.raises(SystemExit) as exc_info:
        parbake_recipe.run()
        assert exc_info.value.code == 1


def test_run_parbake(monkeypatch, tmp_working_dir):
    """Test run_parbake correctly runs cset parbake."""

    def mock_func(*args, **kwargs):
        return ""

    def mock_data_dirs(*args, **kwargs):
        return [""]

    rose_datac = tmp_working_dir / "share/cycle/20000101T0000Z"
    monkeypatch.setattr(subprocess, "run", mock_func)
    monkeypatch.setattr(parbake_recipe, "recipe_file", mock_func)
    monkeypatch.setattr(parbake_recipe, "data_directories", mock_data_dirs)
    monkeypatch.setenv("CYLC_TASK_NAME", "foo")
    monkeypatch.setenv("ROSE_DATAC", str(rose_datac))

    parbake_recipe.run_parbake()

    # Check recipes directory is created.
    assert (rose_datac / "recipes").is_dir()


def test_run_parbake_case_aggregation(monkeypatch, tmp_working_dir):
    """Test run_parbake correctly runs cset parbake for case aggregation."""

    def mock_func(*args, **kwargs):
        return ""

    def mock_data_dirs(*args, **kwargs):
        return [""]

    rose_datac = tmp_working_dir / "share/cycle/20000101T0000Z"
    monkeypatch.setattr(subprocess, "run", mock_func)
    monkeypatch.setattr(parbake_recipe, "recipe_file", mock_func)
    monkeypatch.setattr(parbake_recipe, "data_directories", mock_data_dirs)
    monkeypatch.setenv("DO_CASE_AGGREGATION", "True")
    monkeypatch.setenv("CYLC_TASK_NAME", "foo")
    monkeypatch.setenv("ROSE_DATAC", str(rose_datac))

    parbake_recipe.run_parbake()

    # Check case_aggregation recipes directory is created.
    assert (rose_datac / "aggregation_recipes").is_dir()


def test_run_parbake_exception(monkeypatch, tmp_working_dir):
    """Test run_parbake raises exception on cset parbake error."""

    def mock_subprocess_run(*args, **kwargs):
        raise subprocess.CalledProcessError(1, args, b"", b"")

    def mock_func(*args, **kwargs):
        return ""

    def mock_data_dirs(*args, **kwargs):
        return [""]

    monkeypatch.setattr(subprocess, "run", mock_subprocess_run)
    monkeypatch.setattr(parbake_recipe, "recipe_file", mock_func)
    monkeypatch.setattr(parbake_recipe, "data_directories", mock_data_dirs)
    monkeypatch.setenv("CYLC_TASK_NAME", "foo")
    monkeypatch.setenv("ROSE_DATAC", f"{tmp_working_dir}/share/cycle/20000101T0000Z")

    with pytest.raises(subprocess.CalledProcessError):
        parbake_recipe.run_parbake()
