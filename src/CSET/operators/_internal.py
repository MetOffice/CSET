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
import inspect
from ruamel.yaml import YAML
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


def execute_recipe(recipe_yaml: str, input_file: Path, output_file: Path) -> None:
    """Parses and executes a recipe file.

    Parameters
    ----------
    recipe_yaml: stream
        Stream (such as a str or opened file) of a recipe's YAML describing the
        operators that need running.

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
        The recipe file is not well formed.
    """

    def step_parser(step: dict, step_input: any, output_file_path: Path) -> str:
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

        logging.debug(f"args: {kwargs}")
        logging.debug(f"step_input: {step_input}")

        # If first argument of operator is explicitly defined, use that rather
        # than step_input. This is known through introspection of the operator.
        first_arg = next(iter(inspect.signature(operator).parameters.keys()))
        logging.debug(f"first_arg: {first_arg}")
        if first_arg not in kwargs:
            return operator(step_input, **kwargs)
        else:
            return operator(**kwargs)

    with YAML(typ="safe", pure=True) as yaml:
        recipe = yaml.load(recipe_yaml)
    logging.debug(recipe)
    step_input = input_file
    for step in recipe["steps"]:
        step_input = step_parser(step, step_input, output_file)
    logging.info(f"Recipe output: {step_input}")
