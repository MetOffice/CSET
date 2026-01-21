#!/usr/bin/env python3
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

"""
Create the CSET diagnostic viewing website.

Copies the static files that make up the web interface, constructs the plot
index, and updates the workflow status on the front page of the
web interface.
"""

import json
import logging
import os
import shutil
import sys
import time
from importlib.metadata import version
from pathlib import Path

from CSET._common import sort_dict

logging.basicConfig(
    level=os.getenv("LOGLEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def install_website_skeleton(www_root_link: Path, www_content: Path):
    """Copy static website files and create symlink from web document root."""
    # Remove existing link to output ahead of creating new symlink.
    logger.info("Removing any existing output link at %s.", www_root_link)
    www_root_link.unlink(missing_ok=True)

    logger.info("Installing website files to %s.", www_content)
    # Create directory for web content.
    www_content.mkdir(parents=True, exist_ok=True)
    # Copy static HTML/CSS/JS.
    html_source = Path.cwd() / "html"
    shutil.copytree(html_source, www_content, dirs_exist_ok=True)
    # Create directory for plots.
    plot_dir = www_content / "plots"
    plot_dir.mkdir(exist_ok=True)

    logger.info("Linking %s to web content.", www_root_link)
    # Ensure parent directories of WEB_DIR exist.
    www_root_link.parent.mkdir(parents=True, exist_ok=True)
    # Create symbolic link to web directory.
    # NOTE: While good for space, it means `cylc clean` removes output.
    www_root_link.symlink_to(www_content)


def construct_index(www_content: Path):
    """Construct the plot index."""
    plots_dir = www_content / "plots"
    with open(plots_dir / "index.jsonl", "wt", encoding="UTF-8") as index_fp:
        # Loop over all diagnostics and append to index. The glob is sorted to
        # ensure a consistent ordering.
        for metadata_file in sorted(plots_dir.glob("**/*/meta.json")):
            try:
                with open(metadata_file, "rt", encoding="UTF-8") as plot_fp:
                    plot_metadata = json.load(plot_fp)
                plot_metadata["path"] = str(metadata_file.parent.relative_to(plots_dir))
                # Remove keys that are not useful for the index.
                removed_index_keys = ["description", "plots", "plot_resolution"]
                for key in removed_index_keys:
                    plot_metadata.pop(key, None)
                # Sort plot metadata.
                plot_metadata = sort_dict(plot_metadata)
                # Write metadata into website index.
                json.dump(plot_metadata, index_fp, separators=(",", ":"))
                index_fp.write("\n")
            except (json.JSONDecodeError, KeyError, TypeError) as err:
                logging.error("%s is invalid, skipping.\n%s", metadata_file, err)
                continue


def bust_cache(www_content: Path):
    """Add a unique query string to static requests to avoid stale caches.

    We only need to do this for static resources referenced from the index page,
    as each plot already uses a unique filename based on the recipe.
    """
    # Search and replace the string "CACHEBUSTER".
    CACHEBUSTER = str(int(time.time()))
    with open(www_content / "index.html", "r+t") as fp:
        content = fp.read()
        new_content = content.replace("CACHEBUSTER", CACHEBUSTER)
        fp.seek(0)
        fp.truncate()
        fp.write(new_content)

    # Move plots directory so it has a unique name.
    os.rename(www_content / "plots", www_content / f"plots-{CACHEBUSTER}")


def update_workflow_status(www_content: Path):
    """Update the workflow status on the front page of the web interface."""
    with open(www_content / "placeholder.html", "r+t") as fp:
        content = fp.read()
        finish_time = time.strftime("%Y-%m-%d %H:%M", time.localtime())
        status = f"Completed at {finish_time} using CSET v{version('CSET')}"
        new_content = content.replace(
            '<p id="workflow-status">Unknown</p>',
            f'<p id="workflow-status">{status}</p>',
        )
        fp.seek(0)
        fp.truncate()
        fp.write(new_content)


def copy_rose_config(www_content: Path):
    """Copy the rose-suite.conf file to add to output web directory."""
    rose_suite_conf = Path(os.environ["CYLC_WORKFLOW_RUN_DIR"]) / "rose-suite.conf"
    web_conf_file = www_content / "rose-suite.conf"
    shutil.copyfile(rose_suite_conf, web_conf_file)


def run():
    """Do the final steps to finish the website."""
    # Strip trailing slashes in case they have been added in the config.
    # Otherwise they break the symlinks.
    www_root_link = Path(os.environ["WEB_DIR"].rstrip("/"))
    www_content = Path(os.environ["CYLC_WORKFLOW_SHARE_DIR"] + "/web")

    install_website_skeleton(www_root_link, www_content)
    copy_rose_config(www_content)
    construct_index(www_content)
    bust_cache(www_content)
    update_workflow_status(www_content)


if __name__ == "__main__":  # pragma: no cover
    run()
