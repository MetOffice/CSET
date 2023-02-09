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
from secrets import token_hex
import sys

import CSET.operators.RECIPES as RECIPES
import CSET.operators._internal as internal


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


def test_execute_recipe():
    """Execute recipe and test exceptions"""
    recipe_file = RECIPES.extract_instant_air_temp
    input_file = Path("tests/test_data/air_temp.nc")
    output_file = Path(f"/tmp/{token_hex(4)}_cset_test_output.nc")

    # Test exception for unfound file.
    exception_happened = False
    try:
        internal.execute_recipe(Path("/non-existant/path"), input_file, output_file)
    except FileNotFoundError:
        exception_happened = True
    assert exception_happened

    # Test happy case (this is really an integration test).
    exception_happened = False
    try:
        internal.execute_recipe(recipe_file, input_file, output_file)
    except Exception as e:
        print(e, file=sys.stderr)
        exception_happened = True
    assert not exception_happened
