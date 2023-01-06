#! /usr/bin/env python3

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

"""
Script to chain together individual operators.

Currently it is hard coded, but in future it will take an argument specifying a
config file describing what operators to run in what order.
"""

import argparse
import logging
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    # tomllib is in standard library from 3.11.
    import tomli as tomllib


class Recipe:
    def __init__(self, recipe_file_path: Path) -> None:
        def recipe_parser(recipe) -> callable:
            recipe_code = []
            for step in recipe["steps"]:
                recipe_code.append(step_parser(step, primary=True))
            recipe_code = "\n".join(recipe_code)
            logging.info("Generated Code:\n" + recipe_code)

            def operator_task(input_file_path, output_file_path):
                import CSET.operators as operators  # noqa: F401

                step_io = input_file_path  # noqa: F841
                # ! exec is BAD!
                exec(recipe_code)

            return operator_task

        def step_parser(step, primary=False) -> str:
            if "input" in step:
                if type(step["input"]) == dict:
                    step_input = step_parser(step["input"])
                else:
                    step_input = repr(step["input"])
            else:
                step_input = "step_io"
            args = []
            if "args" in step:
                for key in step["args"].keys():
                    if type(step["args"][key]) == dict:
                        args.append(f"{key}={(step_parser(step['args'][key]))}")
                    elif step["args"][key] == "MAGIC_OUTPUT_PATH":
                        args.append(f"{key}=output_file_path")
                    else:
                        args.append(f"{key}={repr(step['args'][key])}")
            args = ", ".join(args)
            return f"{'step_io = ' if primary else ''}{step['operator']}({step_input}, {args})"

        with open(recipe_file_path, encoding="UTF-8") as f:
            self.recipe = tomllib.loads(f.read())
        self.function = recipe_parser(self.recipe)

    def __call__(self, input_file, output_file):
        return self.function(input_file, output_file)


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

    def step_parser(step) -> str:
        if "input" in step:
            if type(step["input"]) == dict:
                logging.debug(f"Recursing into input: {step['input']}")
                step_input = step_parser(step["input"])()
            else:
                step_input = repr(step["input"])
        else:
            step_input = "step_io"
        args = []
        if "args" in step:
            for key in step["args"].keys():
                if type(step["args"][key]) == dict:
                    logging.debug(f"Recursing into args: {step['args']}")
                    args.append(f"{key}={step_parser(step['args'][key])()}")
                elif step["args"][key] == "MAGIC_OUTPUT_PATH":
                    args.append(f"{key}=output_file_path")
                else:
                    args.append(f"{key}={repr(step['args'][key])}")
        args = ", ".join(args)

        def step_function(step_io):
            # TODO remove use of exec
            exec(f"{step['operator']}({step_input}, {args})")

        return step_function

    with open(recipe_file, encoding="UTF-8") as f:
        recipe = tomllib.loads(f.read())

    import CSET.operators as operators

    step_io = input_file
    for step in recipe["steps"]:
        step_io = step_parser(step)(step_io)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run an operator chain.")
    parser.add_argument("input_file", type=Path, help="input file to read")
    parser.add_argument("output_file", type=Path, help="output file to write")
    parser.add_argument(
        "recipe_file", type=Path, help="recipe file to execute", default="/dev/null"
    )
    parser.add_argument(
        "--verbose", "-v", action="count", default=0, help="increase output verbosity"
    )
    args = parser.parse_args()
    if args.verbose >= 2:
        logging.basicConfig(level=logging.DEBUG)
    elif args.verbose >= 1:
        logging.basicConfig(level=logging.INFO)
    # operator_task = Recipe(args.recipe_file)
    # operator_task(args.input_file, args.output_file)
    execute_recipe(args.recipe_file, args.input_file, args.output_file)
