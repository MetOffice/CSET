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

"""Subpackage contains all of CSET's operators."""

import inspect
import logging
import os
from pathlib import Path
from typing import Union

# Stop iris giving a warning whenever it loads something.
from iris import FUTURE

# Import operators here so they are exported for use by recipes.
import CSET.operators
from CSET._common import parse_recipe
from CSET.operators import (
    aggregate,
    collapse,
    constraints,
    filters,
    misc,
    plot,
    read,
    write,
)

FUTURE.datum_support = True


def get_operator(name: str):
    """Get an operator by its name.

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
    except (AttributeError, TypeError) as err:
        raise ValueError(f"Unknown operator: {name}") from err


def execute_recipe(
    recipe_yaml: Union[Path, str], input_file: Path, output_directory: Path
) -> None:
    """Parse and executes a recipe file.

    Parameters
    ----------
    recipe_yaml: Path or str
        Path to a file containing, or string of, a recipe's YAML describing the
        operators that need running. If a Path is provided it is opened and
        read.

    input_file: Path
        Pathlike to netCDF (or something else that iris read) file to be used as
        input.

    output_directory: Path
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

    def step_parser(step: dict, step_input: any) -> str:
        """Execute a recipe step, recursively executing any sub-steps."""
        logging.debug(f"Executing step: {step}")
        kwargs = {}
        for key in step.keys():
            if key == "operator":
                operator = get_operator(step["operator"])
                logging.info(f"operator: {step['operator']}")
            elif isinstance(step[key], dict) and "operator" in step[key]:
                logging.debug(f"Recursing into argument: {key}")
                kwargs[key] = step_parser(step[key], step_input)
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
    step_input = Path(input_file).absolute()
    try:
        output_directory.mkdir(parents=True, exist_ok=True)
    except FileExistsError as err:
        logging.error("Output directory is a file. %s", output_directory)
        raise err

    original_working_directory = Path.cwd()
    os.chdir(output_directory)
    try:
        # Execute the recipe.
        for step in recipe["steps"]:
            step_input = step_parser(step, step_input)
        logging.info("Recipe output: %s", step_input)
    finally:
        os.chdir(original_working_directory)


__all__ = [
    "aggregate",
    "collapse",
    "constraints",
    "execute_recipe",
    "filters",
    "get_operator",
    "misc",
    "plot",
    "read",
    "write",
]
