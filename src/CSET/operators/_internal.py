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

try:
    import tomllib
except ModuleNotFoundError:
    # tomllib is in standard library from 3.11.
    import tomli as tomllib

import CSET.operators


def get_operator(name: str):
    """
    Increments the input by one.

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
    if name == "read.read_cubes":
        return CSET.operators.read.read_cubes
    if name == "write.write_cube_to_nc":
        return CSET.operators.write.write_cube_to_nc
    if name == "filters.filter_cubes":
        return CSET.operators.filters.filter_cubes
    if name == "constraints.generate_stash_constraint":
        return CSET.operators.constraints.generate_stash_constraint
    if name == "constraints.generate_var_constraint":
        return CSET.operators.constraints.generate_var_constraint
    if name == "constraints.generate_cell_methods_constraint":
        return CSET.operators.constraints.generate_cell_methods_constraint
    if name == "constraints.combine_constraints":
        return CSET.operators.constraints.combine_constraints
    else:
        raise ValueError(f"Unknown operator: {name}")


def execute_recipe(recipe_file: Path, input_file: Path, output_file: Path) -> None:
    """Parses and executes a recipe file.

    Parameters
    ----------
    recipe_file: Path
        Pathlike to a configuration file indicating the operators that need
        running.

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

    def step_parser(step, step_io, output_file_path: Path) -> str:
        if "input" in step:
            if type(step["input"]) == dict:
                logging.debug(f"Recursing into input: {step['input']}")
                step_io = step_parser(step["input"], step_io, output_file_path)
            else:
                step_io = step["input"]
        args = {}
        if "args" in step:
            for key in step["args"].keys():
                if type(step["args"][key]) == dict:
                    logging.debug(f"Recursing into args: {step['args']}")
                    args[key] = step_parser(
                        step["args"][key], step_io, output_file_path
                    )
                elif step["args"][key] == "MAGIC_OUTPUT_PATH":
                    args[key] = output_file_path
                else:
                    args[key] = step["args"][key]
        operator = CSET.operators._internal.get_operator(step["operator"])
        logging.info(f"operator = {step['operator']}")
        logging.debug(f"step_input = {step_io}")
        logging.debug(f"args = {args}")
        return operator(step_io, **args)

    with open(recipe_file, "rb") as f:
        recipe = tomllib.load(f)
    step_io = input_file
    for step in recipe["steps"]:
        step_io = step_parser(step, step_io, output_file)
