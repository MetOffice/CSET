#!/usr/bin/env python3

"""Efficiently bake many recipes."""

import functools
import logging
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from CSET._common import format_duration, parse_recipe, setup_logging
from CSET.operators import execute_recipe

logger = logging.getLogger(__name__)


class RecipeError(RuntimeError):
    """Recipe failed to bake."""


class ProcessLoggingContext:
    """Write this process's logs to a separate file.

    Log messages are filtered out from others.
    """

    def __init__(self, logger: logging.Logger, log_file: Path):
        self.logger = logger
        self.handler = logging.FileHandler(log_file)

        # Construct some filtering functions.
        process_id = os.getpid()

        def keep_process_logs(record: logging.LogRecord) -> bool:
            return record.process == process_id

        def discard_process_logs(record: logging.LogRecord) -> bool:
            return record.process != process_id

        self.handler.addFilter(keep_process_logs)
        self.filter = discard_process_logs

    def __enter__(self):
        """Attach handler and filter when entering the context."""
        # Add filter for this process's log messages to existing handlers.
        for handler in self.logger.handlers:
            handler.addFilter(self.filter)
        # Add a handler without the filter.
        self.logger.addHandler(self.handler)

    def __exit__(self, exc_type, exc_value, traceback):
        """Remove handler and filter and clean up when leaving the context."""
        self.logger.removeHandler(self.handler)
        # Remove filter from other handlers.
        for handler in self.logger.handlers:
            handler.removeFilter(self.filter)
        self.handler.close()


def bake_recipe(
    recipe: Path,
    cycle_output_dir: Path,
    log_dir: Path,
    style_file: Path,
    plot_resolution: int,
    skip_write: bool,
):
    """Bake a single recipe."""
    recipe_name = recipe.name.removesuffix(".yaml")

    # Put together path to output dir from nice name for recipe.
    output_dir = cycle_output_dir / recipe_name

    # Log this recipe's logs to a separate file.
    log_file = log_dir / f"{recipe_name}.log"
    root_logger = logging.getLogger()
    with ProcessLoggingContext(logger=root_logger, log_file=log_file):
        # Log the equivalent bake command for easy rerunning.
        recipe_summary = (
            f"Baking recipe {recipe_name}\n"
            "Equivalent bake command:\n"
            "cset -vv bake \\\n"
            f"    --recipe='{recipe}' \\\n"
            f"    --output-dir='{output_dir}' \\\n"
            f"    --style-file='{style_file}' \\\n"
            f"    --plot_resolution={plot_resolution}"
            f"{' \\\n    --skip-write' if skip_write else ''}"
        )
        logger.info(recipe_summary)
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
            logger.exception(
                "An unhandled exception occurred:\n%s",
                err,
                exc_info=True,
                stack_info=True,
            )
            raise RecipeError(
                f"Recipe {recipe_name} failed to bake. See {log_file}"
            ) from err
        duration = time.time() - start_time
        logger.info("Recipe baked in %s.", format_duration(duration))


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

    # Find recipes to bake.
    recipes = list(filter(lambda p: p.is_file(), recipe_dir.glob("*.yaml")))
    num_recipes = len(recipes)
    if num_recipes:
        logger.info("Baking %s recipes...", num_recipes)
    else:
        logger.warning("No recipes to bake in %s", recipe_dir)
        return

    # Fill in constant arguments. (All but recipe.)
    partial_bake = functools.partial(
        bake_recipe,
        cycle_output_dir=cycle_output_dir,
        log_dir=log_dir,
        style_file=style_file,
        plot_resolution=plot_resolution,
        skip_write=skip_write,
    )

    # Get number of usable CPUs.
    max_parallelism = len(os.sched_getaffinity(0))

    number_length = len(str(num_recipes))  # For formatting.
    num_baked = 0
    num_failed = 0

    # Bake the recipes in parallel.
    with ProcessPoolExecutor(max_workers=max_parallelism) as pool:
        futures = [pool.submit(partial_bake, recipe) for recipe in recipes]
        for future in as_completed(futures):
            num_baked += 1
            try:
                future.result()
                logging.info(f"{num_baked: {number_length}}/{num_recipes}")
            except RecipeError as err:
                num_failed += 1
                logger.error(err)
    logger.info("Baking complete!")
    if num_failed:
        logger.warning("%s/%s recipes failed to bake.", num_failed, num_recipes)


if __name__ == "__main__":
    traybake()
