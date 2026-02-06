#!/usr/bin/env python3

"""Efficiently bake many recipes."""

import functools
import logging
import os
import sys
import time
from pathlib import Path

from CSET._common import format_duration, parse_recipe, setup_logging
from CSET.operators import execute_recipe

logger = logging.getLogger(__name__)


def bake_recipe(
    recipe: Path,
    cycle_output_dir: Path,
    log_dir: Path,
    style_file: Path,
    plot_resolution: int,
    skip_write: bool,
):
    """Bake a single recipe. Returns whether it succeeded."""
    recipe_name = recipe.name.removesuffix(".yaml")

    # Put together path to output dir from nice name for recipe.
    output_dir = cycle_output_dir / recipe_name

    # Make a recipe-specific logger.
    log_file = log_dir / f"{recipe_name}.log"
    recipe_logger = logging.getLogger(f"{__name__}.recipe.{recipe_name}")
    recipe_logger.propagate = False
    file_handler = logging.FileHandler(log_file)
    recipe_logger.addHandler(file_handler)

    # Log the equivalent bake command for easy rerunning.
    recipe_summary = f"""Baking recipe:
Recipe:\t{recipe}
Output:\t{output_dir}
Equivalent bake command:
cset -vv bake --recipe='{recipe}' --output-dir='{output_dir}' --style-file='{style_file}' --plot_resolution={plot_resolution}{" --skip-write" if skip_write else ""}
"""
    recipe_logger.info(recipe_summary)
    start_time = time.time()

    # Bake recipe.
    try:
        parsed_recipe = parse_recipe(recipe)
        execute_recipe(
            recipe=parsed_recipe,
            output_directory=output_dir,
            style_file=style_file,
            plot_resolution=plot_resolution,
            skip_write=skip_write,
        )
    except Exception as err:
        recipe_logger.exception(
            "An unhandled exception occurred:\n%s",
            str(err),
            exc_info=True,
            stack_info=True,
        )
        logger.error("Recipe %s failed to bake. See %s", recipe_name, log_file)
    duration = time.time() - start_time
    recipe_logger.info("Recipe baked in %s.", format_duration(duration))


def traybake():
    """Bake many recipes."""
    # Force DEBUG logging on retries.
    if int(os.environ["CYLC_TASK_SUBMIT_NUMBER"]) > 1:
        setup_logging(2)
    else:
        setup_logging(1)

    # Load in information from environment.
    log_dir = Path(os.environ["CYLC_TASK_LOG_DIR"])
    cycle_point = os.environ["CYLC_TASK_CYCLE_POINT"]
    share_dir = os.environ["CYLC_WORKFLOW_SHARE_DIR"]
    agg = bool(os.getenv("DO_CASE_AGGREGATION", False))
    recipe_dir = Path(
        f"{share_dir}/cycle/{cycle_point}/{'aggregation_' if agg else ''}recipes"
    )
    cycle_output_dir = Path(f"{share_dir}/web/plots/{cycle_point}")

    # Baking configuration.
    style_file = Path(f"{share_dir}/style.json")
    plot_resolution = int(os.getenv("PLOT_RESOLUTION", 72))
    skip_write = bool(os.getenv("SKIP_WRITE", False))

    # TODO: Replace with os.process_cpu_count once python 3.13 is our minimum.
    # max_parallelism = len(os.sched_getaffinity(0))

    recipes = list(filter(lambda p: p.is_file(), recipe_dir.glob("*.yaml")))
    if len(recipes):
        logger.info("Baking %s recipes...", len(recipes))
    else:
        logger.warning("No recipes to bake in %s", recipe_dir)
        sys.exit(0)

    # Fill in all the constant arguments. (Everything but recipe.)
    partial_bake = functools.partial(
        bake_recipe,
        cycle_output_dir=cycle_output_dir,
        log_dir=log_dir,
        style_file=style_file,
        plot_resolution=plot_resolution,
        skip_write=skip_write,
    )

    # TODO: Use a parallel executor.
    for recipe in recipes:
        partial_bake(recipe)


if __name__ == "__main__":
    traybake()
