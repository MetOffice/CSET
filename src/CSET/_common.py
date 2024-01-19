# Copyright 2022-2023 Met Office and contributors.
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

import copy
import io
import json
import logging
import re
from pathlib import Path
from typing import Any, List, Union

import ruamel.yaml


class ArgumentError(ValueError):
    """Indicates provided arguments are not understood."""


def parse_recipe(recipe_yaml: Union[Path, str]):
    """Parse a recipe into a python dictionary.

    Parameters
    ----------
    recipe_yaml: Path | str
        Path to recipe file, or the recipe YAML directly.

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

    Examples
    --------
    >>> CSET._recipe_parsing.parse_recipe(Path("myrecipe.yaml"))
    {'steps': [{'operator': 'misc.noop'}]}
    """
    # Check the type provided explicitly.
    if isinstance(recipe_yaml, str):
        recipe_yaml = io.StringIO(recipe_yaml)
    elif not isinstance(recipe_yaml, Path):
        raise TypeError("recipe_yaml must be a str or Path.")

    with ruamel.yaml.YAML(typ="safe", pure=True) as yaml:
        try:
            recipe = yaml.load(recipe_yaml)
        except ruamel.yaml.parser.ParserError as err:
            raise ValueError("ParserError: Invalid YAML") from err
        except ruamel.yaml.error.YAMLStreamError as err:
            raise TypeError("Must provide a file object (with a read method)") from err

    # Checking that the recipe actually has some steps, and providing helpful
    # error messages otherwise.
    logging.debug(recipe)
    try:
        if len(recipe["steps"]) < 1:
            raise ValueError("Recipe must have at least 1 step.")
    except KeyError as err:
        raise ValueError("Invalid Recipe.") from err
    except TypeError as err:
        if recipe is None:
            raise ValueError("Recipe must have at least 1 step.") from err
        if not isinstance(recipe, dict):
            raise ValueError("Recipe must either be YAML, or a Path.") from err
        # This should never be reached; it's a bug if it is.
        raise err  # pragma: no cover

    return recipe


def slugify(s: str) -> str:
    """Turn a string into a version that can be used everywhere.

    The resultant string will only consist of a-z, 0-9, dots, dashes, and
    underscores.
    """
    return re.sub(r"[^a-z0-9\._-]+", "_", s.casefold()).strip("_")


def get_recipe_metadata() -> dict:
    """Get the metadata of the running recipe."""
    with open("meta.json", "rt", encoding="UTF-8") as fp:
        return json.load(fp)


def parse_variable_options(arguments: List[str]) -> dict:
    """Parse a list of arguments into a dictionary of variables.

    The variable name arguments start with two hyphen-minus (`--`), consisting
    of only capital letters (`A`-`Z`) and underscores (`_`). While the variable
    name is restricted, the value of the variable can be any string.

    Parameters
    ----------
    arguments: List[str]
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
        if re.match(r"^--[A-Z_]+=.*$", arguments[i]):
            key, value = arguments[i].split("=", 1)
        elif re.match(r"^--[A-Z_]+$", arguments[i]):
            try:
                key = arguments[i].strip("-")
                value = arguments[i + 1]
            except IndexError as err:
                raise ArgumentError(f"No value for variable {arguments[i]}") from err
            i += 1
        else:
            raise ArgumentError(f"Unknown argument: {arguments[i]}")
        try:
            recipe_variables[key.strip("-")] = json.loads(value)
        except json.JSONDecodeError:
            recipe_variables[key.strip("-")] = value
        i += 1
    return recipe_variables


def is_variable(var: Any) -> bool:
    """Check if recipe value is a variable."""
    if isinstance(var, str) and re.match(r"^\$[A-Z_]+$", var):
        return True
    return False


def template_variables(recipe: Union[dict, list], variables: dict) -> dict:
    """Insert variables into recipe.

    Parameters
    ----------
    recipe: dict | list
        The recipe as a python dictionary.
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
    recipe = copy.deepcopy(recipe)
    if isinstance(recipe, dict):
        index = recipe.keys()
    elif isinstance(recipe, list):
        index = range(len(recipe))
    else:
        raise TypeError("recipe must be a dict or list.")
    for i in index:
        if isinstance(recipe[i], (dict, list)):
            recipe[i] = template_variables(recipe[i], variables)
        if is_variable(recipe[i]):
            logging.debug("Templating %s", recipe[i])
            recipe[i] = variables[recipe[i].removeprefix("$")]
    return recipe
