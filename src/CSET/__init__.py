# © Crown copyright, Met Office (2022-2024) and CSET contributors.
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
import shlex
import sys
from importlib.metadata import version
from pathlib import Path

from CSET._common import ArgumentError


def main(raw_cli_args: list[str] = sys.argv):
    """CLI entrypoint.

    Handles argument parsing, setting up logging, top level error capturing,
    and execution of the desired subcommand.
    """
    # Read arguments from the command line and CSET_ADDOPTS environment variable
    # into an args object.
    parser = setup_argument_parser()
    cli_args = raw_cli_args[1:] + shlex.split(os.getenv("CSET_ADDOPTS", ""))
    args, unparsed_args = parser.parse_known_args(cli_args)

    setup_logging(args.verbose)

    # Down here so runs after logging is setup.
    logging.debug("CLI Arguments: %s", cli_args)

    if args.subparser is None:
        print("Please choose a command.", file=sys.stderr)
        parser.print_usage()
        sys.exit(127)

    try:
        # Execute the specified subcommand.
        args.func(args, unparsed_args)
    except ArgumentError as err:
        # Error message for when needed template variables are missing.
        print(err, file=sys.stderr)
        parser.print_usage()
        sys.exit(127)
    except Exception as err:
        # Provide slightly nicer error messages for unhandled exceptions.
        print(err, file=sys.stderr)
        # Display the time and full traceback when debug logging.
        logging.debug("An unhandled exception occurred.")
        if logging.root.isEnabledFor(logging.DEBUG):
            raise
        sys.exit(1)


def setup_argument_parser() -> argparse.ArgumentParser:
    """Create argument parser for CSET CLI."""
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
        type=str,
        action="extend",
        required=True,
        nargs="+",
        help="directories containing input data. May contain wildcards",
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
    parser_bake.add_argument(
        "-s", "--style-file", type=Path, help="colour bar definition to use"
    )
    parser_bake.add_argument(
        "--plot-resolution", type=int, help="plotting resolution in dpi"
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

    return parser


def setup_logging(verbosity: int):
    """Configure logging level, format and output stream.

    Level is based on verbose argument and the LOGLEVEL environment variable.
    """
    logging.captureWarnings(True)

    # Calculate logging level.
    # Level from CLI flags.
    if verbosity >= 2:
        cli_loglevel = logging.DEBUG
    elif verbosity == 1:
        cli_loglevel = logging.INFO
    else:
        cli_loglevel = logging.WARNING

    # Level from $LOGLEVEL environment variable.
    try:
        name_to_level = logging.getLevelNamesMapping()
    except AttributeError:
        # logging.getLevelNamesMapping() is python 3.11 or newer. Using
        # implementation detail for older versions.
        name_to_level = logging._nameToLevel
    env_loglevel = name_to_level.get(os.getenv("LOGLEVEL"), logging.ERROR)

    # Logging verbosity is the most verbose of CLI and environment setting.
    loglevel = min(cli_loglevel, env_loglevel)

    # Configure the root logger.
    logger = logging.getLogger()
    # Set logging level.
    logger.setLevel(loglevel)

    # Hide matplotlib's many font messages.
    class NoFontMessageFilter(logging.Filter):
        def filter(self, record):
            return not record.getMessage().startswith("findfont:")

    logging.getLogger("matplotlib.font_manager").addFilter(NoFontMessageFilter())

    stderr_log = logging.StreamHandler()
    stderr_log.setFormatter(
        logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
    )
    logger.addHandler(stderr_log)


def _bake_command(args, unparsed_args):
    from CSET._common import parse_variable_options
    from CSET.operators import execute_recipe

    recipe_variables = parse_variable_options(unparsed_args)
    execute_recipe(
        args.recipe,
        args.input_dir,
        args.output_dir,
        recipe_variables,
        args.style_file,
        args.plot_resolution,
    )


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
