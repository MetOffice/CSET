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
    """Loading and parsing of a YAML recipe from a string."""
    valid_recipe = """\
    steps:
        operator: misc.noop
        arg1: Hello
    """
    parsed = common.parse_recipe(valid_recipe)
    assert parsed == {"steps": {"operator": "misc.noop", "arg1": "Hello"}}


def test_parse_recipe_path():
    """Loading and parsing of a YAML recipe from a Path."""
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
    """Exception for non-existent file."""
    with pytest.raises(FileNotFoundError):
        common.parse_recipe(Path("/non-existent/path"))


def test_parse_recipe_exception_type():
    """Exception for incorrect type."""
    with pytest.raises(TypeError):
        common.parse_recipe(True)


def test_parse_recipe_exception_invalid_yaml():
    """Exception for invalid YAML."""
    with pytest.raises(ValueError):
        common.parse_recipe('"Inside quotes" outside of quotes')


def test_parse_recipe_exception_invalid_recipe():
    """Exception for valid YAML but invalid recipe."""
    with pytest.raises(ValueError):
        common.parse_recipe("a: 1")


def test_parse_recipe_exception_blank():
    """Exception for blank recipe."""
    with pytest.raises(ValueError):
        common.parse_recipe("")


def test_parse_recipe_exception_no_steps():
    """Exception for recipe without any steps."""
    with pytest.raises(ValueError):
        common.parse_recipe("steps: []")


def test_parse_recipe_exception_non_dict():
    """Exception for recipe that parses to a non-dict."""
    with pytest.raises(ValueError):
        common.parse_recipe("[]")


def test_slugify():
    """Slugify removes special characters."""
    assert common.slugify("Test") == "test"
    assert (
        common.slugify("Mean Surface Air Temperature Spatial Plot")
        == "mean_surface_air_temperature_spatial_plot"
    )
    assert common.slugify("file-name.yaml") == "file-name.yaml"
    assert common.slugify("First Line\nSecond Line") == "first_line_second_line"
    assert common.slugify("greekαβγδchars") == "greek_chars"
    assert common.slugify("  ABC ") == "abc"
    # Multi-byte unicode characters are removed.
    assert common.slugify("あいうえお") == ""


def test_parse_variable_options():
    """Variable arguments are parsed correctly."""
    args = ("--STASH=m01s01i001", "--COUNT", "3", "--CELL_METHODS=[]")
    expected = {"STASH": "m01s01i001", "COUNT": 3, "CELL_METHODS": []}
    actual = common.parse_variable_options(args)
    assert actual == expected
    # Not valid variable name.
    with pytest.raises(ValueError):
        common.parse_variable_options(("--lowercase=False",))
    # Missing variable value.
    with pytest.raises(ValueError):
        common.parse_variable_options(("--VARIABLE",))


def test_template_variables():
    """Multiple variables are correctly templated into recipe."""
    recipe = {"steps": [{"operator": "misc.noop", "v1": "$VAR_A", "v2": "$VAR_B"}]}
    variables = {"VAR_A": 42, "VAR_B": 3.14}
    expected = {"steps": [{"operator": "misc.noop", "v1": 42, "v2": 3.14}]}
    actual = common.template_variables(recipe, variables)
    assert actual == expected
    assert recipe == expected


def test_replace_template_variable():
    """Placeholders are correctly substituted."""
    # Test direct substitution.
    vars = {"VAR": 1}
    expected = 1
    actual = common.replace_template_variable("$VAR", vars)
    assert actual == expected

    # Insertion into a larger string.
    expected = "The number 1"
    actual = common.replace_template_variable("The number $VAR", vars)
    assert actual == expected

    # Error when variable not provided.
    with pytest.raises(KeyError):
        common.replace_template_variable("$VAR", {})


def test_template_variables_wrong_recipe_type():
    """Give wrong type for recipe."""
    with pytest.raises(TypeError):
        common.template_variables(1, {})


def test_get_recipe_meta(tmp_working_dir):
    """Reading metadata from disk."""
    # Default for missing file.
    meta_file = Path("meta.json")
    assert not meta_file.exists()
    assert common.get_recipe_metadata() == {}
    assert meta_file.exists()
    # Reads existing file.
    meta_file.write_text('{"title": "Example Title"}', encoding="UTF-8")
    assert common.get_recipe_metadata()["title"] == "Example Title"


def test_simple_placeholder():
    """Simple case of a single placeholder being templated."""
    template = "<p>{{greeting}} World!</p>"
    actual = common.render(template, greeting="Hello")
    expected = "<p>Hello World!</p>"
    assert actual == expected


def test_multiple_placeholders():
    """Templating of multiple different placeholders."""
    template = "<p>{{greeting}} {{who}}!</p>"
    actual = common.render(template, greeting="Hello", who="World")
    expected = "<p>Hello World!</p>"
    assert actual == expected


def test_repeated_placeholders():
    """Templating of repeated placeholders."""
    template = "<p>{{who}} says {{greeting}} {{ who }}!</p>"
    actual = common.render(template, greeting="Hello", who="World")
    expected = "<p>World says Hello World!</p>"
    assert actual == expected


def test_template_with_no_placeholders():
    """Trivial case with no placeholders."""
    template = "<p>Hello World!</p>"
    assert common.render(template) == template


def test_extra_arguments():
    """Give unneeded keyword arguments to ensure they are ignored."""
    template = "<p>{{greeting}} World!</p>"
    actual = common.render(template, greeting="Hello", extra="Ignored")
    expected = "<p>Hello World!</p>"
    assert actual == expected


def test_missing_argument_exception():
    """Exception raised if template is missing a value."""
    template = "<p>{{greeting}} World!</p>"
    with pytest.raises(common.TemplateError):
        common.render(template)


def test_improper_template_type_exception():
    """Exception raised if template isn't a string."""
    template = 3.14159265
    with pytest.raises(TypeError):
        common.render(template)


def test_render_file():
    """Render a template in a file."""
    actual = common.render_file("tests/test_data/template_file.html", greeting="Hello")
    expected = "<p>Hello World!</p>\n"
    assert actual == expected
