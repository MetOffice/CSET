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

import os
from pathlib import Path
import logging
import tempfile
from uuid import uuid4

import CSET.operators.RECIPES as RECIPES
import CSET.operators._internal as internal


logging.basicConfig(level=logging.DEBUG)


def test_get_operator():
    """Get operator and test exceptions"""
    read_operator = internal.get_operator("read.read_cubes")
    assert callable(read_operator)

    # Test exception for non-existent operators.
    exception_occurred = False
    try:
        internal.get_operator("non-existent.operator")
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

    # Test exception for non-existent file.
    exception_happened = False
    try:
        internal.execute_recipe(Path("/non-existent/path"), os.devnull, os.devnull)
    except FileNotFoundError:
        exception_happened = True
    assert exception_happened

    # Test exception for incorrect type.
    exception_happened = False
    try:
        internal.execute_recipe(True, os.devnull, os.devnull)
    except TypeError:
        exception_happened = True
    assert exception_happened

    # Test exception for invalid YAML.
    exception_happened = False
    try:
        internal.execute_recipe(
            '"Inside quotes" outside of quotes', os.devnull, os.devnull
        )
    except ValueError:
        exception_happened = True
    assert exception_happened

    # Test exception for valid YAML but invalid recipe.
    exception_happened = False
    try:
        internal.execute_recipe("a: 1", os.devnull, os.devnull)
    except ValueError:
        exception_happened = True
    assert exception_happened

    # Test exception for blank recipe.
    exception_happened = False
    try:
        internal.execute_recipe("", os.devnull, os.devnull)
    except ValueError:
        exception_happened = True
    assert exception_happened

    # Test exception for recipe without any steps.
    exception_happened = False
    try:
        internal.execute_recipe("steps: []", os.devnull, os.devnull)
    except ValueError:
        exception_happened = True
    assert exception_happened

    # Test exception for recipe that parses to a non-dict.
    exception_happened = False
    try:
        internal.execute_recipe("[]", os.devnull, os.devnull)
    except ValueError:
        exception_happened = True
    assert exception_happened

    # Test happy case (this is really an integration test).
    output_file = Path(f"{tempfile.gettempdir()}/{uuid4()}.nc")
    recipe_file = RECIPES.extract_instant_air_temp
    internal.execute_recipe(recipe_file, input_file, output_file)
    output_file.unlink()

    # Test weird edge cases. Also tests paths not being pathlib Paths, and
    # directly passing in a stream for a recipe file.
    output_file = f"{tempfile.gettempdir()}/{uuid4()}.nc"
    with open("tests/test_data/noop_recipe.yaml", "rb") as recipe:
        internal.execute_recipe(recipe, str(input_file), output_file)
    # The output_file doesn't actually get written, so doesn't need removing.
