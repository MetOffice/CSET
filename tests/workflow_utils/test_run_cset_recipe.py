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

import subprocess
from pathlib import Path

import pytest

from CSET._workflow_utils import run_cset_recipe


def test_recipe_file(monkeypatch, tmp_working_dir):
    """Bundled recipe file is written to disk."""
    monkeypatch.setenv("CSET_RECIPE_NAME", "CAPE_ratio_plot.yaml")
    recipe_path = run_cset_recipe.recipe_file()
    assert recipe_path == "CAPE_ratio_plot.yaml"
    assert Path(recipe_path).is_file()


def test_data_directories(monkeypatch):
    """Data directory correctly interpreted."""
    monkeypatch.setenv("ROSE_DATAC", "/share/cycle/20000101T0000Z")
    monkeypatch.setenv("MODEL_IDENTIFIERS", "1")
    expected = ["/share/cycle/20000101T0000Z/data/1"]
    actual = run_cset_recipe.data_directories()
    assert actual == expected


def test_data_directories_multiple_cases(monkeypatch):
    """Data directory correctly interpreted for multiple cases."""
    monkeypatch.setenv("CYLC_WORKFLOW_SHARE_DIR", "/share")
    monkeypatch.setenv("DO_CASE_AGGREGATION", "True")
    monkeypatch.setenv("MODEL_IDENTIFIERS", "1")
    expected = ["/share/cycle/*/data/1"]
    actual = run_cset_recipe.data_directories()
    assert actual == expected


def test_entrypoint(monkeypatch):
    """Check that run_cset_recipe.run() calls the correct function."""
    function_ran = False

    def assert_true():
        nonlocal function_ran
        function_ran = True

    monkeypatch.setattr(run_cset_recipe, "run_recipe_steps", assert_true)
    run_cset_recipe.run()
    assert function_ran, "Function did not run!"


def test_entrypoint_exit_on_subprocess_exception(monkeypatch):
    """Check that run_cset_recipe.run() exits non-zero."""

    def subprocess_error():
        raise subprocess.CalledProcessError(1, "foo")

    monkeypatch.setattr(run_cset_recipe, "run_recipe_steps", subprocess_error)
    with pytest.raises(SystemExit) as exc_info:
        run_cset_recipe.run()
        assert exc_info.value.code == 1


def test_run_recipe_steps(monkeypatch, tmp_working_dir):
    """Test run recipe steps correctly runs CSET and creates an archive."""

    def mock_func(*args, **kwargs):
        return ""

    def mock_data_dirs(*args, **kwargs):
        return [""]

    monkeypatch.setattr(subprocess, "run", mock_func)
    monkeypatch.setattr(run_cset_recipe, "recipe_file", mock_func)
    monkeypatch.setattr(run_cset_recipe, "data_directories", mock_data_dirs)
    monkeypatch.setenv("CYLC_WORKFLOW_SHARE_DIR", "/share")
    monkeypatch.setenv("CYLC_TASK_ID", "20000101T0000Z/foo")

    run_cset_recipe.run_recipe_steps()


def test_run_recipe_steps_exception(monkeypatch, tmp_working_dir):
    """Test run recipe steps correctly raises exception on cset bake error."""

    def mock_subprocess_run(*args, **kwargs):
        raise subprocess.CalledProcessError(1, args, b"", b"")

    def mock_func(*args, **kwargs):
        return ""

    def mock_data_dirs(*args, **kwargs):
        return [""]

    monkeypatch.setattr(subprocess, "run", mock_subprocess_run)
    monkeypatch.setattr(run_cset_recipe, "recipe_file", mock_func)
    monkeypatch.setattr(run_cset_recipe, "data_directories", mock_data_dirs)
    monkeypatch.setenv("CYLC_WORKFLOW_SHARE_DIR", "/share")
    monkeypatch.setenv("CYLC_TASK_ID", "20000101T0000Z/foo")

    with pytest.raises(subprocess.CalledProcessError):
        run_cset_recipe.run_recipe_steps()
