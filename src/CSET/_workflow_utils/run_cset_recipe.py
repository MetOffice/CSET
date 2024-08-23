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
    try:
        p = subprocess.run(
            ("cset", "recipe-id", "--recipe", file),
            capture_output=True,
            check=True,
            env=env,
        )
    except subprocess.CalledProcessError as err:
        logging.exception(
            "cset recipe-id exited with non-zero code %s.\nstdout: %s\nstderr: %s",
            err.returncode,
            # Presume that subprocesses have the same IO encoding as this one.
            # Honestly, on all our supported platforms this will be "utf-8".
            err.stdout.decode(sys.stdout.encoding),
            err.stderr.decode(sys.stderr.encoding),
        )
        raise
    id = p.stdout.decode(sys.stdout.encoding).strip()
    model_number = os.environ["MODEL_NUMBER"]
    return f"m{model_number}_{id}"


def output_directory():
    """Get the plot output directory for the recipe."""
    share_directory = os.environ["CYLC_WORKFLOW_SHARE_DIR"]
    cycle_point = os.environ["CYLC_TASK_CYCLE_POINT"]
    return f"{share_directory}/web/plots/{recipe_id()}_{cycle_point}"


def data_directory():
    """Get the input data directory for the cycle."""
    share_directory = os.environ["CYLC_WORKFLOW_SHARE_DIR"]
    cycle_point = os.environ["CYLC_TASK_CYCLE_POINT"]
    model_number = os.environ["MODEL_NUMBER"]
    return f"{share_directory}/cycle/{cycle_point}/data/{model_number}"


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


def run_recipe_steps():
    """Process data and produce output plots."""
    try:
        command = (
            "cset",
            "-v",
            "bake",
            f"--recipe={recipe_file()}",
            f"--input-dir={data_directory()}",
            f"--output-dir={output_directory()}",
            f"--style-file={os.getenv('COLORBAR_FILE', '')}",
            f"--plot-resolution={os.getenv('PLOT_RESOLUTION', '')}",
        )
        logging.info("Running %s", " ".join(command))
        subprocess.run(command, check=True, env=subprocess_env(), capture_output=True)
    except subprocess.CalledProcessError as err:
        logging.exception(
            "cset bake exited with non-zero code %s.\nstdout: %s\nstderr: %s",
            err.returncode,
            err.stdout.decode(sys.stdout.encoding),
            err.stderr.decode(sys.stderr.encoding),
        )
        raise
    create_diagnostic_archive(output_directory())


def run():
    """Run workflow script."""
    run_recipe_steps()
