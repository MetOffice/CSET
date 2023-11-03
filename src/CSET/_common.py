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

import io
import logging
from pathlib import Path
from typing import Union

import ruamel.yaml


def parse_recipe(recipe_yaml: Union[Path, str]):
    """
    Parses a recipe into a python dictionary.

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
