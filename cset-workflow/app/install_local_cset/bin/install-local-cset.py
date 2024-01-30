#! /usr/bin/env python3

"""Install development version of CSET into the conda environment if needed."""

import logging
import os
import subprocess
import tempfile

logging.basicConfig(level=logging.INFO)

if os.getenv("CSET_ENV_USE_LOCAL_CSET") == "True":
    local_cset_path = os.getenv("CSET_LOCAL_CSET_PATH")
    logging.info("Using local CSET from %s", local_cset_path)
    if local_cset_path.endswith(".whl"):
        logging.info("Wheel file, installing directly.")
        subprocess.run(
            f"pip install -v --progress-bar off {local_cset_path}",
            check=True,
            shell=True,
        )
    else:
        with tempfile.TemporaryDirectory() as tempdir:
            # Copy project to temporary location to avoid permissions issues. I
            # am using subprocess with shell=True here so variables like $HOME
            # in the path are resolved.
            subprocess.run(
                f"cp -r {local_cset_path} {tempdir}",
                check=True,
                shell=True,
            )
            # Build and install into python environment.
            subprocess.run(
                ("pip", "install", "-v", "--progress-bar", "off", f"{tempdir}/CSET"),
                check=True,
            )

result = subprocess.run(("cset", "--version"), check=True, capture_output=True)
print(f"Using CSET version: {result.stdout}")
