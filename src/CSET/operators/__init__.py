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

"""Subpackage contains all of CSET's operators."""

import inspect
import json
import logging
import os
from pathlib import Path
from typing import Union

from iris import FUTURE

# Import operators here so they are exported for use by recipes.
import CSET.operators
from CSET._common import parse_recipe
from CSET.operators import (
    ageofair,
    aggregate,
    collapse,
    constraints,
    convection,
    ensembles,
    filters,
    mesoscale,
    misc,
    plot,
    read,
    regrid,
    transect,
    write,
)

# Exported operators & functions to use elsewhere.
__all__ = [
    "ageofair",
    "aggregate",
    "collapse",
    "constraints",
    "convection",
    "ensembles",
    "execute_recipe",
    "filters",
    "get_operator",
    "mesoscale",
    "misc",
    "plot",
    "read",
    "regrid",
    "transect",
    "write",
]

# Stop iris giving a warning whenever it loads something.
FUTURE.datum_support = True
# Stop iris giving a warning whenever it saves something.
FUTURE.save_split_attrs = True


def get_operator(name: str):
    """Get an operator by its name.

    Parameters
    ----------
    name: str
        The name of the desired operator.

    Returns
    -------
    function
        The named operator.

    Raises
    ------
    ValueError
        If name is not an operator.

    Examples
    --------
    >>> CSET.operators.get_operator("read.read_cubes")
    <function read_cubes at 0x7fcf9353c8b0>
    """
    logging.debug("get_operator(%s)", name)
    try:
        name_sections = name.split(".")
        operator = CSET.operators
        for section in name_sections:
            operator = getattr(operator, section)
        if callable(operator):
            return operator
        else:
            raise AttributeError
    except (AttributeError, TypeError) as err:
        raise ValueError(f"Unknown operator: {name}") from err


def _write_metadata(recipe: dict):
    """Write a meta.json file in the CWD."""
    # TODO: Investigate whether we might be better served by an SQLite database.
    metadata = recipe.copy()
    # Remove steps, as not needed, and might contain non-serialisable types.
    metadata.pop("steps", None)
    with open("meta.json", "wt", encoding="UTF-8") as fp:
        json.dump(metadata, fp)
    os.sync()
    # Stat directory to force NFS to synchronise metadata.
    os.stat(Path.cwd())


def _step_parser(step: dict, step_input: any) -> str:
    """Execute a recipe step, recursively executing any sub-steps."""
    logging.debug("Executing step: %s", step)
    kwargs = {}
    for key in step.keys():
        if key == "operator":
            operator = get_operator(step["operator"])
            logging.info("operator: %s", step["operator"])
        elif isinstance(step[key], dict) and "operator" in step[key]:
            logging.debug("Recursing into argument: %s", key)
            kwargs[key] = _step_parser(step[key], step_input)
        else:
            kwargs[key] = step[key]
    logging.debug("args: %s", kwargs)
    logging.debug("step_input: %s", step_input)
    # If first argument of operator is explicitly defined, use that rather
    # than step_input. This is known through introspection of the operator.
    first_arg = next(iter(inspect.signature(operator).parameters.keys()))
    logging.debug("first_arg: %s", first_arg)
    if first_arg not in kwargs:
        logging.debug("first_arg not in kwargs, using step_input.")
        return operator(step_input, **kwargs)
    else:
        logging.debug("first_arg in kwargs.")
        return operator(**kwargs)


def _run_steps(
    recipe,
    steps,
    step_input,
    output_directory: Path,
    style_file: Path = None,
    plot_resolution: int = None,
) -> None:
    """Execute the steps in a recipe."""
    original_working_directory = Path.cwd()
    try:
        os.chdir(output_directory)
        logger = logging.getLogger()
        diagnostic_log = logging.FileHandler(
            filename="CSET.log", mode="w", encoding="UTF-8"
        )
        diagnostic_log.addFilter(lambda record: record.levelno >= logging.INFO)
        diagnostic_log.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        )
        logger.addHandler(diagnostic_log)
        # Create metadata file used by some steps.
        if style_file:
            recipe["style_file_path"] = str(style_file)
        if plot_resolution:
            recipe["plot_resolution"] = plot_resolution
        _write_metadata(recipe)
        # Execute the recipe.
        for step in steps:
            step_input = _step_parser(step, step_input)
        logging.info("Recipe output:\n%s", step_input)
    finally:
        os.chdir(original_working_directory)


def execute_recipe(
    recipe_yaml: Union[Path, str],
    input_directory: Path,
    output_directory: Path,
    recipe_variables: dict = None,
    style_file: Path = None,
    plot_resolution: int = None,
) -> None:
    """Parse and executes the steps from a recipe file.

    Parameters
    ----------
    recipe_yaml: Path or str
        Path to a file containing, or string of, a recipe's YAML describing the
        operators that need running. If a Path is provided it is opened and
        read.
    input_directory: Path
        Pathlike to directory containing input files.
    output_directory: Path
        Pathlike indicating desired location of output.
    recipe_variables: dict, optional
        Dictionary of variables for the recipe.
    style_file: Path, optional
        Path to a style file.
    plot_resolution: int, optional
        Resolution of plots in dpi.

    Raises
    ------
    FileNotFoundError
        The recipe or input file cannot be found.
    FileExistsError
        The output directory as actually a file.
    ValueError
        The recipe is not well formed.
    TypeError
        The provided recipe is not a stream or Path.
    """
    recipe = parse_recipe(recipe_yaml, recipe_variables)
    step_input = Path(input_directory).absolute()
    # Create output directory.
    try:
        output_directory.mkdir(parents=True, exist_ok=True)
    except (FileExistsError, NotADirectoryError) as err:
        logging.error("Output directory is a file. %s", output_directory)
        raise err
    steps = recipe["steps"]
    _run_steps(recipe, steps, step_input, output_directory, style_file, plot_resolution)
