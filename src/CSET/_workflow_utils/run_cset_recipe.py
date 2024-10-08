#! /usr/bin/env python3

"""Run a recipe with the CSET CLI."""

import logging
import os
import subprocess
import sys
import zipfile
from pathlib import Path

logging.basicConfig(
    level=os.getenv("LOGLEVEL", "INFO"), format="%(asctime)s %(levelname)s %(message)s"
)


def subprocess_env():
    """Create a dictionary of amended environment variables for subprocess."""
    env_mapping = dict(os.environ)
    cycle_point = env_mapping["CYLC_TASK_CYCLE_POINT"]
    # Add validity time based on cycle point.
    env_mapping["CSET_ADDOPTS"] = (
        f"{os.getenv('CSET_ADDOPTS', '')} --VALIDITY_TIME={cycle_point}"
    )
    return env_mapping


def recipe_file() -> str:
    """Write the recipe file to disk and return its path as a string."""
    # Ready recipe file to disk.
    cset_recipe = os.environ["CSET_RECIPE_NAME"]
    subprocess.run(("cset", "-v", "cookbook", cset_recipe), check=True)
    # Debug check that recipe has been retrieved.
    assert Path(cset_recipe).is_file()
    return cset_recipe


def recipe_id():
    """Get the ID for the recipe."""
    file = recipe_file()
    env = subprocess_env()
    p = subprocess.run(
        ("cset", "recipe-id", "--recipe", file),
        capture_output=True,
        env=env,
    )
    # Explicitly check return code as otherwise we can't get the error message.
    if p.returncode != 0:
        logging.error(
            "cset recipe-id returned non-zero exit code.\n%s",
            # Presume that subprocesses have the same IO encoding as this one.
            # Honestly, on all our supported platforms this will be "utf-8".
            p.stderr.decode(sys.stderr.encoding),
        )
        p.check_returncode()
    id = p.stdout.decode(sys.stdout.encoding).strip()
    return id


def output_directory():
    """Get the plot output directory for the recipe."""
    share_directory = os.environ["CYLC_WORKFLOW_SHARE_DIR"]
    return f"{share_directory}/web/plots/{recipe_id()}"


def data_directory():
    """Get the input data directory for the cycle."""
    share_directory = os.environ["CYLC_WORKFLOW_SHARE_DIR"]
    cycle_point = os.environ["CYLC_TASK_CYCLE_POINT"]
    return f"{share_directory}/cycle/{cycle_point}/data"


def create_diagnostic_archive(output_directory):
    """Create archive for easy download of plots and data."""
    output_directory = Path(output_directory)
    archive_path = output_directory / "diagnostic.zip"
    with zipfile.ZipFile(
        archive_path, "w", compression=zipfile.ZIP_DEFLATED
    ) as archive:
        for file in output_directory.rglob("*"):
            # Check the archive doesn't add itself.
            if not file.samefile(archive_path):
                archive.write(file, arcname=file.relative_to(output_directory))


# Not covered by tests as will soon be removed in #765.
def parallel():  # pragma: no cover
    """Process raw data in parallel."""
    logging.info("Pre-processing data into intermediate form.")
    try:
        subprocess.run(
            (
                "cset",
                "-v",
                "bake",
                f"--recipe={recipe_file()}",
                f"--input-dir={data_directory()}",
                f"--output-dir={output_directory()}",
                f"--style-file={os.getenv('COLORBAR_FILE', '')}",
                f"--plot-resolution={os.getenv('PLOT_RESOLUTION', '')}",
                "--parallel-only",
            ),
            check=True,
            env=subprocess_env(),
        )
    except subprocess.CalledProcessError:
        logging.error("cset bake exited non-zero while processing.")
        raise


# Not covered by tests as will soon be removed in #765.
def collate():  # pragma: no cover
    """Collate processed data together and produce output plot.

    If the intermediate directory doesn't exist then we are running a simple
    non-parallelised recipe, and we need to run cset bake to process the data
    and produce any plots. So we actually get some usage out of it, we are using
    the non-restricted form of bake, so it runs both the processing and
    collation steps.
    """
    try:
        logging.info("Collating intermediate data and saving output.")
        subprocess.run(
            (
                "cset",
                "-v",
                "bake",
                f"--recipe={recipe_file()}",
                f"--output-dir={output_directory()}",
                f"--style-file={os.getenv('COLORBAR_FILE', '')}",
                f"--plot-resolution={os.getenv('PLOT_RESOLUTION', '')}",
                "--collate-only",
            ),
            check=True,
            env=subprocess_env(),
        )
    except subprocess.CalledProcessError:
        logging.error("cset bake exited non-zero while collating.")
        raise
    create_diagnostic_archive(output_directory())


def run():
    """Run workflow script."""
    # Check if we are running in parallel or collate mode.
    bake_mode = os.getenv("CSET_BAKE_MODE")
    if bake_mode == "parallel":
        parallel()
    elif bake_mode == "collate":
        collate()
