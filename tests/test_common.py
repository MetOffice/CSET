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

import pytest

import CSET._common as common


def test_parse_recipe_string():
    """Happy case for loading and parsing of a YAML recipe from a string."""
    valid_recipe = """\
    steps:
        operator: misc.noop
        arg1: Hello
    """
    parsed = common.parse_recipe(valid_recipe)
    assert parsed == {"steps": {"operator": "misc.noop", "arg1": "Hello"}}


def test_parse_recipe_path():
    """Happy case for loading and parsing of a YAML recipe from a Path."""
    parsed = common.parse_recipe(Path("tests/test_data/noop_recipe.yaml"))
    expected = {
        "name": "Noop",
        "description": "A recipe that does nothing. Only used for testing.",
        "steps": [
            {
                "operator": "misc.noop",
                "test_argument": "Banana",
                "dict_argument": {"key": "value"},
                "substep": {"operator": "constraints.combine_constraints"},
            }
        ],
    }
    assert parsed == expected


def test_parse_recipe_exception_missing():
    """Test exception for non-existent file."""
    with pytest.raises(FileNotFoundError):
        common.parse_recipe(Path("/non-existent/path"))


def test_parse_recipe_exception_type():
    """Test exception for incorrect type."""
    with pytest.raises(TypeError):
        common.parse_recipe(True)


def test_parse_recipe_exception_invalid_yaml():
    """Test exception for invalid YAML."""
    with pytest.raises(ValueError):
        common.parse_recipe('"Inside quotes" outside of quotes')


def test_parse_recipe_exception_invalid_recipe():
    """Test exception for valid YAML but invalid recipe."""
    with pytest.raises(ValueError):
        common.parse_recipe("a: 1")


def test_parse_recipe_exception_blank():
    """Test exception for blank recipe."""
    with pytest.raises(ValueError):
        common.parse_recipe("")


def test_parse_recipe_exception_no_steps():
    """Test exception for recipe without any steps."""
    with pytest.raises(ValueError):
        common.parse_recipe("steps: []")


def test_parse_recipe_exception_non_dict():
    """Test exception for recipe that parses to a non-dict."""
    with pytest.raises(ValueError):
        common.parse_recipe("[]")


def test_slugify():
    """Test slugify removes special characters."""
    assert common.slugify("Test") == "test"
    assert (
        common.slugify("Mean Surface Air Temperature Spatial Plot")
        == "mean_surface_air_temperature_spatial_plot"
    )
    assert common.slugify("file-name.yaml") == "file-name.yaml"
    assert common.slugify("First Line\nSecond Line") == "first_line_second_line"
    assert common.slugify("greekαβγδchars") == "greek_chars"
    assert common.slugify("  ABC ") == "abc"
    assert common.slugify("あいうえお") == ""
