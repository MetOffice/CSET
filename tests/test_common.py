# Copyright 2023 Met Office and contributors.
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

"""Tests for common functionality across CSET."""

from pathlib import Path

import CSET._common as common


def test_parse_recipe():
    """Loading and parsing of YAML recipes. Also tests exceptions."""

    # Check happy case.
    valid_recipe = """\
    steps:
        operator: misc.noop
        arg1: Hello
    """
    parsed = common.parse_recipe(valid_recipe)
    assert parsed == {"steps": {"operator": "misc.noop", "arg1": "Hello"}}

    # Test exception for non-existent file.
    try:
        common.parse_recipe(Path("/non-existent/path"))
    except FileNotFoundError:
        assert True
    else:
        assert False

    # Test exception for incorrect type.
    try:
        common.parse_recipe(True)
    except TypeError:
        assert True
    else:
        assert False

    # Test exception for invalid YAML.
    try:
        common.parse_recipe('"Inside quotes" outside of quotes')
    except ValueError:
        assert True
    else:
        assert False

    # Test exception for valid YAML but invalid recipe.
    try:
        common.parse_recipe("a: 1")
    except ValueError:
        assert True
    else:
        assert False

    # Test exception for blank recipe.
    try:
        common.parse_recipe("")
    except ValueError:
        assert True
    else:
        assert False

    # Test exception for recipe without any steps.
    try:
        common.parse_recipe("steps: []")
    except ValueError:
        assert True
    else:
        assert False

    # Test exception for recipe that parses to a non-dict.
    try:
        common.parse_recipe("[]")
    except ValueError:
        assert True
    else:
        assert False
