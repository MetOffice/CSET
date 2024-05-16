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

"""Subpackage contains all of CSET's operators."""

import inspect
import json
import logging
import os
import warnings
from pathlib import Path
from typing import Union

from iris import FUTURE

# Import operators here so they are exported for use by recipes.
import CSET.operators
from CSET._common import parse_recipe
from CSET.operators import (
    aggregate,
    collapse,
    constraints,
    convection,
    filters,
    misc,
    plot,
    read,
    regrid,
    write,
)

# Exported operators & functions to use elsewhere.
__all__ = [
    "aggregate",
    "collapse",
    "constraints",
    "convection",
    "execute_recipe_parallel",
    "execute_recipe_collate",
    "filters",
    "get_operator",
    "misc",
    "plot",
    "read",
    "regrid",
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
    metadata.pop("parallel", None)
    metadata.pop("steps", None)
    metadata.pop("collate", None)
    metadata.pop("post-steps", None)
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
        return operator(step_input, **kwargs)
    else:
        return operator(**kwargs)


def _run_steps(recipe, steps, step_input, output_directory: Path, style_file: Path):
    """Execute the steps in a recipe."""
    original_working_directory = Path.cwd()
    os.chdir(output_directory)
    try:
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
        _write_metadata(recipe)
        # Execute the recipe.
        for step in steps:
            step_input = _step_parser(step, step_input)
        logging.info("Recipe output:\n%s", step_input)
    finally:
        os.chdir(original_working_directory)


def execute_recipe_parallel(
    recipe_yaml: Union[Path, str],
    input_directory: Path,
    output_directory: Path,
    recipe_variables: dict = None,
    style_file: Path = None,
) -> None:
    """Parse and executes the parallel steps from a recipe file.

    Parameters
    ----------
    recipe_yaml: Path or str
        Path to a file containing, or string of, a recipe's YAML describing the
        operators that need running. If a Path is provided it is opened and
        read.
    input_file: Path
        Pathlike to netCDF (or something else that iris read) file to be used as
        input.
    output_directory: Path
        Pathlike indicating desired location of output.
    recipe_variables: dict
        Dictionary of variables for the recipe.

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
    if recipe_variables is None:
        recipe_variables = {}
    recipe = parse_recipe(recipe_yaml, recipe_variables)
    step_input = Path(input_directory).absolute()
    # Create output directory, and an inter-cycle intermediate directory.
    try:
        (output_directory / "intermediate").mkdir(parents=True, exist_ok=True)
    except (FileExistsError, NotADirectoryError) as err:
        logging.error("Output directory is a file. %s", output_directory)
        raise err
    # If parallel doesn't exist try steps.
    try:
        steps = recipe["parallel"]
    except KeyError:
        if "steps" in recipe:
            warnings.warn(
                "'steps' recipe key is deprecated. Use 'parallel' instead.",
                DeprecationWarning,
                stacklevel=1,
            )
        steps = recipe["steps"]
    _run_steps(recipe, steps, step_input, output_directory, style_file)


def execute_recipe_collate(
    recipe_yaml: Union[Path, str],
    output_directory: Path,
    recipe_variables: dict = None,
    style_file: Path = None,
) -> None:
    """Parse and execute the collation steps from a recipe file.

    Parameters
    ----------
    recipe_yaml: Path or str
        Path to a file containing, or string of, a recipe's YAML describing the
        operators that need running. If a Path is provided it is opened and
        read.
    output_directory: Path
        Pathlike indicating desired location of output. Must already exist.
    recipe_variables: dict
        Dictionary of variables for the recipe.

    Raises
    ------
    ValueError
        The recipe is not well formed.
    TypeError
        The provided recipe is not a stream or Path.
    """
    if recipe_variables is None:
        recipe_variables = {}
    output_directory = Path(output_directory).resolve()
    assert output_directory.is_dir()
    recipe = parse_recipe(recipe_yaml, recipe_variables)
    # If collate doesn't exist try post-steps, else treat it as having no steps.
    try:
        steps = recipe["collate"]
    except KeyError:
        if "post-steps" in recipe:
            warnings.warn(
                "'post-steps' recipe key is deprecated. Use 'collate' instead.",
                DeprecationWarning,
                stacklevel=1,
            )
        steps = recipe.get("post-steps", tuple())
    _run_steps(recipe, steps, output_directory, output_directory, style_file)
