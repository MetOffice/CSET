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

import argparse
import json
import logging
import os
import re
import shutil
import sys
import time
from collections.abc import Iterable
from importlib.metadata import version
from pathlib import Path

logging.basicConfig(
    level=os.getenv("LOGLEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def human_sorted(iterable: Iterable, reverse: bool = False) -> list:
    """Sort such numbers within strings are sorted correctly."""
    # Adapted from https://nedbatchelder.com/blog/200712/human_sorting.html

    def alphanum_key(s):
        """Turn a string into a list of string and number chunks.

        >>> alphanum_key("z23a")
        ["z", 23, "a"]
        """
        try:
            return [int(c) if c.isdecimal() else c for c in re.split(r"(\d+)", s)]
        except TypeError:
            return s

    return sorted(iterable, key=alphanum_key, reverse=reverse)


def sort_dict(d: dict) -> dict:
    """Recursively sort a dictionary."""
    # Thank you to https://stackoverflow.com/a/47882384
    return {
        k: sort_dict(v) if isinstance(v, dict) else v
        for k, v in human_sorted(d.items())
    }


def install_website_skeleton(
    www_root_link: Path | None, www_content: Path, skeleton_dir: Path
):
    """Copy static website files and create symlink from web document root."""
    logger.info("Installing website files to %s.", www_content)
    # Create directory for web content.
    www_content.mkdir(parents=True, exist_ok=True)
    # Copy static HTML/CSS/JS.
    shutil.copytree(skeleton_dir, www_content, dirs_exist_ok=True)
    # Setup symbolic link from web root.
    if www_root_link is not None:
        logger.info("Linking %s to web content.", www_root_link)
        # Remove existing link to output ahead of creating new symlink.
        www_root_link.unlink(missing_ok=True)
        # Ensure parent directories of WEB_DIR exist.
        www_root_link.parent.mkdir(parents=True, exist_ok=True)
        # Create symbolic link to web directory.
        # NOTE: While good for space, it means `cylc clean` removes output.
        www_root_link.symlink_to(www_content)


def construct_index(www_content: Path):
    """Construct the plot index."""
    with open(www_content / "index.jsonl", "wt", encoding="UTF-8") as index_fp:
        # Loop over all diagnostics and append to index. The glob is sorted to
        # ensure a consistent ordering.
        for metadata_file in sorted(www_content.glob("**/*/meta.json")):
            try:
                with open(metadata_file, "rt", encoding="UTF-8") as plot_fp:
                    plot_metadata = json.load(plot_fp)
                plot_metadata["path"] = str(
                    metadata_file.parent.relative_to(www_content)
                )
                # Remove keys that are not useful for the index.
                removed_index_keys = [
                    "description",
                    "plot_resolution",
                    "plots",
                    "skip_write",
                    "COORD_LIST",
                    "ONE_TO_ONE",
                    "PERCENTILES",
                    "SUBAREA_EXTENT",
                    "SUBAREA_TYPE",
                ]
                for key in removed_index_keys:
                    plot_metadata.pop(key, None)
                # Sort plot metadata for consistency.
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
    # Search and replace the string "CACHEBUSTER" with a time-based cache key.
    cache_key = str(int(time.time()))
    with open(www_content / "index.html", "r+t") as fp:
        content = fp.read()
        new_content = content.replace("CACHEBUSTER", cache_key)
        fp.seek(0)
        fp.truncate()
        fp.write(new_content)


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
    cylc_run_dir = os.getenv("CYLC_WORKFLOW_RUN_DIR", None)
    if cylc_run_dir:
        rose_suite_conf = Path(cylc_run_dir) / "rose-suite.conf"
        web_conf_file = www_content / "rose-suite.conf"
        try:
            shutil.copyfile(rose_suite_conf, web_conf_file)
        except FileNotFoundError:
            logger.warning("No rose-suite.conf file found for cylc workflow.")


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Create a navigation interface for a set of diagnostic webpages.",
    )
    parser.add_argument(
        "web_content",
        type=Path,
        help="Where to save the HTML content and find the diagnostic webpages.",
    )
    parser.add_argument(
        "--web-root-link",
        type=Path,
        help="Where to create a symlink to the content, optional.",
    )
    parser.add_argument(
        "--skeleton",
        type=Path,
        help="Directory containing static website files. Defaults to $PWD/html",
        default=Path.cwd() / "html",
    )
    return parser.parse_args(args)


def run():  # pragma: no cover
    """Do the final steps to finish the website."""
    args = parse_args()
    logger.debug("Arguments: %s", args)

    install_website_skeleton(args.web_root_link, args.web_content, args.skeleton)
    copy_rose_config(args.web_content)
    construct_index(args.web_content)
    bust_cache(args.web_content)
    update_workflow_status(args.web_content)


if __name__ == "__main__":  # pragma: no cover
    run()
