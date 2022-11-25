#! /usr/bin/env python3
"""
Script to chain together individual operators.

Currently it is hard coded, but in future it will take an argument specifying a
config file describing what operators to run in what order.
"""

import sys
from CSET.operators import read, write, filters

# First argument is input file name, second is output file name.
input_file = sys.argv[1]
output_file = sys.argv[2]

# Hardcoded task chain
cubes = read.read_cubes(input_file)
cube = filters.filter_cubes(cubes, "stash_code")
write.write_cube_to_nc(cube, output_file)
