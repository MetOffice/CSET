#! /usr/bin/env python3

# Copyright 2022 Met Office and contributors.
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

It takes the input file as its first argument, and the output file as the second
argument. The third argument is stash name (currently "m01s03i236", and
optional) and forth argument is variable name (currently "test", and optional)
to constrain loading of model data.
"""

import sys
from CSET.operators import generate_constraints, read, write, filters

input_file = sys.argv[1]
output_file = sys.argv[2]
try:
    stash = sys.argv[3]
except IndexError:
    stash = "m01s03i236"
try:
    varname = sys.argv[4]
except IndexError:
    varname = "test"

# Hardcoded task chain to extract instantaneous air temperature.
stash_constraint = generate_constraints.generate_stash_constraints(stash)
var_constraint = generate_constraints.generate_var_constraints(varname)
cubes = read.read_cubes(input_file, stash_constraint)
cube = filters.filter_cubes(cubes, "m01s03i236", ())
write.write_cube_to_nc(cube, output_file)
