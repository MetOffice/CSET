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


def parse_recipe(recipe: str):
    """
    Parses the operator recipe and returns a function that runs the required
    operators.
    """
    if recipe is None:
        return hardcoded_recipe
    else:
        raise NotImplementedError


def hardcoded_recipe(input_file, output_file):
    """
    Hardcoded task chain to extract instantaneous air temperature.

    TODO: Replace with recipe file.
    """
    from CSET.operators import generate_constraints, read, write, filters

    stash = "m01s03i236"
    # varname = "test"

    stash_constraint = generate_constraints.generate_stash_constraints(stash)
    # var_constraint = generate_constraints.generate_var_constraints(varname)
    cubes = read.read_cubes(input_file, stash_constraint)
    cube = filters.filter_cubes(cubes, stash, ())
    write.write_cube_to_nc(cube, output_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run an operator chain.")
    parser.add_argument("input_file", type=Path, help="input file to read")
    parser.add_argument("output_file", type=Path, help="output file to write")
    parser.add_argument("recipe", type=Path, help="recipe file to execute")
    args = parser.parse_args()
    with open(args.recipe, encoding="UTF-8") as f:
        recipe = f.read()
    operator_task = parse_recipe(recipe)
    operator_task(args.input_file, args.output_file)
