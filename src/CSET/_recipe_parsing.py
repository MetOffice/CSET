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

"""Internal functions used to run operators."""

import logging
from pathlib import Path
from typing import Union
import inspect
import ruamel.yaml
import CSET.operators


def get_operator(name: str):
    """
    Gets an operator by its name.

    Parameters
    ----------
    name: str
        The name of the desired operator.

    Returns
    -------
    function
        The named operator.

    Raises
    ------
    ValueError
        If name is not an operator.

    Examples
    --------
    >>> CSET.operators.get_operator("read.read_cubes")
    <function read_cubes at 0x7fcf9353c8b0>
    """

    logging.debug("get_operator(%s)", name)
    try:
        name_sections = name.split(".")
        operator = CSET.operators
        for section in name_sections:
            operator = getattr(operator, section)
        if callable(operator):
            return operator
        else:
            raise AttributeError
    except (AttributeError, TypeError):
        raise ValueError(f"Unknown operator: {name}")


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

    with ruamel.yaml.YAML(typ="safe", pure=True) as yaml:
        try:
            recipe = yaml.load(recipe_yaml)
        except ruamel.yaml.parser.ParserError:
            raise ValueError("ParserError: Invalid YAML")
        except ruamel.yaml.error.YAMLStreamError:
            raise TypeError("Must provide a stream (with a read method)")

    # Checking that the recipe actually has some steps, and providing helpful
    # error messages otherwise.
    logging.debug(recipe)
    try:
        if len(recipe["steps"]) < 1:
            raise ValueError("Recipe must have at least 1 step.")
    except KeyError as err:
        raise ValueError("Invalid Recipe:", err)
    except TypeError as err:
        if recipe is None:
            raise ValueError("Recipe must have at least 1 step.")
        if type(recipe) != dict:
            raise ValueError("Recipe must either be YAML, or a Path.")
        # This should never be reached; it's a bug if it is.
        raise err  # pragma: no cover

    return recipe


def execute_recipe(
    recipe_yaml: Union[Path, str], input_file: Path, output_file: Path
) -> None:
    """Parses and executes a recipe file.

    Parameters
    ----------
    recipe_yaml: Path or str
        Path to a file containing, or string of, a recipe's YAML describing the
        operators that need running. If a Path is provided it is opened and
        read.

    input_file: Path
        Pathlike to netCDF (or something else that iris read) file to be used as
        input.

    output_file: Path
        Pathlike indicating desired location of output.

    Raises
    ------
    FileNotFoundError
        The recipe or input file cannot be found.

    ValueError
        The recipe is not well formed.

    TypeError
        The provided recipe is not a stream or Path.
    """

    def step_parser(step: dict, step_input: any, output_file_path: Path) -> str:
        """Executes a recipe step, recursively executing any sub-steps."""
        logging.debug(f"Executing step: {step}")
        kwargs = {}
        for key in step.keys():
            if key == "operator":
                operator = get_operator(step["operator"])
                logging.info(f"operator: {step['operator']}")
            elif type(step[key]) == dict and "operator" in step[key]:
                logging.debug(f"Recursing into argument: {key}")
                kwargs[key] = step_parser(step[key], step_input, output_file_path)
            elif step[key] == "CSET_OUTPUT_PATH":
                kwargs[key] = output_file_path
            else:
                kwargs[key] = step[key]
        logging.debug("args: %s", kwargs)
        logging.debug("step_input: %s", step_input)
        # If first argument of operator is explicitly defined, use that rather
        # than step_input. This is known through introspection of the operator.
        first_arg = next(iter(inspect.signature(operator).parameters.keys()))
        logging.debug("first_arg: %s", first_arg)
        if first_arg not in kwargs:
            return operator(step_input, **kwargs)
        else:
            return operator(**kwargs)

    recipe = parse_recipe(recipe_yaml)

    # Execute the recipe.
    step_input = input_file
    for step in recipe["steps"]:
        step_input = step_parser(step, step_input, output_file)

    logging.info("Recipe output: %s", step_input)
