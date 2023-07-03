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

from pathlib import Path
import tempfile
from uuid import uuid4

import CSET.operators.RECIPES as RECIPES
import CSET.run as recipe_parsing


def test_get_operator():
    """Get operator and test exceptions"""

    read_operator = recipe_parsing.get_operator("read.read_cubes")
    assert callable(read_operator)

    # Test exception for non-existent operators.
    try:
        recipe_parsing.get_operator("non-existent.operator")
    except ValueError:
        assert True
    else:
        assert False

    # Test exception if wrong type provided.
    try:
        recipe_parsing.get_operator(["Not", b"a", "string", 1])
    except ValueError:
        assert True
    else:
        assert False

    # Test exception if operator isn't a function.
    try:
        recipe_parsing.get_operator("RECIPES.extract_instant_air_temp")
    except ValueError:
        assert True
    else:
        assert False


def test_execute_recipe():
    """Execute recipe"""

    input_file = Path("tests/test_data/air_temp.nc")

    # Test happy case (this is really an integration test).
    output_file = Path(f"{tempfile.gettempdir()}/{uuid4()}.nc")
    recipe_file = RECIPES.extract_instant_air_temp
    recipe_parsing.execute_recipe(recipe_file, input_file, output_file)
    output_file.unlink()

    # Test weird edge cases. Also tests paths not being pathlib Paths, and
    # directly passing in a stream for a recipe file.
    output_file = f"{tempfile.gettempdir()}/{uuid4()}.nc"
    with open("tests/test_data/noop_recipe.yaml", "rb") as recipe:
        recipe_parsing.execute_recipe(recipe, str(input_file), output_file)
    # The output_file doesn't actually get written, so doesn't need removing.
