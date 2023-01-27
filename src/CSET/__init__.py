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
CSET: Convective Scale Evaluation Tool
"""

import argparse
import logging
from pathlib import Path


def main():
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        prog="cset", description="Convective Scale Evaluation Tool."
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="increase output verbosity, may be specified multiple times",
    )
    # https://docs.python.org/3/library/argparse.html#sub-commands
    subparsers = parser.add_subparsers(title="subcommands")
    parser_operators = subparsers.add_parser(
        "operators", help="run a chain of operators"
    )
    parser_operators.add_argument("input_file", type=Path, help="input file to read")
    parser_operators.add_argument("output_file", type=Path, help="output file to write")
    parser_operators.add_argument(
        "recipe_file", type=Path, help="recipe file to execute"
    )
    parser_operators.set_defaults(func=run_operators)
    args = parser.parse_args()
    # Logging verbosity
    if args.verbose >= 2:
        logging.basicConfig(level=logging.DEBUG)
    elif args.verbose >= 1:
        logging.basicConfig(level=logging.INFO)
    args.func(args)


def run_operators(args):
    from .operators._internal import execute_recipe

    execute_recipe(args.recipe_file, args.input_file, args.output_file)
