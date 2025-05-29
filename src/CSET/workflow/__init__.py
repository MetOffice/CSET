# © Crown copyright, Met Office (2022-2025) and CSET contributors.
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

"""Subpackage containing code used in the CSET workflow.

This package is totally unstable, and its contents are subject to change without
notice.
"""

import importlib.metadata
import importlib.resources
import logging
import os
import shutil
import stat
from pathlib import Path

import CSET.workflow.files

logger = logging.getLogger(__name__)


def make_script_executable(p: Path):
    """Make scripts (starting with a shebang) executable."""
    if p.is_file():
        with open(p, "rb") as fd:
            shebang = fd.read(2)
        # Assume the first two bytes of a script are #!
        if shebang == b"#!":
            logger.debug("Changing file mode to executable: %s", p)
            mode = p.stat().st_mode
            # Make executable by all who can read.
            if mode & stat.S_IRUSR:
                mode |= stat.S_IXUSR
            if mode & stat.S_IRGRP:
                mode |= stat.S_IXGRP
            if mode & stat.S_IROTH:
                mode |= stat.S_IXOTH
            p.chmod(mode)


def install_workflow(location: Path):
    """Install the workflow's files and link the conda environment.

    Arguments
    ---------
    location: Path
        A directory where the workflow files are to be installed to. A
        sub-directory named "cset-workflow-vX.Y.Z" will be created under here.
    """
    # Check location's parents exist.
    if not location.is_dir():
        raise OSError(f"{location} should exist and be a directory.")
    workflow_dir = location / f"cset-workflow-v{importlib.metadata.version('CSET')}"

    # Write workflow content into workflow_dir.
    workflow_files = importlib.resources.files(CSET.workflow.files)
    with importlib.resources.as_file(workflow_files) as w:
        logger.info("Copying workflow files into place.")
        try:
            shutil.copytree(w, workflow_dir)
        except FileExistsError as err:
            raise FileExistsError(f"Refusing to overwrite {workflow_dir}") from err

    # Make scripts executable.
    logger.info("Changing mode of scripts to be executable.")
    for dirpath, _, filenames in workflow_dir.walk():
        for filename in filenames:
            make_script_executable(dirpath / filename)

    # Create link to conda environment.
    conda_prefix = os.getenv("CONDA_PREFIX")
    if conda_prefix is not None:
        logger.info("Linking workflow conda environment to %s", conda_prefix)
        (workflow_dir / "conda-environment").symlink_to(Path(conda_prefix).resolve())
    else:
        logger.warning("CONDA_PREFIX not defined. Skipping linking environment.")

    print(f"Workflow written to {workflow_dir}")
