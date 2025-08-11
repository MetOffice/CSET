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

from collections import defaultdict
from pathlib import Path

import pytest

import CSET.cset_workflow.app.parbake_recipes.bin.parbake as parbake


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
    """Error when no recipes are enabled."""
    share_dir = tmp_working_dir / "share"
    rose_datac = share_dir / "cycle/20000101T0000Z"
    aggregation = False
    # Defaults non-existent keys to an empty list for testing, as it evaluates
    # to False and can be iterated over.
    variables = defaultdict(lambda: [], {})
    with pytest.raises(ValueError, match="At least one recipe should be enabled."):
        parbake.parbake_all(variables, rose_datac, share_dir, aggregation)


# def test_parbake_all(tmp_working_dir):
#     """Recipes are correctly loaded, parbaked, and written to disk."""
#     share_dir = tmp_working_dir / "share"
#     rose_datac = share_dir / "cycle/20000101T0000Z"
#     aggregation = False
#     # Defaults non-existent keys to an empty list for testing, as it evaluates
#     # to False and can be iterated over.
#     variables = defaultdict(
#         lambda: [],
#         {
#             "SPATIAL_SURFACE_FIELD": True,
#             "SURFACE_FIELDS": ["air_temperature"],
#             "SPATIAL_SURFACE_FIELD_METHOD": ["MEAN"],
#             "m1_name": "foo",
#         },
#     )
#     parbake.parbake_all(variables, rose_datac, share_dir, aggregation)

#     # Check recipes directory is created.
#     assert (rose_datac / "recipes").is_dir()

#     raise NotImplementedError


# def test_parbake_all_aggregate(tmp_working_dir):
#     """Aggregation recipes are correctly loaded, parbaked, and written to disk."""
#     share_dir = tmp_working_dir / "share"
#     rose_datac = share_dir / "cycle/20000101T0000Z"
#     aggregation = True
#     # TODO: Add some variables.
#     variables = {}

#     parbake.parbake_all(variables, rose_datac, share_dir, aggregation)

#     # Check recipes directory is created.
#     assert (rose_datac / "aggregation_recipes").is_dir()

#     raise NotImplementedError
