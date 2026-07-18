# © Crown copyright, Met Office (2022-2026) and CSET contributors.
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

"""Extract the CSET cylc workflow for use."""

import importlib.metadata
import importlib.resources
import logging
import os
import re
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path

import CSET.cset_workflow

logger = logging.getLogger(__name__)


def make_script_executable(p: Path):
    """Make a script file (starting with a shebang) executable."""
    if p.is_file():
        try:
            with open(p, "rb") as fd:
                shebang = fd.read(14)
        except PermissionError:
            # Skip files that can't be read.
            logger.debug("Unreadable file: %s", p)
            return
        # Assume the first 14 bytes of a script are #!/usr/bin/env
        if shebang == b"#!/usr/bin/env":
            logger.debug("Changing file mode to executable: %s", p)
            mode = p.stat().st_mode
            # User must be able to read if we read the file.
            mode |= stat.S_IXUSR
            # Make executable by group and/or others if they can read.
            if mode & stat.S_IRGRP:
                mode |= stat.S_IXGRP
            if mode & stat.S_IROTH:
                mode |= stat.S_IXOTH
            p.chmod(mode)


def install_workflow(location: Path) -> Path:
    """Install the workflow's files and link the conda environment.

    Parameters
    ----------
    location: Path
        A directory where the workflow files are to be installed to. A
        sub-directory named "cset-workflow-vX.Y.Z" will be created under here.

    Returns
    -------
    workflow_dir: Path
        Path to newly created workflow directory.
    """
    # Check location's parents exist.
    if not location.is_dir():
        raise OSError(f"{location} should exist and be a directory.")
    workflow_dir = location / f"cset-workflow-v{importlib.metadata.version('CSET')}"

    # Write workflow content into workflow_dir.
    workflow_files = importlib.resources.files(CSET.cset_workflow)
    with importlib.resources.as_file(workflow_files) as w:
        logger.info("Copying workflow files into place.")
        try:
            shutil.copytree(w, workflow_dir)
        except FileExistsError as err:
            raise FileExistsError(f"Refusing to overwrite {workflow_dir}") from err

    # Make scripts executable.
    logger.info("Changing mode of scripts to be executable.")
    for dirpath, _, filenames in os.walk(workflow_dir):
        for filename in filenames:
            make_script_executable(Path(dirpath) / filename)

    # Create link to conda environment.
    conda_prefix = os.getenv("CONDA_PREFIX")
    if conda_prefix is not None:
        logger.info("Linking workflow conda environment to %s", conda_prefix)
        (workflow_dir / "conda-environment").symlink_to(Path(conda_prefix).resolve())
    else:
        logger.warning("CONDA_PREFIX not defined. Skipping linking environment.")

    print(f"Workflow written to {workflow_dir}")
    return workflow_dir


def list_refs(url: str) -> list[str]:
    """List release refs for the repository.

    This serves both as an access check and to find an appropriate ref.
    """
    # Disable interactively asking for authentication.
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "false"

    # List release references.
    cmd = ("git", "ls-remote", "--quiet", "--refs", url, "releases/**", "v*")
    logger.debug("Running %s", " ".join(cmd))
    try:
        p = subprocess.run(cmd, env=env, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as err:
        raise ValueError(f"Cannot access Git repository at {url}") from err

    # Reduce to just ref names.
    release_refs = [
        line.split(maxsplit=1)[-1]
        .removeprefix("refs/heads/")
        .removeprefix("refs/tags/")
        for line in p.stdout.splitlines()
    ]
    return release_refs


def clone_ref(ref: str, url: str, location: str):
    """Clone the specified ref."""
    # Disable interactively asking for authentication.
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "false"

    cmd = ("git", "clone", "--quiet", "--depth", "1", "--branch", ref, url, location)
    logger.debug("Running %s", " ".join(cmd))
    try:
        subprocess.run(cmd, env=env, check=True, capture_output=True)
    except subprocess.CalledProcessError as err:
        raise ValueError(
            f"Cannot access ref {ref} from Git repository at {url}"
        ) from err


def install_restricted_files(workflow_dir: Path, alternative_url: str | None = None):
    """Install restricted site-specific restricted files into CSET workflow.

    Parameters
    ----------
    workflow_dir: Path
        The workflow directory into which the restricted files will be copied.
    alternative_url: str, optional
        Alternative Git URL to fetch the restricted files from. If omitted,
        defaults to trying to clone first from 'localmirrors:', then from GitHub
        via SSH and HTTPS.

    Notes
    -----
    Requires Git to be installed to function.
    """
    # Basic check workflow_dir is correct.
    if not (workflow_dir / "flow.cylc").is_file():
        raise ValueError(f"{workflow_dir} should be a CSET workflow directory.")

    # Determine target tag/branch from version.
    version_tag = f"v{importlib.metadata.version('CSET')}"
    logger.debug("Running for CSET %s", version_tag)
    m = re.match(r"v\d+\.\d+", version_tag)
    base_version = m.group(0) if m else version_tag
    if m is None:
        logger.warning("Cannot determine major version from %s", version_tag)
    release_branch = f"releases/{base_version}"

    # Default URLs to try in order, or use alternative if provided.
    urls = (
        (
            "localmirrors:MetOffice/CSET-restricted-files.git",
            "git@github.com:MetOffice/CSET-restricted-files.git",
            "https://github.com/MetOffice/CSET-restricted-files.git",
        )
        if alternative_url is None
        else (alternative_url,)
    )

    # Find first working URL and list its refs.
    for url in urls:
        try:
            refs = list_refs(url)
            break
        except ValueError:
            continue
    else:
        raise ValueError(
            "Could not read from restricted repository. Have you got access?"
        )

    # Use most specific ref, falling back to main.
    logger.debug("Release refs: %s", refs)
    if version_tag in refs:
        ref = version_tag
    elif release_branch in refs:
        ref = release_branch
    else:
        ref = "main"
    logger.info("Fetching restricted files from ref %s of %s", ref, url)

    # Checkout git repository to temporary location.
    with tempfile.TemporaryDirectory() as tempdir:
        # Clone restrict file repository.
        logger.debug("Cloning to %s", tempdir)
        clone_ref(ref, url, tempdir)

        # Delete unwanted top-level README.
        (Path(tempdir) / "README.md").unlink(missing_ok=True)

        # Copy remaining files, skipping hidden files.
        shutil.copytree(
            tempdir,
            workflow_dir,
            ignore=shutil.ignore_patterns(".*"),
            symlinks=True,
            dirs_exist_ok=True,
        )
        print(f"Installed site-specific restricted files into {workflow_dir}.")
