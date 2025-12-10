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
Write finished status to website front page.

Constructs the plot index, and does the final update to the workflow status on
the front page of the web interface.
"""

import datetime
import json
import logging
import os
import shutil
from importlib.metadata import version
from pathlib import Path

from CSET._common import sort_dict

logging.basicConfig(
    level=os.getenv("LOGLEVEL", "INFO"), format="%(asctime)s %(levelname)s %(message)s"
)


def construct_index():
    """Construct the plot index.

    Index should has the form ``{"Category Name": {"recipe_id": "Plot Name"}}``
    where ``recipe_id`` is the name of the plot's directory.
    """
    plots_dir = Path(os.environ["CYLC_WORKFLOW_SHARE_DIR"]) / "web/plots"
    with open(plots_dir / "index.jsonl", "wt", encoding="UTF-8") as index_fp:
        # Loop over all diagnostics and append to index. The glob is sorted to
        # ensure a consistent ordering.
        for metadata_file in sorted(plots_dir.glob("**/*/meta.json")):
            try:
                with open(metadata_file, "rt", encoding="UTF-8") as plot_fp:
                    plot_metadata = json.load(plot_fp)
                plot_metadata["path"] = str(metadata_file.parent.relative_to(plots_dir))
                # Sort plot metadata.
                plot_metadata = sort_dict(plot_metadata)
                # Write metadata into website index.
                json.dump(plot_metadata, index_fp, separators=(",", ":"))
                index_fp.write("\n")
            except (json.JSONDecodeError, KeyError, TypeError) as err:
                logging.error("%s is invalid, skipping.\n%s", metadata_file, err)
                continue


def update_workflow_status():
    """Update the workflow status on the front page of the web interface."""
    web_dir = Path(os.environ["CYLC_WORKFLOW_SHARE_DIR"] + "/web")
    with open(web_dir / "status.html", "wt") as fp:
        finish_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        fp.write(f"<p>Completed at {finish_time} using CSET v{version('CSET')}</p>\n")


def copy_rose_config():
    """Copy the rose-suite.conf file to add to output web directory."""
    rose_suite_conf = Path(os.environ["CYLC_WORKFLOW_RUN_DIR"]) / "rose-suite.conf"
    web_conf_file = Path(os.environ["CYLC_WORKFLOW_SHARE_DIR"]) / "web/rose-suite.conf"
    shutil.copy(rose_suite_conf, web_conf_file)


def run():
    """Do the final steps to finish the website."""
    construct_index()
    update_workflow_status()
    copy_rose_config()


if __name__ == "__main__":  # pragma: no cover
    run()
