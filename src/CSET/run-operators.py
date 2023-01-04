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

parser = argparse.ArgumentParser(description="Run an operator chain.")
parser.add_argument("input_file", help="input file to read")
parser.add_argument("output_file", help="output file to write")
parser.add_argument("--stash", help="STASH code to filter by", default="m01s03i236")
parser.add_argument("--varname", help="variable name to filter by", default="test")
args = parser.parse_args()

from CSET.operators import generate_constraints, read, write, filters

# Hardcoded task chain to extract instantaneous air temperature.
stash_constraint = generate_constraints.generate_stash_constraints(args.stash)
var_constraint = generate_constraints.generate_var_constraints(args.varname)
cubes = read.read_cubes(args.input_file, stash_constraint)
cube = filters.filter_cubes(cubes, args.stash, ())
write.write_cube_to_nc(cube, args.output_file)
