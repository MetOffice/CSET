#! /usr/bin/env python3

"""Install development version of CSET into the conda environment if needed."""

import logging
import os
import shutil
import subprocess
import sys
import tempfile

logging.basicConfig(
    level=os.getenv("LOGLEVEL", "INFO"), format="%(asctime)s %(levelname)s %(message)s"
)

if os.getenv("CSET_ENV_USE_LOCAL_CSET") == "True":
    with tempfile.TemporaryDirectory as cset_install_path:
        cset_source_path = os.path.expandvars(
            os.path.expanduser(os.getenv("CSET_LOCAL_CSET_PATH"))
        )
        logging.info("Using local CSET from %s", cset_source_path)

        # Directly install wheel files, or copy source folders.
        if cset_source_path.endswith(".whl"):
            logging.info("Wheel file, installing directly.")
            cset_install_path = cset_source_path
        else:
            # Copy project to temporary location to avoid permissions issues.
            shutil.copytree(cset_source_path, cset_install_path, dirs_exist_ok=True)

        # Build and install into python environment.
        subprocess.run(
            (
                "pip",
                "install",
                "--verbose",
                "--progress-bar",
                "off",
                "--no-deps",
                cset_install_path,
            ),
            check=True,
        )

result = subprocess.run(("cset", "--version"), check=True, capture_output=True)
print(f"Using CSET version: {result.stdout.decode(sys.stdout.encoding)}")
