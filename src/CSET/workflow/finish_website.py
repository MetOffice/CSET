#! /usr/bin/env python3

"""Write finished status to website front page.

Constructs the plot index, and does the final update to the workflow status on
the front page of the web interface.
"""

import json
import logging
import os
import shutil
from pathlib import Path

from CSET._common import combine_dicts, sort_dict

logging.basicConfig(
    level=os.getenv("LOGLEVEL", "INFO"), format="%(asctime)s %(levelname)s %(message)s"
)


def construct_index():
    """Construct the plot index.

    Index should has the form ``{"Category Name": {"recipe_id": "Plot Name"}}``
    where ``recipe_id`` is the name of the plot's directory.
    """
    index = {}
    plots_dir = Path(os.environ["CYLC_WORKFLOW_SHARE_DIR"]) / "web/plots"
    # Loop over all diagnostics and append to index.
    for metadata_file in plots_dir.glob("**/*/meta.json"):
        try:
            with open(metadata_file, "rt", encoding="UTF-8") as fp:
                plot_metadata = json.load(fp)

            category = plot_metadata["category"]
            case_date = plot_metadata.get("case_date", "")
            relative_url = str(metadata_file.parent.relative_to(plots_dir))

            record = {
                category: {
                    case_date if case_date else "Aggregation": {
                        relative_url: plot_metadata["title"].strip()
                    }
                }
            }
        except (json.JSONDecodeError, KeyError, TypeError) as err:
            logging.error("%s is invalid, skipping.\n%s", metadata_file, err)
            continue
        index = combine_dicts(index, record)

    # Sort index of diagnostics.
    index = sort_dict(index)

    # Write out website index.
    with open(plots_dir / "index.json", "wt", encoding="UTF-8") as fp:
        json.dump(index, fp, indent=2)


def update_workflow_status():
    """Update the workflow status on the front page of the web interface."""
    web_dir = Path(os.environ["CYLC_WORKFLOW_SHARE_DIR"] + "/web")
    with open(web_dir / "status.html", "wt") as fp:
        fp.write("<p>Finished</p>\n")


def copy_rose_config():
    """Copy the rose-suite.conf file to add to output web directory."""
    rose_suite_conf = Path(os.environ["CYLC_WORKFLOW_RUN_DIR"]) / "rose-suite.conf"
    web_conf_file = (
        Path(os.environ["CYLC_WORKFLOW_SHARE_DIR"]) / "web/rose-suite.conf.txt"
    )
    shutil.copy(rose_suite_conf, web_conf_file)


def run():
    """Do the final steps to finish the website."""
    construct_index()
    update_workflow_status()
    copy_rose_config()
