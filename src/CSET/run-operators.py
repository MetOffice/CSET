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
from pathlib import Path
import sys

try:
    import tomllib
except ImportError:
    # tomllib is in standard library from 3.11.
    import tomli as tomllib


class Recipe:
    def __init__(self, recipe_file_path: Path) -> None:
        def recipe_parser(recipe) -> callable:
            recipe_code = []
            for step in recipe["steps"]:
                recipe_code.append(step_parser(step, primary=True))
            recipe_code = "\n".join(recipe_code)
            print(
                "───┤ Generated Code ├───────────────────────────────────────"
                + "───────────────────\n\n"
                + recipe_code
                + "\n\n──────────────────────────────────────────────────────"
                + "─────────────────────────"
            )

            def operator_task(input_file_path, output_file_path):
                import CSET.operators as operators

                step_io = input_file_path
                exec(recipe_code)

            return operator_task

        def step_parser(step, primary=False) -> str:
            args = ""
            if "args" in step:
                args_string = []
                for key in step["args"].keys():
                    if type(step["args"][key]) == dict:
                        args_string.append(
                            f"{key} = {(step_parser(step['args'][key]))}"
                        )
                    elif step["args"][key] == "MAGIC_OUTPUT_PATH":
                        args_string.append(f"{key} = output_file_path")
                    else:
                        args_string.append(f"{key} = {repr(step['args'][key])}")
                args = ", ".join(args_string)
            if "input" in step:
                if type(step["input"]) == dict:
                    step_input = repr(step_parser(step["input"]))
                else:
                    step_input = repr(step["input"])
            else:
                step_input = "step_io"
            if primary:
                output_variable = "step_io = "
            else:
                output_variable = ""
            return f"{output_variable}{step['operator']}({step_input}, {args})"

        with open(recipe_file_path, encoding="UTF-8") as f:
            self.recipe = tomllib.loads(f.read())
        self.function = recipe_parser(self.recipe)

    def __call__(self, input_file, output_file):
        return self.function(input_file, output_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run an operator chain.")
    parser.add_argument("input_file", type=Path, help="input file to read")
    parser.add_argument("output_file", type=Path, help="output file to write")
    parser.add_argument(
        "recipe", type=Path, help="recipe file to execute", default="/dev/null"
    )
    args = parser.parse_args()

    operator_task = Recipe(args.recipe)
    operator_task(args.input_file, args.output_file)
