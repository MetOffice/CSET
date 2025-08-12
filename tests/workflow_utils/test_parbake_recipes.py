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

from pathlib import Path

import pytest

import CSET.cset_workflow.app.parbake_recipes.bin.parbake as parbake
import CSET.recipes


def test_main(monkeypatch):
    """Check parbake.main() invokes parbake_all correctly."""
    function_ran = False

    def mock_parbake_all(variables, rose_datac, share_dir, aggregation):
        nonlocal function_ran
        function_ran = True
        assert variables == {"variable": "value"}
        assert rose_datac == Path("/share/cycle/20000101T0000Z")
        assert share_dir == Path("/share")
        assert isinstance(aggregation, bool)

    monkeypatch.setattr(parbake, "parbake_all", mock_parbake_all)

    # Setup environment.
    monkeypatch.setenv("ENCODED_ROSE_SUITE_VARIABLES", "eyJ2YXJpYWJsZSI6ICJ2YWx1ZSJ9")
    monkeypatch.setenv("ROSE_DATAC", "/share/cycle/20000101T0000Z")
    monkeypatch.setenv("CYLC_WORKFLOW_SHARE_DIR", "/share")
    monkeypatch.setenv("DO_CASE_AGGREGATION", "True")

    parbake.main()
    assert function_ran, "Function did not run!"

    # Retry without DO_CASE_AGGREGATION
    function_ran = False
    monkeypatch.delenv("DO_CASE_AGGREGATION")
    parbake.main()
    assert function_ran, "Function did not run!"


def test_parbake_all_none_enabled(tmp_working_dir):
    """Error when no recipes are enabled.

    This also tests that all loaders don't error and return no recipes when
    variables are undefined.
    """
    # Non-aggregation recipes.
    with pytest.raises(ValueError, match="At least one recipe should be enabled."):
        parbake.parbake_all({}, tmp_working_dir, tmp_working_dir, False)
    # Aggregation recipes.
    with pytest.raises(ValueError, match="At least one recipe should be enabled."):
        parbake.parbake_all({}, tmp_working_dir, tmp_working_dir, True)


def test_parbake_all_missing_load_func(tmp_working_dir, monkeypatch):
    """Error when loader doesn't provide a load() function."""
    # Parbake module does not have a load() function.
    monkeypatch.setattr(CSET.recipes, "loader_test", parbake)
    with pytest.raises(
        AttributeError,
        match="CSET.recipes.loader_test should provide a `load` function.",
    ):
        parbake.parbake_all({}, tmp_working_dir, tmp_working_dir, False)


def test_parbake_all(tmp_working_dir, monkeypatch):
    """Recipes are correctly loaded and parbake called."""
    share_dir = tmp_working_dir / "share"
    rose_datac = share_dir / "cycle/20000101T0000Z"
    variables = {"TESTING_RECIPE": True}
    aggregation = False
    # Counter for number of times parbake was called.
    recipes_parbaked = 0

    def mock_parbake(self: CSET.recipes.RawRecipe, ROSE_DATAC: Path, SHARE_DIR: Path):
        nonlocal recipes_parbaked
        recipes_parbaked += 1
        assert SHARE_DIR == share_dir
        assert ROSE_DATAC == rose_datac
        assert self.aggregation is aggregation
        assert self.recipe == "test.yaml"
        assert self.model_ids == [1]
        assert self.variables == {}

    monkeypatch.setattr(CSET.recipes.RawRecipe, "parbake", mock_parbake)
    parbake.parbake_all(variables, rose_datac, share_dir, aggregation)
    assert recipes_parbaked == 1


def test_parbake_all_aggregate(tmp_working_dir, monkeypatch):
    """Aggregation recipes are correctly loaded and parbake called."""
    share_dir = tmp_working_dir / "share"
    rose_datac = share_dir / "cycle/20000101T0000Z"
    variables = {"TESTING_RECIPE": True}
    aggregation = True
    # Counter for number of times parbake was called.
    recipes_parbaked = 0

    def mock_parbake(self: CSET.recipes.RawRecipe, ROSE_DATAC: Path, SHARE_DIR: Path):
        nonlocal recipes_parbaked
        recipes_parbaked += 1
        assert SHARE_DIR == share_dir
        assert ROSE_DATAC == rose_datac
        assert self.aggregation is aggregation
        assert self.recipe == "test.yaml"
        assert self.model_ids == [1]
        assert self.variables == {}

    monkeypatch.setattr(CSET.recipes.RawRecipe, "parbake", mock_parbake)
    parbake.parbake_all(variables, rose_datac, share_dir, aggregation)
    assert recipes_parbaked == 1
