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

from pathlib import Path
import tempfile

import CSET.operators.RECIPES as RECIPES
import CSET.operators._internal as internal
import logging

logging.basicConfig(level=logging.DEBUG)


def test_get_operator():
    """Get operator and test exceptions"""
    read_operator = internal.get_operator("read.read_cubes")
    assert callable(read_operator)

    # Test exception for non-existant operators.
    exception_occurred = False
    try:
        internal.get_operator("non-existant.operator")
    except ValueError:
        exception_occurred = True
    assert exception_occurred

    # Test exception if wrong type provided.
    exception_occurred = False
    try:
        internal.get_operator(["Not", b"a", "string", 1])
    except ValueError:
        exception_occurred = True
    assert exception_occurred

    # Test exception if operator isn't a function.
    exception_occurred = False
    try:
        internal.get_operator("RECIPES.extract_instant_air_temp")
    except ValueError:
        exception_occurred = True
    assert exception_occurred


def test_execute_recipe():
    """Execute recipe and test exceptions"""
    input_file = Path("tests/test_data/air_temp.nc")

    with tempfile.NamedTemporaryFile(prefix="cset_test_") as output_file:
        # Test exception for file not found.
        exception_happened = False
        try:
            internal.execute_recipe(
                Path("/non-existant/path"), input_file, output_file.name
            )
        except FileNotFoundError:
            exception_happened = True
        assert exception_happened

    # Test happy case (this is really an integration test).
    with tempfile.NamedTemporaryFile(prefix="cset_test_") as output_file:
        recipe_file = RECIPES.extract_instant_air_temp
        internal.execute_recipe(recipe_file, input_file, output_file.name)

    # Test weird edge cases. (also tests paths not being pathlib Paths)
    with tempfile.NamedTemporaryFile(prefix="cset_test_") as output_file:
        recipe_file = "tests/test_data/test_recipe.yaml"
        internal.execute_recipe(recipe_file, input_file, output_file.name)
