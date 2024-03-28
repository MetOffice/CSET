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
import os
import sys
from importlib.metadata import version
from pathlib import Path

from CSET._common import ArgumentError


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
    parser_bake = subparsers.add_parser("bake", help="run steps from a recipe file")
    parser_bake.add_argument(
        "-i",
        "--input-dir",
        type=Path,
        help="directory containing input data",
    )
    parser_bake.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        required=True,
        help="directory to write output into",
    )
    parser_bake.add_argument(
        "-r",
        "--recipe",
        type=Path,
        required=True,
        help="recipe file to read",
    )
    bake_step_control = parser_bake.add_mutually_exclusive_group()
    bake_step_control.add_argument(
        "--pre-only", action="store_true", help="only run pre-processing steps"
    )
    bake_step_control.add_argument(
        "--post-only", action="store_true", help="only run post-processing steps"
    )
    parser_bake.set_defaults(func=_bake_command)

    parser_graph = subparsers.add_parser("graph", help="visualise a recipe file")
    parser_graph.add_argument(
        "-d",
        "--details",
        action="store_true",
        help="include operator arguments in output",
    )
    parser_graph.add_argument(
        "-o",
        "--output-path",
        type=Path,
        nargs="?",
        help="persistent file to save the graph. Otherwise the file is opened",
        default=None,
    )
    parser_graph.add_argument(
        "-r",
        "--recipe",
        type=Path,
        required=True,
        help="recipe file to read",
    )
    parser_graph.set_defaults(func=_graph_command)

    parser_cookbook = subparsers.add_parser(
        "cookbook", help="unpack included recipes to a folder"
    )
    parser_cookbook.add_argument(
        "-d",
        "--details",
        action="store_true",
        help="list available recipes. Supplied recipes are detailed",
    )
    parser_cookbook.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        help="directory to save recipes. If omitted uses $PWD",
        default=Path.cwd(),
    )
    parser_cookbook.add_argument(
        "recipe",
        type=str,
        nargs="?",
        help="recipe to output or detail",
        default="",
    )
    parser_cookbook.set_defaults(func=_cookbook_command)

    parser_recipe_id = subparsers.add_parser("recipe-id", help="get the ID of a recipe")
    parser_recipe_id.add_argument(
        "-r",
        "--recipe",
        type=Path,
        required=True,
        help="recipe file to read",
    )
    parser_recipe_id.set_defaults(func=_recipe_id_command)

    cli_args = sys.argv[1:] + os.getenv("CSET_ADDOPTS", "").split()
    args, unparsed_args = parser.parse_known_args(cli_args)

    # Setup logging.
    logging.captureWarnings(True)
    loglevel = calculate_loglevel(args)
    logger = logging.getLogger()
    logger.setLevel(min(loglevel, logging.INFO))
    stderr_log = logging.StreamHandler()
    stderr_log.addFilter(lambda record: record.levelno >= loglevel)
    stderr_log.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(stderr_log)

    if args.subparser is None:
        print("Please choose a command.", file=sys.stderr)
        parser.print_usage()
        sys.exit(127)

    try:
        # Execute the specified subcommand.
        args.func(args, unparsed_args)
    except ArgumentError as err:
        logging.error(err)
        parser.print_usage()
        sys.exit(3)


def calculate_loglevel(args) -> int:
    """Calculate the logging level to apply.

    Level is based on verbose argument and the LOGLEVEL environment variable.
    """
    try:
        name_to_level = logging.getLevelNamesMapping()
    except AttributeError:
        # logging.getLevelNamesMapping() is python 3.11 or newer. Using
        # implementation detail for older versions.
        name_to_level = logging._nameToLevel
    # Level from CLI flags.
    if args.verbose >= 2:
        loglevel = logging.DEBUG
    elif args.verbose == 1:
        loglevel = logging.INFO
    else:
        loglevel = logging.WARNING
    return min(
        loglevel,
        # Level from environment variable.
        name_to_level.get(os.getenv("LOGLEVEL"), logging.ERROR),
    )


def _bake_command(args, unparsed_args):
    from CSET._common import parse_variable_options
    from CSET.operators import execute_recipe_post_steps, execute_recipe_steps

    recipe_variables = parse_variable_options(unparsed_args)
    if not args.post_only:
        # Input dir is needed for pre-steps, but not post-steps.
        if not args.input_dir:
            raise ArgumentError("the following arguments are required: -i/--input-dir")
        execute_recipe_steps(
            args.recipe, args.input_dir, args.output_dir, recipe_variables
        )
    if not args.pre_only:
        execute_recipe_post_steps(args.recipe, args.output_dir, recipe_variables)


def _graph_command(args, unparsed_args):
    from CSET.graph import save_graph

    save_graph(
        args.recipe,
        args.output_path,
        auto_open=not args.output_path,
        detailed=args.details,
    )


def _cookbook_command(args, unparsed_args):
    from CSET.recipes import detail_recipe, list_available_recipes, unpack_recipe

    if args.recipe:
        if args.details:
            detail_recipe(args.recipe)
        else:
            try:
                unpack_recipe(args.output_dir, args.recipe)
            except FileNotFoundError:
                logging.error("Recipe %s does not exist.", args.recipe)
                sys.exit(1)
    else:
        list_available_recipes()


def _recipe_id_command(args, unparsed_args):
    from uuid import uuid4

    from CSET._common import parse_recipe, parse_variable_options, slugify

    recipe_variables = parse_variable_options(unparsed_args)
    recipe = parse_recipe(args.recipe, recipe_variables)
    try:
        recipe_id = slugify(recipe["title"])
    except KeyError:
        logging.warning("Recipe has no title; Falling back to random recipe_id.")
        recipe_id = str(uuid4())
    print(recipe_id)
