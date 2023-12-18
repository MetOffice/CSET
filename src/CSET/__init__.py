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

"""CSET: Convective and turbulence Scale Evaluation Tool."""

import argparse
import logging
import sys
from importlib.metadata import version
from pathlib import Path


def main():
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        prog="cset", description="Convective Scale Evaluation Tool"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="increase output verbosity, may be specified multiple times",
    )
    parser.add_argument(
        "--version", action="version", version=f"CSET v{version('CSET')}"
    )

    # https://docs.python.org/3/library/argparse.html#sub-commands
    subparsers = parser.add_subparsers(title="subcommands", dest="subparser")

    # Run operator chain
    parser_bake = subparsers.add_parser("bake", help="run a recipe file")
    parser_bake.add_argument(
        "-r",
        "--recipe",
        type=Path,
        required=True,
        help="recipe file to read",
    )
    parser_bake.add_argument(
        "-i",
        "--input-dir",
        type=Path,
        required=True,
        help="directory containing input data",
    )
    parser_bake.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        required=True,
        help="directory to write output",
    )
    parser_bake.set_defaults(func=_bake_command)

    parser_graph = subparsers.add_parser("graph", help="visualise a recipe file")
    parser_graph.add_argument(
        "-r",
        "--recipe",
        type=Path,
        required=True,
        help="recipe file to read",
    )
    parser_graph.add_argument(
        "-o",
        "--output-path",
        type=Path,
        nargs="?",
        help="file in which to save the graph image, otherwise uses a temporary file. When specified the file is not automatically opened",
        default=None,
    )
    parser_graph.add_argument(
        "-d",
        "--details",
        action="store_true",
        help="include operator arguments in output",
    )
    parser_graph.set_defaults(func=_graph_command)

    parser_cookbook = subparsers.add_parser(
        "cookbook", help="unpack included recipes to a folder"
    )
    parser_cookbook.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        help="directory to save recipes. If omitted uses $PWD",
        default=Path.cwd(),
    )
    parser_cookbook.add_argument(
        "-l",
        "--list",
        action="store_true",
        help="list available recipes. Supplied recipes are detailed.",
    )
    parser_cookbook.add_argument(
        "recipe",
        type=str,
        nargs="?",
        help="recipe to output or detail. Omit for all.",
        default="",
    )
    parser_cookbook.set_defaults(func=_cookbook_command)

    args = parser.parse_args()

    logging.captureWarnings(True)

    # Logging verbosity
    if args.verbose >= 2:
        logging.basicConfig(level=logging.DEBUG)
    elif args.verbose >= 1:
        logging.basicConfig(level=logging.INFO)

    if args.subparser:
        try:
            args.func(args)
        except ValueError:
            parser.print_usage()
            sys.exit(2)
    else:
        parser.print_help()


def _bake_command(args):
    from CSET.operators import execute_recipe

    execute_recipe(args.recipe, args.input_dir, args.output_dir)


def _graph_command(args):
    from CSET.graph import save_graph

    save_graph(
        args.recipe,
        args.output_path,
        auto_open=not args.output_path,
        detailed=args.details,
    )


def _cookbook_command(args):
    from CSET.recipes import detail_recipe, list_available_recipes, unpack_recipes

    if args.list:
        if args.recipe:
            detail_recipe(args.recipe)
        else:
            list_available_recipes()
    else:
        unpack_recipes(args.output_dir, args.recipe)
