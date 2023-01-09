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

"""Script to chain together individual operators."""

import argparse
import logging
from pathlib import Path
from ._internal import execute_recipe


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

execute_recipe(args.recipe_file, args.input_file, args.output_file)
