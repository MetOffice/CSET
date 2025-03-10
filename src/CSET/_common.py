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

"""Common functionality used across CSET."""

import ast
import io
import json
import logging
import re
from collections.abc import Iterable
from pathlib import Path

import ruamel.yaml


class ArgumentError(ValueError):
    """Provided arguments are not understood."""


def parse_recipe(recipe_yaml: Path | str, variables: dict = None) -> dict:
    """Parse a recipe into a python dictionary.

    Parameters
    ----------
    recipe_yaml: Path | str
        Path to recipe file, or the recipe YAML directly.
    variables: dict
        Dictionary of recipe variables. If None templating is not attempted.

    Returns
    -------
    recipe: dict
        The recipe as a python dictionary.

    Raises
    ------
    ValueError
        If the recipe is invalid. E.g. invalid YAML, missing any steps, etc.
    TypeError
        If recipe_yaml isn't a Path or string.
    KeyError
        If needed recipe variables are not supplied.

    Examples
    --------
    >>> CSET._common.parse_recipe(Path("myrecipe.yaml"))
    {'steps': [{'operator': 'misc.noop'}]}
    """
    # Ensure recipe_yaml is something the YAML parser can read.
    if isinstance(recipe_yaml, str):
        recipe_yaml = io.StringIO(recipe_yaml)
    elif not isinstance(recipe_yaml, Path):
        raise TypeError("recipe_yaml must be a str or Path.")

    # Parse the recipe YAML.
    with ruamel.yaml.YAML(typ="safe", pure=True) as yaml:
        try:
            recipe = yaml.load(recipe_yaml)
        except ruamel.yaml.parser.ParserError as err:
            raise ValueError("ParserError: Invalid YAML") from err

    logging.debug("Recipe before templating:\n%s", recipe)
    check_recipe_has_steps(recipe)

    if variables is not None:
        logging.debug("Recipe variables: %s", variables)
        recipe = template_variables(recipe, variables)

    logging.debug("Recipe after templating:\n%s", recipe)
    return recipe


def check_recipe_has_steps(recipe: dict):
    """Check a recipe has the minimum required steps.

    Checking that the recipe actually has some steps, and providing helpful
    error messages otherwise. We must have at least a steps step, as that
    reads the raw data.

    Parameters
    ----------
    recipe: dict
        The recipe as a python dictionary.

    Raises
    ------
    ValueError
        If the recipe is invalid. E.g. invalid YAML, missing any steps, etc.
    TypeError
        If recipe isn't a dict.
    KeyError
        If needed recipe variables are not supplied.
    """
    if not isinstance(recipe, dict):
        raise TypeError("Recipe must contain a mapping.")
    if "steps" not in recipe:
        raise ValueError("Recipe must contain a 'steps' key.")
    try:
        if len(recipe["steps"]) < 1:
            raise ValueError("Recipe must have at least 1 step.")
    except TypeError as err:
        raise ValueError("'steps' key must contain a sequence of steps.") from err


def slugify(s: str) -> str:
    """Turn a string into a version that can be used everywhere.

    The resultant string will only consist of a-z, 0-9, dots, dashes, and
    underscores.
    """
    return re.sub(r"[^a-z0-9\._-]+", "_", s.casefold()).strip("_")


def get_recipe_metadata() -> dict:
    """Get the metadata of the running recipe."""
    try:
        with open("meta.json", "rt", encoding="UTF-8") as fp:
            return json.load(fp)
    except FileNotFoundError:
        meta = {}
        with open("meta.json", "wt", encoding="UTF-8") as fp:
            json.dump(meta, fp, indent=2)
        return {}


def parse_variable_options(arguments: list[str]) -> dict:
    """Parse a list of arguments into a dictionary of variables.

    The variable name arguments start with two hyphen-minus (`--`), consisting
    of only capital letters (`A`-`Z`) and underscores (`_`). While the variable
    name is restricted, the value of the variable can be any string.

    Parameters
    ----------
    arguments: list[str]
        List of arguments, e.g: `["--LEVEL", "2", "--STASH=m01s01i001"]`

    Returns
    -------
    recipe_variables: dict
        Dictionary keyed with the variable names.

    Raises
    ------
    ValueError
        If any arguments cannot be parsed.
    """
    recipe_variables = {}
    i = 0
    while i < len(arguments):
        if re.fullmatch(r"--[A-Z_]+=.*", arguments[i]):
            key, value = arguments[i].split("=", 1)
        elif re.fullmatch(r"--[A-Z_]+", arguments[i]):
            try:
                key = arguments[i].strip("-")
                value = arguments[i + 1]
            except IndexError as err:
                raise ArgumentError(f"No value for variable {arguments[i]}") from err
            i += 1
        else:
            raise ArgumentError(f"Unknown argument: {arguments[i]}")
        try:
            # Remove quotes from arguments, in case left in CSET_ADDOPTS.
            if re.fullmatch(r"""["'].+["']""", value):
                value = value[1:-1]
            recipe_variables[key.strip("-")] = ast.literal_eval(value)
        # Capture the many possible exceptions from ast.literal_eval
        except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
            recipe_variables[key.strip("-")] = value
        i += 1
    return recipe_variables


def template_variables(recipe: dict | list, variables: dict) -> dict:
    """Insert variables into recipe.

    Parameters
    ----------
    recipe: dict | list
        The recipe as a python dictionary. It is updated in-place.
    variables: dict
        Dictionary of variables for the recipe.

    Returns
    -------
    recipe: dict
        Filled recipe as a python dictionary.

    Raises
    ------
    KeyError
        If needed recipe variables are not supplied.
    """
    if isinstance(recipe, dict):
        index = recipe.keys()
    elif isinstance(recipe, list):
        # We have to handle lists for when we have one inside a recipe.
        index = range(len(recipe))
    else:
        raise TypeError("recipe must be a dict or list.", recipe)

    for i in index:
        if isinstance(recipe[i], (dict, list)):
            recipe[i] = template_variables(recipe[i], variables)
        elif isinstance(recipe[i], str):
            recipe[i] = replace_template_variable(recipe[i], variables)
    return recipe


def replace_template_variable(s: str, variables):
    """Fill all variable placeholders in the string."""
    for var_name, var_value in variables.items():
        placeholder = f"${var_name}"
        # If the value is just the placeholder we directly overwrite it
        # to keep the value type.
        if s == placeholder:
            s = var_value
            break
        else:
            s = s.replace(placeholder, str(var_value))
    if isinstance(s, str) and re.match(r"^.*\$[A-Z_].*", s):
        raise KeyError("Variable without a value.", s)
    return s


################################################################################
# Templating code taken from the simple_template package under the 0BSD licence.
# Original at https://github.com/Fraetor/simple_template
################################################################################


class TemplateError(KeyError):
    """Rendering a template failed due a placeholder without a value."""


def render(template: str, /, **variables) -> str:
    """Render the template with the provided variables.

    The template should contain placeholders that will be replaced. These
    placeholders consist of the placeholder name within double curly braces. The
    name of the placeholder should be a valid python identifier. Whitespace
    between the braces and the name is ignored. E.g.: `{{ placeholder_name }}`

    An exception will be raised if there are placeholders without corresponding
    values. It is acceptable to provide unused values; they will be ignored.

    Parameters
    ----------
    template: str
        Template to fill with variables.

    **variables: Any
        Keyword arguments for the placeholder values. The argument name should
        be the same as the placeholder's name. You can unpack a dictionary of
        value with `render(template, **my_dict)`.

    Returns
    -------
    rendered_template: str
        Filled template.

    Raises
    ------
    TemplateError
        Value not given for a placeholder in the template.
    TypeError
        If the template is not a string, or a variable cannot be casted to a
        string.

    Examples
    --------
    >>> template = "<p>Hello {{myplaceholder}}!</p>"
    >>> simple_template.render(template, myplaceholder="World")
    "<p>Hello World!</p>"
    """

    def isidentifier(s: str):
        return s.isidentifier()

    def extract_placeholders():
        matches = re.finditer(r"{{\s*([^}]+)\s*}}", template)
        unique_names = {match.group(1) for match in matches}
        return filter(isidentifier, unique_names)

    def substitute_placeholder(name):
        try:
            value = str(variables[name])
        except KeyError as err:
            raise TemplateError("Placeholder missing value", name) from err
        pattern = r"{{\s*%s\s*}}" % re.escape(name)
        return re.sub(pattern, value, template)

    for name in extract_placeholders():
        template = substitute_placeholder(name)
    return template


def render_file(template_path: str, /, **variables) -> str:
    """Render a template directly from a file.

    Otherwise the same as `simple_template.render()`.

    Examples
    --------
    >>> simple_template.render_file("/path/to/template.html", myplaceholder="World")
    "<p>Hello World!</p>"
    """
    with open(template_path, "rt", encoding="UTF-8") as fp:
        template = fp.read()
    return render(template, **variables)


def iter_maybe(thing) -> Iterable:
    """Ensure thing is Iterable. Strings count as atoms."""
    if isinstance(thing, Iterable) and not isinstance(thing, str):
        return thing
    return (thing,)


def human_sorted(iterable: Iterable, reverse: bool = False) -> list:
    """Sort such numbers within strings are sorted correctly."""
    # Adapted from https://nedbatchelder.com/blog/200712/human_sorting.html

    def alphanum_key(s):
        """Turn a string into a list of string and number chunks.

        >>> alphanum_key("z23a")
        ["z", 23, "a"]
        """
        try:
            return [int(c) if c.isdecimal() else c for c in re.split(r"(\d+)", s)]
        except TypeError:
            return s

    return sorted(iterable, key=alphanum_key, reverse=reverse)


def combine_dicts(d1: dict, d2: dict) -> dict:
    """Recursively combines two dictionaries.

    Duplicate atoms favour the second dictionary.
    """
    # Update existing keys.
    for key in d1.keys() & d2.keys():
        if isinstance(d1[key], dict):
            d1[key] = combine_dicts(d1[key], d2[key])
        else:
            d1[key] = d2[key]
    # Add any new keys.
    for key in d2.keys() - d1.keys():
        d1[key] = d2[key]
    return d1


def sort_dict(d: dict) -> dict:
    """Recursively sort a dictionary."""
    # Thank you to https://stackoverflow.com/a/47882384
    return {
        k: sort_dict(v) if isinstance(v, dict) else v
        for k, v in human_sorted(d.items())
    }
